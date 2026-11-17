"""Incidência do surto (2019-2020) por ano de nascimento no estado de SP, comparada à cobertura da época de cada coorte.

Uso: python scripts/coortes_suscetibilidade.py   ->  results/geracoes/coortes_incidencia.csv, .png, coortes_resumo.txt
Entradas: casos confirmados (base.notificacoes), população por idade da série do Ministério da Saúde em 2020
(base.pop_idade) e cobertura estadual (data/processed/cobertura_estado.csv).

Tamanho da coorte nascida no ano B = média da população com idade 2020-B e 2019-B em 2020 (referência 1º de julho):
metade dos nascidos em B já fez aniversário na data. Idade 80 = 80 anos e mais, por isso as coortes começam em 1941.
Os marcos do calendário vacinal nos rótulos (dose única, 2ª dose em 2004, campanha de 2008) ainda precisam de citação
oficial do PNI no texto.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import base

OUT = base.ROOT / 'results' / 'geracoes'
OUT.mkdir(parents=True, exist_ok=True)
c = base.notificacoes()
c = c[c.ano.isin([2019, 2020])]
pop = base.pop_idade(2020).sum()  # estado = soma dos municípios, por idade
cob = pd.read_csv(base.PRO / 'cobertura_estado.csv').set_index('ano')

anos = range(1941, 2020)
coh = pd.DataFrame(index=pd.Index(anos, name='ano_nascimento'))
coh['casos'] = c.groupby('ano_nasc').size().reindex(anos).fillna(0).astype(int)
coh['pop_coorte'] = [(pop.get(2020 - b, np.nan) + pop.get(2019 - b, np.nan)) / 2 for b in anos]
coh['incidencia_100k'] = coh.casos / coh.pop_coorte * 1e5
coh['idade_em_2019'] = 2019 - coh.index
# cobertura da 1ª dose no ano em que a coorte fez 1 ano (monovalente até 1999, tríplice D1 depois)
d1 = cob.triplice_d1.combine_first(cob.sarampo_monovalente.where(cob.index <= 1999))
coh['cob_1a_dose_ano_seguinte'] = [d1.get(b + 1, np.nan) for b in anos]
coh.round(2).to_csv(OUT / 'coortes_incidencia.csv')

ERAS = [
    ('nascidos 1941–1980', 1941, 1980, 'infecção natural na infância; 2008: campanha para 20–39 anos'),
    ('nascidos 1981–1988', 1981, 1988, 'transição; campanhas de 1992 na infância'),
    ('nascidos 1989–2001', 1989, 2001, 'dose única na rotina (2ª dose instituída em 2004)'),
    ('nascidos 2002–2013', 2002, 2013, 'duas doses na rotina'),
    ('nascidos 2014–2017', 2014, 2017, 'vacinados durante a queda de cobertura de 2016–2018'),
    ('nascidos 2018–2019', 2018, 2019, 'bebês: abaixo da idade ou com a 1ª dose por fazer'),
]
L = [f'Casos 2019-2020 com ano de nascimento: {coh.casos.sum()} de {len(c)} (sem ano de nascimento ou antes de 1941: '
     f'{len(c) - coh.casos.sum()})',
     'Incidencia acumulada 2019-2020 por grupo de coortes (casos / populacao do grupo x 100 mil):']
for nome, a, b, desc in ERAS:
    s = coh.loc[a:b]
    L.append(f'  {nome}: {s.casos.sum():6d} casos ({s.casos.sum() / coh.casos.sum():5.1%}) | '
             f'{s.casos.sum() / s.pop_coorte.sum() * 1e5:6.1f} por 100 mil | {desc}')
s = coh.loc[1995:2017]
r = stats.spearmanr(s.cob_1a_dose_ano_seguinte, s.incidencia_100k)
L.append(f'\nCoortes 1995-2017: Spearman cobertura da 1a dose (estado) x incidencia = {r.statistic:.2f} (p={r.pvalue:.3f})')
s = coh.loc[2012:2017]
r = stats.spearmanr(s.cob_1a_dose_ano_seguinte, s.incidencia_100k)
L.append(f'Coortes 2012-2017 (so TABNET recente): Spearman = {r.statistic:.2f} (p={r.pvalue:.3f}), n=6')
print('\n'.join(L))
(OUT / 'coortes_resumo.txt').write_text('\n'.join(L), encoding='utf-8')

# ---------------- figura ----------------
AZUL, LARANJA, CINZA, TINTA, TINTA2 = '#2a78d6', '#eb6834', '#b9b8b2', '#0b0b0b', '#52514e'
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': CINZA, 'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2,
                     'axes.titlelocation': 'left', 'axes.titleweight': 'bold', 'axes.grid': True, 'grid.color': '#e6e5e0',
                     'axes.axisbelow': True, 'savefig.dpi': 200, 'savefig.bbox': 'tight'})
fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 7.2), sharex=True, gridspec_kw={'height_ratios': [2.3, 1]})
x = coh.loc[1960:2019]
topo = 200
cores = [LARANJA if 1989 <= b <= 2001 or b >= 2014 else AZUL for b in x.index]
ax.bar(x.index, x.incidencia_100k.clip(upper=topo), color=cores, width=.8)
for b, dx, ha in [(2018, -0.45, 'right'), (2019, 0.45, 'left')]:
    v = x.loc[b, 'incidencia_100k']
    ax.text(b + dx, topo + 4, f'{v:.0f}', ha=ha, fontsize=9, color=TINTA)
ax.set_ylim(0, topo + 24)
ax.set_ylabel('Casos por 100 mil da coorte')
ax.set_title('Sarampo em SP (2019–2020): incidência por ano de nascimento')
faixas = [(1989, 2001, 'dose única na rotina\n(2ª dose só a partir de 2004)'), (2002, 2013, 'duas doses\nna rotina'),
          (2014, 2017, 'queda da\ncobertura'), (2018, 2019, 'bebês')]
for a, b, txt in faixas:
    ax.axvspan(a - .45, b + .45, color='#f3f2ee', zorder=0)
    ax.text((a + b) / 2, 214 if a == 2018 else 168, txt, ha='center', va='top', fontsize=8.5, color=TINTA2)
ax.text(1970, 168, 'imunidade por infecção natural\n+ campanha de 2008 (20–39 anos)', ha='center', va='top', fontsize=8.5, color=TINTA2)
ax.grid(axis='x', visible=False)
ax2.plot(d1.index - 1, d1.values, color=AZUL, marker='o', ms=3, label='1ª dose (monovalente até 1999, tríplice D1 depois)')
d2 = cob.triplice_d2.dropna()
ax2.plot(d2.index - 1, d2.values, color=LARANJA, marker='o', ms=3, label='2ª dose (tríplice D2, dado a partir de 2013)')
ax2.axhline(95, color=TINTA2, lw=1, ls='--')
ax2.text(1960.5, 97, 'meta 95%', fontsize=8, color=TINTA2)
ax2.set_ylim(55, 140)
ax2.set_ylabel('Cobertura no estado (%)')
ax2.set_xlabel('Ano de nascimento (cobertura plotada no ano de nascimento da coorte vacinada no ano seguinte)')
ax2.legend(fontsize=8, loc='upper left', frameon=False)
ax2.set_xlim(1959.3, 2019.7)
ax2.set_title('Cobertura vacinal registrada no estado (TABNET PNI; antes de 1995 não disponível)', fontsize=10)
fig.tight_layout()
fig.savefig(OUT / 'coortes_incidencia.png')
print('figura: results/geracoes/coortes_incidencia.png')
