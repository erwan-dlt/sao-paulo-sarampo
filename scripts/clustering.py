"""Perfis municipais exploratórios, estabilidade e análises de sensibilidade."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans,AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score,adjusted_rand_score
from sklearn.decomposition import PCA
from scipy.optimize import linear_sum_assignment
from threadpoolctl import threadpool_limits
from modelagem import carregar_base
ROOT=Path(__file__).resolve().parents[1]
FEATURES=['d1_media','d2_media','d1_delta','d2_delta','log_incidencia','log_densidade','frac_0a4']
WEIGHTS=np.array([.5,.5,.5,.5,1,1/np.sqrt(2),1/np.sqrt(2)])

def assinatura():
    paths=list((ROOT/'data/processed').glob('*'))+[Path(__file__),ROOT/'scripts/modelagem.py']
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths) if p.is_file()}

def base(cenario='limitada'):
    d=carregar_base(cap=cenario=='limitada');d['incidencia']=d.casos/d.populacao*1e5;d['log_incidencia']=np.log1p(d.incidencia)
    if cenario=='ausente':
        v=pd.read_csv(ROOT/'data/processed/mmr.csv',dtype={'municipality_ibge':str});v['codigo']=v.municipality_ibge.str[:6]
        v.loc[v.coverage_percent>100,'coverage_percent']=np.nan
        p=v.pivot(index='codigo',columns=['year','dose'],values='coverage_percent')
        for dose,label in [('MMR1','d1'),('MMR2','d2')]:
            d[label+'_media']=p.loc[:,[(y,dose) for y in [2016,2017,2018]]].mean(axis=1)
            d[label+'_delta']=p[(2018,dose)]-p[(2016,dose)]
    return d

def transformar(d,cols=FEATURES):
    # Imputação ajustada no subconjunto, inclusive em cada reamostragem.
    X=d[cols].copy();med=X.median();X=X.fillna(med);sc=StandardScaler();w=WEIGHTS[[FEATURES.index(c) for c in cols]]
    Z=sc.fit_transform(X)*w
    return Z,med,sc,w

def ajustar(d,k,cols=FEATURES,seed=42):
    Z,med,sc,w=transformar(d,cols);km=KMeans(k,n_init=30,random_state=seed).fit(Z)
    return km.labels_,Z,km,med,sc,w

def run(out=ROOT/'results/clustering'):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);d=base();raw=base('original')
    d['d2_media_original']=raw.d2_media
    limvac=raw.d2_media.median();liminc=d.casos.sum()/d.populacao.sum()*1e5
    d['quadrante']=np.select([(raw.d2_media>=limvac)&(d.incidencia>=liminc),(raw.d2_media>=limvac)&(d.incidencia<liminc),(raw.d2_media<limvac)&(d.incidencia>=liminc)],['Cobertura maior / incidência maior','Cobertura maior / incidência menor','Cobertura menor / incidência maior'],default='Cobertura menor / incidência menor')
    scores=[];fits={}
    with threadpool_limits(limits=1):
        for k in range(2,7):
            lab,Z,*_=ajustar(d,k);fits[k]=lab
            scores.append({'k':k,'silhueta':silhouette_score(Z,lab),'menor_grupo':np.bincount(lab).min(),'maior_grupo':np.bincount(lab).max()})
        score=pd.DataFrame(scores);valid=score[score.menor_grupo>=20];k=int(valid.sort_values(['silhueta','k'],ascending=[False,True]).iloc[0].k)
        lab,Z,km,med,sc,w=ajustar(d,k)
        # IDs ordenados pela mediana da incidência, apenas para apresentação.
        order=sorted(range(k),key=lambda i:d.incidencia[lab==i].median());mapping={old:new for new,old in enumerate(order,1)}
        ref=np.array([mapping[x] for x in lab]);d['grupo']=ref
        st=[];jacc=[];agreement=np.zeros(len(d))
        for rep in range(40):
            rng=np.random.default_rng(100+rep);idx=rng.choice(len(d),int(.8*len(d)),replace=False)
            _,_,obj,mi,ss,ww=ajustar(d.iloc[idx],k,seed=100+rep)
            pred=obj.predict(ss.transform(d[FEATURES].fillna(mi))*ww)
            tab=pd.crosstab(ref,pred).reindex(index=range(1,k+1),columns=range(k),fill_value=0).to_numpy()
            a,b=linear_sum_assignment(-tab);mp={bb:aa+1 for aa,bb in zip(a,b)};aligned=np.array([mp[x] for x in pred]);agreement+=(aligned==ref)
            candidatos=[]
            for kk in range(2,7):
                ll,zz,*_=ajustar(d.iloc[idx],kk,seed=100+rep)
                if np.bincount(ll).min()>=20:candidatos.append((silhouette_score(zz,ll),kk))
            st.append({'repeticao':rep,'ARI':adjusted_rand_score(ref,pred),'k_reselecionado':max(candidatos,key=lambda x:x[0])[1]})
            for g in range(1,k+1):
                inter=((ref==g)&(aligned==g)).sum();union=((ref==g)|(aligned==g)).sum()
                jacc.append({'repeticao':rep,'grupo':g,'Jaccard':inter/union})
        d['concordancia_reamostragem']=agreement/40
        sens=[];senslabels=[]
        for name,dd,cols,method in [('Coberturas originais',raw,FEATURES,'kmeans'),('>100 como ausente',base('ausente'),FEATURES,'kmeans'),('Sem valores >100',raw[raw.fracao_cob_acima100==0],FEATURES,'kmeans'),('Sem incidência',d,[c for c in FEATURES if c!='log_incidencia'],'kmeans'),('Ward',d,FEATURES,'ward')]:
            ll,zz,*_=ajustar(dd,k,cols)
            if method=='ward':ll=AgglomerativeClustering(n_clusters=k,linkage='ward').fit_predict(zz)
            rr=d.loc[dd.index,'grupo'];sens.append({'cenario':name,'n':len(dd),'ARI_vs_principal':adjusted_rand_score(rr,ll),'silhueta_no_espaco_proprio':silhouette_score(zz,ll)})
            senslabels.extend({'cenario':name,'codigo':cod,'grupo_alternativo':int(l)} for cod,l in zip(dd.index,ll))
        for name,col in [('Só incidência','log_incidencia'),('Só densidade','log_densidade'),('Só D2','d2_media')]:
            ll=KMeans(k,n_init=30,random_state=42).fit_predict(d[[col]])
            sens.append({'cenario':name,'n':len(d),'ARI_vs_principal':adjusted_rand_score(ref,ll),'silhueta_no_espaco_proprio':np.nan})
        # Controle de estrutura: embaralha colunas separadamente, preservando marginais.
        null=[]
        for rep in range(20):
            rng=np.random.default_rng(800+rep);zz=np.column_stack([rng.permutation(Z[:,j]) for j in range(Z.shape[1])]);vals=[]
            for kk in range(2,7):
                ll=KMeans(kk,n_init=30,random_state=rep).fit_predict(zz)
                if np.bincount(ll).min()>=20:vals.append(silhouette_score(zz,ll))
            null.append({'repeticao':rep,'melhor_silhueta':max(vals) if vals else np.nan})
        pca=PCA(2).fit(Z);proj=pca.transform(Z);d['PC1']=proj[:,0];d['PC2']=proj[:,1]
    desc=d.groupby('grupo').agg(n=('casos','size'),casos=('casos','sum'),populacao=('populacao','sum'),incidencia_mediana=('incidencia','median'),d1_mediana=('d1_media','median'),d2_mediana=('d2_media','median'),d1_delta_mediana=('d1_delta','median'),d2_delta_mediana=('d2_delta','median'),log_densidade_mediana=('log_densidade','median'),criancas_mediana=('frac_0a4','median'),anomalia_mediana=('fracao_cob_acima100','median'),estabilidade_mediana=('concordancia_reamostragem','median'),pib_log_mediano=('log_pib','median'))
    desc['incidencia_agregada']=desc.casos/desc.populacao*1e5
    desc['densidade_mediana']=np.exp(desc.log_densidade_mediana);desc['pib_pc_mediano']=np.exp(desc.pib_log_mediano)
    d['grupo_k2']=fits[2]
    # Variáveis abaixo descrevem os grupos; não participam do agrupamento.
    notif=pd.read_csv(ROOT/'data/processed/notificacoes.csv',dtype=str,keep_default_na=False)
    dt=pd.to_datetime(notif.DT_INICIO_,errors='coerce')
    cc=notif[notif.SG_UF.eq('35') & notif.CLASSI_FIN.eq('1') & dt.dt.year.eq(2019)].copy()
    cc['grupo']=cc.ID_MN_RESI.map(d.grupo);cod=pd.to_numeric(cc.NU_IDADE_N,errors='coerce')
    cc['adulto20a29']=cod.between(4020,4029);cc['julho_setembro']=pd.to_datetime(cc.DT_INICIO_).dt.month.between(7,9)
    ext=cc.groupby('grupo').agg(casos=('grupo','size'),adultos20a29=('adulto20a29','sum'),julho_setembro=('julho_setembro','sum'),hospitalizados=('ID_HOSPIT',lambda x:x.eq('1').sum()),hospitalizacao_conhecida=('ID_HOSPIT',lambda x:x.isin(['1','2']).sum()))
    ext['adultos20a29_%']=ext.adultos20a29/ext.casos*100;ext['julho_setembro_%']=ext.julho_setembro/ext.casos*100
    ext['hospitalizados_%_conhecidos']=ext.hospitalizados/ext.hospitalizacao_conhecida*100
    ext.to_csv(out/'perfil_casos.csv')
    d.to_csv(out/'municipios.csv');desc.to_csv(out/'perfis.csv');score.to_csv(out/'selecao_k.csv',index=False)
    pd.DataFrame(st).to_csv(out/'estabilidade.csv',index=False);pd.DataFrame(jacc).to_csv(out/'jaccard.csv',index=False)
    pd.DataFrame(sens).to_csv(out/'sensibilidades.csv',index=False);pd.DataFrame(senslabels).to_csv(out/'grupos_alternativos.csv',index=False);pd.DataFrame(null).to_csv(out/'controle_permutado.csv',index=False)
    pd.crosstab(d.grupo,d.quadrante).to_csv(out/'grupos_quadrantes.csv')
    pd.DataFrame(Z,index=d.index,columns=FEATURES).groupby(ref).mean().to_csv(out/'centros_padronizados.csv',index_label='grupo')
    info={'assinatura':assinatura(),'k':k,'silhueta':float(score.set_index('k').loc[k,'silhueta']),'limiar_D2':float(limvac),'limiar_incidencia':float(liminc),'PCA_variancia':pca.explained_variance_ratio_.tolist(),'atributos':FEATURES,'pesos':WEIGHTS.tolist(),'arquivos':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob('*.csv'))}}
    (out/'execucao.json').write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({x:info[x] for x in ['k','silhueta','limiar_D2','limiar_incidencia','PCA_variancia']},indent=2));print(desc.to_string());print(pd.DataFrame(sens).to_string(index=False));print(pd.DataFrame(st).describe())
if __name__=='__main__':run()
