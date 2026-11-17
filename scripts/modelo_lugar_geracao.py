"""Combina "onde" (características do município) e "quem" (geração de nascimento / regime vacinal).

Uso: python scripts/modelo_lugar_geracao.py   ->  results/geracoes/modelo_lugar_geracao.txt
Entradas: base.base_municipal, casos confirmados 2019-2020 (base.notificacoes) e população por idade de 2019
(série do Ministério da Saúde; nascidos ~ 2019 - idade).

Duas formas de combinar:
 1) nível município: % da população nas gerações de risco (dose única, bebês) como variável extra do classificador;
 2) nível município x geração: cada linha é um grupo de nascidos num município; modelo de Poisson da taxa
    (casos / população do grupo) com variáveis de lugar + geração. Validação espacial: uma RRAS de fora por vez.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression, PoissonRegressor
from sklearn.metrics import mean_poisson_deviance, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

import base

OUT = base.ROOT / 'results' / 'geracoes'
OUT.mkdir(parents=True, exist_ok=True)
LOG = []


def log(x=''):
    print(x)
    LOG.append(str(x))


def geracao(nasc):
    for lim, nome in [(1980, 'ate 1980'), (1988, '1981-88'), (2001, '1989-2001 dose unica'), (2013, '2002-13 duas doses'),
                      (2017, '2014-17 queda cobertura'), (2019, '2018-19 bebes')]:
        if nasc <= lim:
            return nome
    return None


m = base.base_municipal()
LUGAR = base.ESTRUTURA
P = base.pop_idade(base.ANO_SURTO)                      # município x idade (0-80) em 2019
pa = P.stack().rename('pop').reset_index()
pa['geracao'] = [geracao(base.ANO_SURTO - i) for i in pa.idade]
cs = base.notificacoes()
cs = cs[cs.ano.isin([2019, 2020]) & cs.ano_nasc.notna()].copy()
cs['geracao'] = [geracao(int(n)) for n in cs.ano_nasc]

# ---------- 1) nível município ----------
tot = P.sum(1)
m['pct_dose_unica'] = (P.loc[:, 18:30].sum(1) / tot * 100).reindex(m.index)   # nascidos ~1989-2001
m['pct_bebes'] = (P.loc[:, 0:1].sum(1) / tot * 100).reindex(m.index)           # nascidos ~2018-2019
log('1) Nivel municipio: % da populacao em geracoes de risco (2019)')
log(f'   % dose unica (nascidos ~1989-2001): media {m.pct_dose_unica.mean():.1f}%, desvio-padrao {m.pct_dose_unica.std():.1f} pp')
log(f'   % bebes (nascidos ~2018-2019): media {m.pct_bebes.mean():.2f}%, desvio-padrao {m.pct_bebes.std():.2f} pp')
for alvo, y in {'>=1 caso': m.casos_2019_20 >= 1, '>=2 autoctones': m.autoctones_2019_20 >= 2}.items():
    y = y.astype(int).values
    a0 = base.auc_espacial(m, LUGAR, y)
    a1 = base.auc_espacial(m, LUGAR + ['pct_dose_unica', 'pct_bebes'], y)
    log(f'   alvo {alvo}: AUC lugar {a0:.3f} -> lugar + geracoes {a1:.3f}')

# ---------- 2) nível município x geração ----------
pg = pa.dropna(subset=['geracao']).groupby(['co_ibge', 'geracao'])['pop'].sum()
cg = cs.groupby(['ID_MN_RESI', 'geracao']).size()
cg.index.names = ['co_ibge', 'geracao']
d = pd.DataFrame({'pop': pg}).join(cg.rename('casos')).fillna({'casos': 0}).reset_index()
d = d.join(m[LUGAR + ['rras']], on='co_ibge')
d = d[d['pop'] > 0].reset_index(drop=True)
log(f'\n2) Nivel municipio x geracao: {len(d)} grupos, {int(d.casos.sum())} casos')


def prep(num, cat):
    tr = []
    if num:
        tr.append(('n', StandardScaler(), num))
    if cat:
        tr.append(('c', OneHotEncoder(drop='first'), cat))
    return ColumnTransformer(tr)


for nome, num, cat in [('so lugar', LUGAR, []), ('so geracao', [], ['geracao']), ('lugar + geracao', LUGAR, ['geracao'])]:
    pred = np.zeros(len(d))
    pb = np.zeros(len(d))
    for tr, te in base.cv_rras(d):
        X, Y = d.iloc[tr], d.iloc[te]
        pm = make_pipeline(prep(num, cat), PoissonRegressor(alpha=1e-4, max_iter=3000))
        pm.fit(X, X.casos / X['pop'], poissonregressor__sample_weight=X['pop'])
        pred[te] = pm.predict(Y) * Y['pop']
        lm = make_pipeline(prep(num, cat), LogisticRegression(max_iter=3000))
        lm.fit(X, (X.casos > 0).astype(int))
        pb[te] = lm.predict_proba(Y)[:, 1]
    nulo = d.casos.sum() / d['pop'].sum() * d['pop']
    d2 = 1 - mean_poisson_deviance(d.casos, np.maximum(pred, 1e-9)) / mean_poisson_deviance(d.casos, nulo)
    log(f'   {nome:16s}: deviance explicada {d2:6.1%} | AUC ">=1 caso no grupo" {roc_auc_score(d.casos > 0, pb):.3f} | '
        f'AUC ">=2 casos no grupo" {roc_auc_score(d.casos >= 2, pred):.3f}')
(OUT / 'modelo_lugar_geracao.txt').write_text('\n'.join(LOG), encoding='utf-8')
