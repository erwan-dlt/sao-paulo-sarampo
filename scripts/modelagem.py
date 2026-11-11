"""Validação municipal aninhada. Nenhum resultado do teste orienta o ajuste."""
from pathlib import Path
import json
import hashlib
import platform
from importlib.metadata import version
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.model_selection import KFold, LeaveOneGroupOut
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import PoissonRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_poisson_deviance, mean_absolute_error, r2_score
from threadpoolctl import threadpool_limits
import statsmodels.api as sm

ROOT=Path(__file__).resolve().parents[1]
DEM=['log_densidade','frac_0a4','frac_5a19','frac_20a39','frac_60mais']
SOC=DEM+['log_pib']
VAC=['d1_media','d2_media','d1_delta','d2_delta','fracao_cob_acima100']
MODELOS={
 'Referência populacional':('base',[],[0]),
 'Poisson demografia':('pois',DEM,[.1,1.,10.]),
 'Poisson + PIB':('pois',SOC,[.1,1.,10.]),
 'Poisson + PIB + vacina':('pois',SOC+VAC,[.1,1.,10.]),
 'Binomial negativa completa':('nb',SOC+VAC,[.1,1.,10.]),
 'Boosting sem vacina':('boost',SOC,[3,7]),
 'Boosting com vacina':('boost',SOC+VAC,[3,7])}

def carregar_base(pasta=ROOT/'data/processed',cap=False):
    p=Path(pasta)
    m=pd.read_csv(p/'municipios.csv',dtype={'codigo':str}).set_index('codigo')
    n=pd.read_csv(p/'notificacoes.csv',dtype=str,keep_default_na=False)
    mask=n.SG_UF.eq('35')&n.CLASSI_FIN.eq('1')&pd.to_datetime(n.DT_INICIO_,errors='coerce').dt.year.eq(2019)
    m['casos']=n.loc[mask,'ID_MN_RESI'].value_counts().reindex(m.index,fill_value=0)
    idade=pd.read_csv(p/'pop_idade.csv',dtype={'codigo':str}).set_index('codigo')
    for nome,cols in [('frac_0a4',['<1 Ano','1-4']),('frac_5a19',['5-9','10-14','15-19']),('frac_20a39',['20-29','30-39']),('frac_60mais',['60-64','65-69','70-79','80 e +'])]:
        m[nome]=idade[cols].sum(axis=1)/m.populacao
    m['log_densidade']=np.log(m.populacao/m.area_km2)
    pib=pd.read_csv(p/'pib.csv',dtype={'municipality_ibge':str});pib['codigo']=pib.municipality_ibge.str[:6]
    m['log_pib']=np.log(pib.set_index('codigo').gdp_per_capita_brl_2016)
    v=pd.read_csv(p/'mmr.csv',dtype={'municipality_ibge':str});v['codigo']=v.municipality_ibge.str[:6]
    m['fracao_cob_acima100']=v.assign(flag=v.coverage_percent.gt(100)).groupby('codigo').flag.mean()
    if cap:v['coverage_percent']=v.coverage_percent.clip(upper=100)
    piv=v.pivot(index='codigo',columns=['year','dose'],values='coverage_percent')
    for dose,label in [('MMR1','d1'),('MMR2','d2')]:
        m[label+'_media']=piv.loc[:,[(y,dose) for y in [2016,2017,2018]]].mean(axis=1)
        m[label+'_delta']=piv[(2018,dose)]-piv[(2016,dose)]
    geom=json.loads((p/'malha.json').read_text(encoding='utf-8'))
    # Centro da caixa envolvente: aproximação apenas para partição espacial.
    for cod,parts in geom.items():
        pts=np.concatenate(parts)
        m.loc[cod,'lon']=(pts[:,0].min()+pts[:,0].max())/2
        m.loc[cod,'lat']=(pts[:,1].min()+pts[:,1].max())/2
    xy=np.column_stack([m.lon*np.cos(np.deg2rad(m.lat.mean())),m.lat])
    with threadpool_limits(limits=1):labels=KMeans(n_clusters=5,n_init=20,random_state=42).fit_predict(xy)
    order=np.argsort([m.lon[labels==i].mean() for i in range(5)])
    m['bloco']=[dict(zip(order,range(1,6)))[i] for i in labels]
    m['faixa_longitude']=pd.qcut(m.lon.rank(method='first'),5,labels=False).astype(int)+1
    assert len(m)==645 and m.casos.sum()==18025 and m.index.is_unique
    assert np.isfinite(m[DEM+['log_pib']+VAC].to_numpy()).all()
    return m

class Ajuste:
    def __init__(self,tipo,cols,hiper):self.tipo=tipo;self.cols=cols;self.hiper=hiper
    def fit(self,df):
        y=df.casos.to_numpy(float);e=df.populacao.to_numpy(float)/1e5
        self.taxa=y.sum()/e.sum()
        if self.tipo=='base':return self
        self.imp=SimpleImputer(strategy='median');self.scale=StandardScaler()
        X=self.scale.fit_transform(self.imp.fit_transform(df[self.cols]))
        if self.tipo=='pois':
            self.model=PoissonRegressor(alpha=self.hiper,max_iter=2000,tol=1e-7)
            self.model.fit(X,y/e,sample_weight=e)
        elif self.tipo=='boost':
            self.model=HistGradientBoostingRegressor(loss='poisson',max_iter=100,learning_rate=.05,
                max_leaf_nodes=int(self.hiper),min_samples_leaf=20,l2_regularization=10,
                early_stopping=False,random_state=42)
            self.model.fit(X,y/e,sample_weight=e)
        else:
            Z=sm.add_constant(X,has_constant='add')
            glm=sm.GLM(y,Z,offset=np.log(e),family=sm.families.NegativeBinomial(alpha=self.hiper))
            # Penalização L2 fixa, intercepto sem penalidade; dispersão selecionada internamente.
            self.model=glm.fit_regularized(alpha=np.r_[0,np.repeat(.1,X.shape[1])],L1_wt=0,maxiter=1000)
        return self
    def predict(self,df):
        e=df.populacao.to_numpy(float)/1e5
        if self.tipo=='base':return np.full(len(df),self.taxa)*e
        X=self.scale.transform(self.imp.transform(df[self.cols]))
        if self.tipo=='nb':pred=self.model.predict(sm.add_constant(X,has_constant='add'),offset=np.log(e))
        else:pred=self.model.predict(X)*e
        assert np.isfinite(pred).all()
        return np.maximum(pred,1e-9)

def metricas(y,p,e):
    return {'desvio_Poisson':mean_poisson_deviance(y,p),'MAE_casos':mean_absolute_error(y,p),
        'MAE_incidencia':mean_absolute_error(y/e,p/e),'R2_incidencia':r2_score(y/e,p/e),
        'razao_pred_obs':np.sum(p)/np.sum(y)}

def executar(df,esquema='espacial',modelos=None,permutar=False):
    modelos=MODELOS if modelos is None else {k:MODELOS[k] for k in modelos}
    if esquema=='aleatorio':outer=list(KFold(5,shuffle=True,random_state=42).split(df))
    else:
        groups=df.bloco if esquema=='espacial' else df.faixa_longitude
        outer=list(LeaveOneGroupOut().split(df,groups=groups))
    preds=[];scores=[];tuning=[];importance=[];diagnostico=[]
    for fold,(tr,te) in enumerate(outer,1):
        treino=df.iloc[tr];teste=df.iloc[te]
        assert set(treino.index).isdisjoint(teste.index)
        if esquema=='aleatorio':inner=list(KFold(3,shuffle=True,random_state=43).split(treino))
        else:
            g=treino.bloco if esquema=='espacial' else treino.faixa_longitude
            inner=list(LeaveOneGroupOut().split(treino,groups=g))
        for nome,(tipo,cols,grid) in modelos.items():
            candidatos=[]
            for h in grid:
                if tipo=='base':loss=0.
                else:
                    losses=[];sizes=[]
                    for itr,iva in inner:
                        mod=Ajuste(tipo,cols,h).fit(treino.iloc[itr])
                        pred=mod.predict(treino.iloc[iva]);losses.append(mean_poisson_deviance(treino.iloc[iva].casos,pred));sizes.append(len(iva))
                    loss=np.average(losses,weights=sizes)
                candidatos.append((loss,h));tuning.append({'esquema':esquema,'fold':fold,'modelo':nome,'hiper':h,'desvio_interno':loss})
            _,melhor=min(candidatos,key=lambda x:x[0])
            mod=Ajuste(tipo,cols,melhor).fit(treino);p=mod.predict(teste)
            y=teste.casos.to_numpy();ex=teste.populacao.to_numpy()/1e5
            scores.append({'esquema':esquema,'fold':fold,'modelo':nome,'n_treino':len(tr),'n_teste':len(te),'hiper':melhor,**metricas(y,p,ex)})
            for cod,pred in zip(teste.index,p):preds.append({'codigo':cod,'esquema':esquema,'fold':fold,'modelo':nome,'pred_casos':pred})
            if tipo=='pois' and nome=='Poisson + PIB + vacina':
                mt=mod.predict(treino);pearson=np.sum((treino.casos-mt)**2/mt)/max(len(treino)-len(cols)-1,1)
                diagnostico.append({'esquema':esquema,'fold':fold,'Pearson_por_gl':pearson})
            if permutar and nome in ['Poisson + PIB + vacina','Boosting com vacina']:
                base_loss=mean_poisson_deviance(y,p)
                for grupo,cc in [('Vacinação',VAC),('Densidade',['log_densidade']),('Idade',DEM[1:]),('PIB',['log_pib'])]:
                    for rep in range(10):
                        rng=np.random.default_rng(1000+100*fold+rep)
                        t=teste.copy();t.loc[:,cc]=teste[cc].to_numpy()[rng.permutation(len(t))]
                        importance.append({'esquema':esquema,'fold':fold,'modelo':nome,'grupo':grupo,'repeticao':rep,'aumento_desvio':mean_poisson_deviance(y,mod.predict(t))-base_loss})
        print(f'{esquema}: bloco {fold}/5 concluído',flush=True)
    return {'predicoes':pd.DataFrame(preds),'folds':pd.DataFrame(scores),'ajustes':pd.DataFrame(tuning),
        'permutacao':pd.DataFrame(importance),'dispersao':pd.DataFrame(diagnostico)}

def resumir(df,preds):
    out=[]
    for (esq,nome),s in preds.groupby(['esquema','modelo']):
        s=s.set_index('codigo').reindex(df.index)
        assert s.pred_casos.notna().all()
        out.append({'esquema':esq,'modelo':nome,**metricas(df.casos,s.pred_casos,df.populacao/1e5)})
    return pd.DataFrame(out)

def assinatura_entradas():
    paths=sorted((ROOT/'data/processed').glob('*'))+[Path(__file__)]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}

def rodar_tudo(destino=ROOT/'results/ml'):
    destino=Path(destino);destino.mkdir(parents=True,exist_ok=True)
    df=carregar_base();df.to_csv(destino/'base_municipal_ml.csv')
    results=[]
    with threadpool_limits(limits=1):
        results.append(executar(df,'espacial',permutar=True))
        results.append(executar(df,'longitude'))
        results.append(executar(df,'aleatorio'))
        cap=executar(carregar_base(cap=True),'espacial',modelos=['Poisson + PIB + vacina','Boosting com vacina'])
        for v in cap.values():
            if 'esquema' in v:v['esquema']='espacial_cob_limitada'
        results.append(cap)
    for key in ['predicoes','folds','ajustes','permutacao','dispersao']:
        frames=[r[key] for r in results if not r[key].empty]
        pd.concat(frames,ignore_index=True).to_csv(destino/(key+'.csv'),index=False)
    pred=pd.concat([r['predicoes'] for r in results],ignore_index=True)
    resumo=resumir(df,pred);resumo.to_csv(destino/'metricas.csv',index=False)
    semcapital=resumir(df.drop('355030'),pred[pred.codigo!='355030'])
    semcapital.to_csv(destino/'metricas_sem_capital.csv',index=False)
    meta={'assinatura_entradas':assinatura_entradas(),
          'python':platform.python_version(),
          'versoes':{p:version(p) for p in ['scikit-learn','statsmodels','pandas','numpy','scipy']},
          'semente':42,'modelos':MODELOS,
          'protocolo':'Validação externa de cinco blocos; ajuste interno por blocos restantes. Critério: desvio Poisson médio por município.'}
    meta['arquivos_resultados']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destino.glob('*.csv'))}
    (destino/'execucao.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return df,resumo

if __name__=='__main__':
    df,res=rodar_tudo();print(res.to_string(index=False))
