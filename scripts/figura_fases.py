"""Mapas dos casos confirmados por fase, 2007-2026 (figura da apresentação).

Lê data/processed/notificacoes.csv e malha.json; grava results/apresentacao/06_fases_mapas.png.
Caso = CLASSI_FIN 1, ano pela DT_CASO, município de residência (ID_MN_RESI).
"""
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.collections import PatchCollection
from matplotlib.patches import Patch, Polygon

import base

OUT = base.ROOT / 'results' / 'apresentacao'
OUT.mkdir(parents=True, exist_ok=True)

n = pd.read_csv(base.PRO / 'notificacoes.csv', dtype=str, usecols=['CLASSI_FIN', 'DT_CASO', 'ID_MN_RESI'])
n = n[n.CLASSI_FIN == '1'].copy()
n['ano'] = pd.to_datetime(n.DT_CASO, errors='coerce').dt.year
n['cod'] = n.ID_MN_RESI.str[:6]

FASES = [('2007–2018', 2007, 2018), ('2019', 2019, 2019), ('2020', 2020, 2020),
         ('2021–2025', 2021, 2025), ('2026', 2026, 2026)]
CORTES, ROTULOS = [0, 4, 49], ['nenhum', '1–4', '5–49', '50 ou mais']
RAMPA = ['#E4E0D6', '#F2B8A8', '#E5533A', '#8E2414']
PAPEL, TINTA, CINZA = '#F6F3EC', '#11161D', '#5C6570'

malha = json.loads((base.PRO / 'malha.json').read_text(encoding='utf-8'))
k0 = np.cos(np.radians(22.3))


def classe(v):
    for i, c in enumerate(CORTES):
        if v <= c:
            return i
    return len(CORTES)


fig, axs = plt.subplots(1, 5, figsize=(20, 4.6), facecolor=PAPEL)
for ax, (rot, a0, a1) in zip(axs, FASES):
    sel = n[(n.ano >= a0) & (n.ano <= a1)]
    casos = sel.groupby('cod').size().to_dict()
    patches, cores = [], []
    for cod, aneis in malha.items():
        cor = RAMPA[classe(casos.get(cod, 0))]
        for anel in aneis:
            a = np.array(anel)
            patches.append(Polygon(np.column_stack([a[:, 0] * k0, a[:, 1]]), closed=True))
            cores.append(cor)
    ax.add_collection(PatchCollection(patches, facecolor=cores, edgecolor=PAPEL, linewidth=.15))
    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_facecolor(PAPEL)
    ax.set_title(rot, loc='left', fontsize=20, fontweight='bold', color=TINTA, pad=26)
    ax.text(0, 1.02, f'{len(sel):,} casos · {len(casos)} municípios'.replace(',', '.'),
            transform=ax.transAxes, fontsize=13, color=CINZA)
    print(rot, len(sel), 'casos', len(casos), 'municipios')

fig.legend(handles=[Patch(color=RAMPA[i], label=r) for i, r in enumerate(ROTULOS)], loc='lower center',
           ncol=4, frameon=False, fontsize=13, title='casos confirmados no município', title_fontsize=12)
fig.tight_layout(rect=(0, 0.1, 1, 1))
fig.savefig(OUT / '06_fases_mapas.png', dpi=170, facecolor=PAPEL, bbox_inches='tight')
print('figura: results/apresentacao/06_fases_mapas.png')
