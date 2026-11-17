"""Validação municipal aninhada. Nenhum resultado do teste orienta o ajuste.

Partição principal: deixar uma RRAS de fora por vez (19 regiões oficiais de saúde); ajuste interno em 5 grupos de
RRAS do treino. Sensibilidades: 5 blocos k-means das coordenadas (partição original deste script), 5 faixas de
longitude e divisão aleatória. Variáveis vêm de scripts/base.py (decisões comuns do projeto)."""
from pathlib import Path
import json
import hashlib
import platform
from importlib.metadata import version
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, KFold, LeaveOneGroupOut
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import PoissonRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_poisson_deviance, mean_absolute_error, r2_score
from threadpoolctl import threadpool_limits

import base

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

def carregar_base(cap=False):
    """Base municipal comum (scripts/base.py). cap=True limita cada cobertura anual a 100% antes das médias."""
    return base.base_municipal('limitada' if cap else 'original')

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
            import statsmodels.api as sm
            Z=sm.add_constant(X,has_constant='add')
            glm=sm.GLM(y,Z,offset=np.log(e),family=sm.families.NegativeBinomial(alpha=self.hiper))
            # Penalização L2 fixa, intercepto sem penalidade; dispersão selecionada internamente.
            self.model=glm.fit_regularized(alpha=np.r_[0,np.repeat(.1,X.shape[1])],L1_wt=0,maxiter=1000)
        return self
    def predict(self,df):
        e=df.populacao.to_numpy(float)/1e5
        if self.tipo=='base':return np.full(len(df),self.taxa)*e
        X=self.scale.transform(self.imp.transform(df[self.cols]))
        if self.tipo=='nb':
            import statsmodels.api as sm
            pred=self.model.predict(sm.add_constant(X,has_constant='add'),offset=np.log(e))
        else:pred=self.model.predict(X)*e
        assert np.isfinite(pred).all()
        return np.maximum(pred,1e-9)

def metricas(y,p,e):
    return {'desvio_Poisson':mean_poisson_deviance(y,p),'MAE_casos':mean_absolute_error(y,p),
        'MAE_incidencia':mean_absolute_error(y/e,p/e),
        'R2_incidencia':r2_score(y/e,p/e) if len(y)>1 else np.nan,  # RRAS6 (capital) tem um município só
        'razao_pred_obs':np.sum(p)/np.sum(y)}

GRUPO={'rras':'rras','blocos':'bloco','longitude':'faixa_longitude'}

def executar(df,esquema='rras',modelos=None,permutar=False):
    modelos=MODELOS if modelos is None else {k:MODELOS[k] for k in modelos}
    if esquema=='aleatorio':outer=list(KFold(5,shuffle=True,random_state=42).split(df))
    else:outer=list(LeaveOneGroupOut().split(df,groups=df[GRUPO[esquema]]))
    preds=[];scores=[];tuning=[];importance=[];diagnostico=[]
    for fold,(tr,te) in enumerate(outer,1):
        treino=df.iloc[tr];teste=df.iloc[te]
        assert set(treino.index).isdisjoint(teste.index)
        if esquema=='aleatorio':inner=list(KFold(3,shuffle=True,random_state=43).split(treino))
        elif esquema=='rras':inner=list(GroupKFold(5).split(treino,groups=treino.rras))  # 18 RRAS em 5 grupos
        else:inner=list(LeaveOneGroupOut().split(treino,groups=treino[GRUPO[esquema]]))
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
        print(f'{esquema}: partição {fold}/{len(outer)} concluída',flush=True)
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
    paths=sorted((ROOT/'data/processed').glob('*'))+[Path(__file__),ROOT/'scripts/base.py']
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}

def rodar_tudo(destino=ROOT/'results/ml'):
    destino=Path(destino);destino.mkdir(parents=True,exist_ok=True)
    df=carregar_base();df.to_csv(destino/'base_municipal_ml.csv')
    results=[]
    with threadpool_limits(limits=1):
        results.append(executar(df,'rras',permutar=True))
        results.append(executar(df,'blocos'))
        results.append(executar(df,'longitude'))
        results.append(executar(df,'aleatorio'))
        cap=executar(carregar_base(cap=True),'rras',modelos=['Poisson + PIB + vacina','Boosting com vacina'])
        for v in cap.values():
            if 'esquema' in v:v['esquema']='rras_cob_limitada'
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
          'protocolo':'Validação externa deixando uma RRAS de fora (19); ajuste interno em 5 grupos das RRAS restantes. Sensibilidades: 5 blocos k-means, 5 faixas de longitude, 5 partes aleatórias. Critério: desvio Poisson médio por município.'}
    meta['arquivos_resultados']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(destino.glob('*.csv'))}
    (destino/'execucao.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    return df,resumo

if __name__=='__main__':
    df,res=rodar_tudo();print(res.to_string(index=False))
