"""Histórico de 1997 (internações SUS por sarampo, SIH) como preditor do surto de 2019-2020, e mapa 1997 x 2019.

Uso: python scripts/historico_1997.py   ->  results/historico/historico_1997.txt, mapa_1997_2019.png
Entradas: data/raw/sih_sarampo_1996_1998_municipio.csv (scripts/coleta/sih_sarampo_1996_1998.py),
base.base_municipal e data/processed/malha.json.
"""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Polygon
from scipy import stats

import base

OUT = base.ROOT / 'results' / 'historico'
OUT.mkdir(parents=True, exist_ok=True)
LOG = []


def log(x=''):
    print(x)
    LOG.append(str(x))


m = base.base_municipal()
h = pd.read_csv(base.RAW / 'sih_sarampo_1996_1998_municipio.csv', dtype={'co_ibge': str, 'ano_internacao': str})
int97 = h[h.ano_internacao.isin(['1997', '1998'])].groupby('co_ibge').internacoes.sum()  # epidemia: 1997 e cauda em 1998
m['int_97_98'] = int97.reindex(m.index).fillna(0)
m['teve_int_97'] = (m.int_97_98 > 0).astype(int)
m['log_int_97'] = np.log1p(m.int_97_98)
casos = m.casos_2019_20

log(f'Municipios com internacao por sarampo em 1997-98 (SIH): {m.teve_int_97.sum()} de {len(m)}')
log(f'  desses, com caso em 2019-20: {(casos[m.teve_int_97 == 1] > 0).mean():.0%}; '
    f'sem internacao em 1997-98: {(casos[m.teve_int_97 == 0] > 0).mean():.0%}')
log(f'  correlacao (Spearman) internacoes 1997-98 x log populacao: {stats.spearmanr(m.int_97_98, m.log_pop).statistic:.2f}')
log(f'  correlacao (Spearman) internacoes 1997-98 x casos 2019-20: {stats.spearmanr(m.int_97_98, casos).statistic:.2f}')
g = m.populacao > 1e5
log(f'  so municipios > 100 mil hab (n={g.sum()}): Spearman int 97-98 por hab x incidencia 2019-20 = '
    f'{stats.spearmanr(m.int_97_98[g] / m.populacao[g], m.incidencia_2019_20[g]).statistic:.2f}')

log('\nHistorico de 1997 como variavel do classificador (validacao espacial: 1 RRAS de fora por vez):')
AJUSTE = ['log_pop', 'dist_capital_km', 'log_pib', 'em_arranjo']
for alvo, y in {'>=1 caso': casos >= 1, '>=2 autoctones': m.autoctones_2019_20 >= 2,
                'incidencia >=20/100 mil': m.incidencia_2019_20 >= 20}.items():
    y = y.astype(int).values
    a_so = base.auc_espacial(m, ['log_int_97'], y)
    a0 = base.auc_espacial(m, base.ESTRUTURA, y)
    a1 = base.auc_espacial(m, base.ESTRUTURA + ['log_int_97'], y)
    r = base.or_ajustado(m, ['log_int_97'] + AJUSTE, y).loc['log_int_97']
    log(f'  {alvo} ({y.sum()} pos): AUC so historico {a_so:.3f} | estrutura {a0:.3f} -> +historico {a1:.3f} ({a1 - a0:+.3f}) | '
        f'OR ajustado {r.OR:.2f} ({r.IC_inf:.2f}-{r.IC_sup:.2f}) p={r.p:.3f}')
(OUT / 'historico_1997.txt').write_text('\n'.join(LOG), encoding='utf-8')

# ---------------- mapa ----------------
malha = json.loads((base.PRO / 'malha.json').read_text(encoding='utf-8'))
RAMPA = ['#e8e7e1', '#9ec5f4', '#3987e5', '#184f95']
TINTA2 = '#52514e'


def classe(v, cortes):
    for i, c in enumerate(cortes):
        if v <= c:
            return i
    return len(cortes)


def desenha(ax, valores, cortes, rotulos, titulo):
    patches, cores = [], []
    k0 = np.cos(np.radians(22.3))
    for cod, aneis in malha.items():
        cor = RAMPA[classe(valores.get(cod, 0), cortes)]
        for anel in aneis:
            a = np.array(anel)
            patches.append(Polygon(np.column_stack([a[:, 0] * k0, a[:, 1]]), closed=True))
            cores.append(cor)
    ax.add_collection(PatchCollection(patches, facecolor=cores, edgecolor='white', linewidth=.2))
    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title(titulo, loc='left', fontsize=11, fontweight='bold')
    n = [sum(classe(valores.get(c, 0), cortes) == i for c in m.index) for i in range(len(rotulos))]
    ax.legend(handles=[Patch(color=RAMPA[i], label=f'{r} ({n[i]})') for i, r in enumerate(rotulos)],
              loc='lower left', frameon=False, fontsize=8.5, title='municípios', title_fontsize=8.5)


fig, axs = plt.subplots(1, 2, figsize=(14, 5.6))
desenha(axs[0], m.int_97_98.to_dict(), [0, 1, 9], ['nenhuma', '1', '2–9', '10 ou mais'],
        'Epidemia de 1997: internações SUS por sarampo (SIH)')
desenha(axs[1], casos.to_dict(), [0, 4, 49], ['nenhum', '1–4', '5–49', '50 ou mais'],
        'Surto de 2019–2020: casos confirmados (SINAN)')
fig.text(0.01, 0.01, f'1997 só mostra casos graves (cerca de 2 internações a cada 100 casos), por isso aparecem menos municípios. '
         f'Dos {m.teve_int_97.sum()} municípios com internação em 1997–98, {(casos[m.teve_int_97 == 1] > 0).mean():.0%} '
         f'tiveram caso em 2019–20.', fontsize=8.5, color=TINTA2)
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT / 'mapa_1997_2019.png', dpi=200, bbox_inches='tight')
print('figura: results/historico/mapa_1997_2019.png')
