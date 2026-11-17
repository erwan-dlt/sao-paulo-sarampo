"""EDA do período inteiro (2007-2026) em três painéis, para a apresentação.

A: casos confirmados por ano (escala log) e cobertura estadual D1/D2 da tríplice viral.
B: % de municípios com pelo menos 1 caso, por faixa de população, em 2019-20 e nos demais anos.
C: composição por idade dos casos em cada fase.
Grava results/apresentacao/07_eda_periodo.png e imprime os números usados.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import base

OUT = base.ROOT / 'results' / 'apresentacao'
PAPEL, TINTA, CINZA = '#F6F3EC', '#11161D', '#5C6570'
VERM, PETR, AREIA = '#D2432B', '#17809C', '#C9C3B6'

n = base.notificacoes()
n = n[n.ano.between(2007, 2026)].copy()
n['cod'] = n.ID_MN_RESI.str[:6]
cob = pd.read_csv(base.PRO / 'cobertura_estado.csv').set_index('ano')

fig = plt.figure(figsize=(21, 6.6), facecolor=PAPEL)
gs = fig.add_gridspec(2, 3, width_ratios=[1.25, 1, 1], height_ratios=[1, 1.25], hspace=.12, wspace=.28)
axA1, axA2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0])
axs = [axA2, fig.add_subplot(gs[:, 1]), fig.add_subplot(gs[:, 2])]
for ax in axs + [axA1]:
    ax.set_facecolor(PAPEL)
    for s in ['top', 'right']:
        ax.spines[s].set_visible(False)

# ---------- A: cobertura estadual (em cima) e casos por ano (embaixo) ----------
anos = np.arange(2007, 2027)
ax = axA1
ax.plot(cob.loc[2007:2026].index, cob.loc[2007:2026, 'triplice_d1'], color=PETR, lw=2.5, marker='o', ms=4, label='D1')
ax.plot(cob.loc[2013:2026].index, cob.loc[2013:2026, 'triplice_d2'], color=PETR, lw=2.5, ls='--', marker='o', ms=4, label='D2')
ax.axhline(95, color=CINZA, lw=.8, ls=':', label='meta 95%')
ax.axvline(2022.5, color=CINZA, lw=1, ls=':')
ax.text(2022.7, 60, 'troca de sistema', fontsize=9, color=CINZA)
ax.set_ylim(55, 110)
ax.set_xlim(2006.4, 2026.6)
ax.set_xticks([])
ax.spines['bottom'].set_visible(False)
ax.set_ylabel('cobertura (%)', color=PETR, fontsize=12)
ax.legend(loc='lower left', frameon=False, fontsize=10, ncol=3)
ax.set_title('Cobertura no estado e casos por ano', loc='left', fontsize=16, fontweight='bold', color=TINTA, pad=12)

ax = axA2
casos = n.groupby('ano').size().reindex(anos, fill_value=0)
ax.bar(anos, casos.replace(0, np.nan), color=[VERM if a in (2019, 2020) else AREIA for a in anos], width=.75)
ax.set_yscale('log')
ax.set_ylim(.7, 90000)
ax.set_xlim(2006.4, 2026.6)
ax.set_ylabel('casos (escala log)', color=CINZA, fontsize=12)
for a, c in casos.items():
    if c > 0:
        ax.text(a, c * 1.35, f'{c:,}'.replace(',', '.'), ha='center', fontsize=9, color=TINTA)
ax.set_xticks([2007, 2010, 2013, 2016, 2019, 2022, 2026])

# ---------- B: porte ----------
ax = axs[1]
pop = base.painel().query('ano == 2019').set_index('co_ibge').populacao
cortes = [0, 10_000, 50_000, 100_000, 500_000, np.inf]
rot = ['<10\nmil', '10–50\nmil', '50–100\nmil', '100–500\nmil', '≥500\nmil']
faixa = pd.cut(pop, cortes, labels=rot, right=False)
surto = set(n[n.ano.isin([2019, 2020])].cod)
outros = set(n[~n.ano.isin([2019, 2020])].cod)
tab = pd.DataFrame({'faixa': faixa, 'surto': pop.index.isin(list(surto)), 'outros': pop.index.isin(list(outros))})
g = tab.groupby('faixa', observed=False).agg(n=('surto', 'size'), surto=('surto', 'mean'), outros=('outros', 'mean'))
x = np.arange(len(rot))
ax.bar(x - .2, g.surto * 100, .4, color=VERM, label='2019–20')
ax.bar(x + .2, g.outros * 100, .4, color=AREIA, label='outros anos')
for i, (s, o) in enumerate(zip(g.surto, g.outros)):
    ax.text(i - .2, s * 100 + 2, f'{s:.0%}', ha='center', fontsize=10, color=TINTA)
    ax.text(i + .2, o * 100 + 2, f'{o:.0%}', ha='center', fontsize=10, color=TINTA)
ax.set_xticks(x, [f'{r}\n({k})' for r, k in zip(rot, g.n)], fontsize=10)
ax.set_ylim(0, 128)
ax.set_ylabel('% dos municípios com pelo menos 1 caso', color=CINZA, fontsize=12)
ax.legend(loc='upper left', frameon=False, fontsize=10, ncol=2)
ax.set_title('Porte do município (população 2019)', loc='left', fontsize=16, fontweight='bold', color=TINTA, pad=12)

# ---------- C: idade por fase ----------
ax = axs[2]
FASES = [('2007–18', 2007, 2018), ('2019', 2019, 2019), ('2020', 2020, 2020), ('2021–25', 2021, 2025), ('2026', 2026, 2026)]
GR = [('<1', 0, 1), ('1–4', 1, 5), ('5–19', 5, 20), ('20–29', 20, 30), ('30–39', 30, 40), ('40+', 40, 200)]
CORES = ['#8E2414', '#D2432B', '#F2B8A8', '#17809C', '#7FB9C9', '#C9C3B6']
comp, ns = [], []
for rf, a0, a1 in FASES:
    idade = n[n.ano.between(a0, a1)].idade.dropna()
    ns.append(len(idade))
    comp.append([((idade >= lo) & (idade < hi)).mean() * 100 for _, lo, hi in GR])
    print(rf, len(idade), 'casos com idade;', ' '.join(f'{g[0]} {v:.0f}%' for g, v in zip(GR, comp[-1])))
comp = np.array(comp)
esq = np.zeros(len(FASES))
y = np.arange(len(FASES))[::-1]
for j, (gn, _, _) in enumerate(GR):
    ax.barh(y, comp[:, j], left=esq, color=CORES[j], label=gn, height=.62)
    for i in range(len(FASES)):
        if comp[i, j] >= 9:
            ax.text(esq[i] + comp[i, j] / 2, y[i], f'{comp[i, j]:.0f}%', ha='center', va='center', fontsize=9.5,
                    color='white' if j in (0, 1, 3) else TINTA)
    esq += comp[:, j]
ax.set_yticks(y, [f'{f[0]}\nn = {k:,}'.replace(',', '.') for f, k in zip(FASES, ns)], fontsize=12)
ax.set_xlim(0, 100)
ax.set_xlabel('% dos casos da fase', color=CINZA, fontsize=12)
ax.legend(loc='upper center', bbox_to_anchor=(.5, -.13), ncol=6, frameon=False, fontsize=10, title='idade (anos)', title_fontsize=10)
ax.set_title('Idade dos casos em cada fase', loc='left', fontsize=16, fontweight='bold', color=TINTA, pad=12)

print('casos por ano:', casos.to_dict())
print(g.round(3).to_string())

fig.savefig(OUT / '07_eda_periodo.png', dpi=170, facecolor=PAPEL, bbox_inches='tight')
print('figura: results/apresentacao/07_eda_periodo.png')
