"""Classificador do surto de 2019-2020 por município, com quatro definições de alvo.

Pergunta: as características do município (porte, densidade, distância à capital, REGIC, arranjo, PIB) separam
quem teve caso de quem não teve? A cobertura vacinal pré-surto (média 2016-2018) acrescenta algo?
Validação espacial principal: uma RRAS de fora por vez; estratificada aleatória só para comparação.
Uso: python scripts/modelo_alvos.py   ->  results/classificador/modelo_alvos.txt e auc.csv
"""
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

import base

OUT = base.ROOT / 'results' / 'classificador'
OUT.mkdir(parents=True, exist_ok=True)
m = base.base_municipal()

ALVOS = {
    'A. >=1 caso confirmado (definicao da vigilancia)': m.casos_2019_20 >= 1,
    'B. >=1 caso autoctone': m.autoctones_2019_20 >= 1,
    'C. >=2 casos autoctones (transmissao local)': m.autoctones_2019_20 >= 2,
    'D. incidencia >=20 por 100 mil': m.incidencia_2019_20 >= 20,
}
CONJ = {
    'so populacao': ['log_pop'],
    'so cobertura D1+D2': base.COBERTURA,
    'estrutura (pop, dens, dist, REGIC, arranjo, PIB)': base.ESTRUTURA,
    'estrutura + cobertura': base.ESTRUTURA + base.COBERTURA,
}
MOD = {
    'logistica': lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000)),
    'boosting': lambda: HistGradientBoostingClassifier(max_depth=3, learning_rate=.05, max_iter=200, random_state=0),
}
CV = {'estratificada 5x': StratifiedKFold(5, shuffle=True, random_state=0), 'espacial por RRAS': base.cv_rras(m)}
LOG = []


def log(x=''):
    print(x)
    LOG.append(str(x))


log(f'645 municipios; cobertura = media {base.JANELA_COB[0]}-{base.JANELA_COB[1]}; '
    f'validacao espacial = 1 RRAS de fora por vez ({m.rras.nunique()} RRAS)')
resumo = []
for an, yb in ALVOS.items():
    y = yb.astype(int).values
    log('=' * 90)
    log(f'{an}: {y.sum()} positivos de {len(y)} ({y.mean():.0%})')
    for cvn, cv in CV.items():
        for cn, cols in CONJ.items():
            linha = []
            for mn, mk in MOD.items():
                pr = cross_val_predict(mk(), m[cols].values, y, cv=cv, method='predict_proba')[:, 1]
                auc = roc_auc_score(y, pr)
                linha.append(f'{mn} AUC {auc:.3f} BA {balanced_accuracy_score(y, pr > y.mean()):.2f}')
                resumo.append((an[:2], cvn, cn, mn, auc))
            log(f'  [{cvn:17s}] {cn:48s} ' + ' | '.join(linha))
    ors = base.or_ajustado(m, ['d1_media', 'log_pop', 'log_pib', 'dist_capital_km', 'em_arranjo'], y)
    log('  Logistica ajustada (OR por 1 DP, IC95%, p):')
    for c, r in ors.iterrows():
        log(f'    {c:16s} {r.OR:5.2f} ({r.IC_inf:.2f}-{r.IC_sup:.2f}) p={r.p:.3f}')
    log(f'  AUC univariada da cobertura D1: {roc_auc_score(y, m.d1_media):.3f}')

r = pd.DataFrame(resumo, columns=['alvo', 'cv', 'conjunto', 'modelo', 'auc'])
r.to_csv(OUT / 'auc.csv', index=False)
log('\nGanho de AUC ao somar cobertura a estrutura (validacao espacial):')
for a in r.alvo.unique():
    for mn in MOD:
        q = r[(r.alvo == a) & (r.cv == 'espacial por RRAS') & (r.modelo == mn)].set_index('conjunto').auc
        e, ec = q['estrutura (pop, dens, dist, REGIC, arranjo, PIB)'], q['estrutura + cobertura']
        log(f'  {a} {mn:9s}: estrutura {e:.3f} -> +cobertura {ec:.3f} (dif {ec - e:+.3f})')
(OUT / 'modelo_alvos.txt').write_text('\n'.join(LOG), encoding='utf-8')
