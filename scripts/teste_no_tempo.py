"""Validação no tempo: o classificador treinado com o surto de 2019-20 ordena os municípios por risco;
conferimos onde caíram os casos de anos posteriores (2021-25 e 2026), que o modelo nunca viu.

Modelo: regressão logística com as variáveis de estrutura (base.ESTRUTURA), alvo >=1 caso em 2019-20.
Saída: results/classificador/teste_no_tempo.txt e ranking_risco.csv (645 municípios).
"""
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import base

OUT = base.ROOT / 'results' / 'classificador'
m = base.base_municipal()
mod = make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
mod.fit(m[base.ESTRUTURA], (m.casos_2019_20 >= 1).astype(int))
m['prob'] = mod.predict_proba(m[base.ESTRUTURA])[:, 1]
m['posicao'] = m.prob.rank(ascending=False, method='first').astype(int)

n = base.notificacoes()
n['cod'] = n.ID_MN_RESI.str[:6]
log = ['Classificador (estrutura) treinado com o surto de 2019-20; posição de risco de 1 (maior) a 645.']
for nome, a0, a1 in [('2007-18 (antes do treino)', 2007, 2018), ('2021-25', 2021, 2025), ('2026', 2026, 2026)]:
    cods = n[n.ano.between(a0, a1)].cod.unique()
    r = m.loc[m.index.intersection(cods)].sort_values('posicao')
    log.append(f'{nome}: {len(r)} municípios com caso; posições {r.posicao.tolist()}; '
               f'{(r.posicao <= 30).sum()} entre os 30 primeiros; {(r.posicao <= 7).sum()} entre os 7 primeiros (1%)')
c26 = set(n[n.ano == 2026].cod)
prox = m[~m.index.isin(list(c26))].sort_values('posicao').head(10)
log.append('Maior risco sem caso em 2026: ' + ', '.join(f'{r.no_municipio} ({r.posicao}º, {r.rras})' for _, r in prox.iterrows()))
(OUT / 'teste_no_tempo.txt').write_text('\n'.join(log), encoding='utf-8')
m[['no_municipio', 'rras', 'populacao', 'prob', 'posicao']].sort_values('posicao').to_csv(OUT / 'ranking_risco.csv')
print('\n'.join(log))
