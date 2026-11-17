"""Perfis do k-means (k = 3) num plano legível para a apresentação.

Lê results/clustering/municipios.csv (saída de scripts/clustering.py).
x = cobertura D1 média 2016-18 (a mesma usada no agrupamento), y = densidade (escala log),
cor = grupo, tamanho = casos de 2019. Grava results/apresentacao/08_clusters.png.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import base

PAPEL, TINTA, CINZA = '#F6F3EC', '#11161D', '#5C6570'
CORES = {1: '#E0A15A', 2: '#17809C', 3: '#D2432B'}

d = pd.read_csv(base.ROOT / 'results' / 'clustering' / 'municipios.csv')
d['densidade'] = np.exp(d.log_densidade)
fig, ax = plt.subplots(figsize=(10.5, 5), facecolor=PAPEL)
ax.set_facecolor(PAPEL)
for s in ['top', 'right']:
    ax.spines[s].set_visible(False)
for g in [2, 1, 3]:
    s = d[d.grupo == g]
    ax.scatter(s.d1_media, s.densidade, s=12 + np.sqrt(s.casos) * 9, color=CORES[g], alpha=.6, edgecolor='white', lw=.4,
               label=f'Grupo {g} · {len(s)} municípios · {int(s.casos.sum()):,} casos'.replace(',', '.'))
ax.set_yscale('log')
ax.set_xlabel('cobertura D1 média 2016–18 (%)', fontsize=17, color=CINZA)
ax.set_ylabel('densidade (hab/km², escala log)', fontsize=17, color=CINZA)
ax.tick_params(labelsize=15)
from matplotlib.lines import Line2D
handles = [Line2D([], [], marker='o', ls='', ms=13, color=CORES[g], alpha=.8,
                  label=f'Grupo {g} · {(d.grupo == g).sum()} municípios · {int(d[d.grupo == g].casos.sum()):,} casos'.replace(',', '.'))
           for g in [1, 2, 3]]
ax.legend(handles=handles, loc='upper left', frameon=False, fontsize=16)
ax.text(.99, .02, 'tamanho do ponto = casos em 2019', transform=ax.transAxes, ha='right', fontsize=14, color=CINZA)
print(d.groupby('grupo').agg(n=('casos', 'size'), casos=('casos', 'sum'), d1=('d1_media', 'median'), dens=('densidade', 'median')).round(1))
fig.tight_layout()
fig.savefig(base.ROOT / 'results' / 'apresentacao' / '08_clusters.png', dpi=170, facecolor=PAPEL)
print('figura: results/apresentacao/08_clusters.png')
