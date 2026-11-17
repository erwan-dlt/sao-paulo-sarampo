"""Figuras da parte de dados (integração e limpeza) para a apresentação.

Uso: python scripts/figuras_dados.py   ->  results/apresentacao/*.png
Todas as contagens são calculadas aqui a partir de data/raw e data/processed (nada digitado à mão, exceto o total
nacional de notificações, impresso por prepare_data.py, e o total oficial da RIPSA, lido do arquivo).
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

import base

OUT = base.ROOT / 'results' / 'apresentacao'
OUT.mkdir(parents=True, exist_ok=True)
AZUL, LARANJA, AQUA = '#2a78d6', '#eb6834', '#1baf7a'
TINTA, TINTA2, CINZA, GRADE, FUNDO = '#0b0b0b', '#52514e', '#b9b8b2', '#e6e5e0', '#fcfcfb'
plt.rcParams.update({'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': CINZA,
                     'axes.labelcolor': TINTA2, 'xtick.color': TINTA2, 'ytick.color': TINTA2, 'text.color': TINTA,
                     'axes.titlelocation': 'left', 'axes.titleweight': 'bold', 'axes.titlesize': 13,
                     'figure.facecolor': FUNDO, 'axes.facecolor': FUNDO, 'savefig.dpi': 200, 'savefig.bbox': 'tight'})
fmt = lambda v: f'{v:,.0f}'.replace(',', '.')
COLS = ['arquivo', 'CLASSI_FIN', 'DT_NOTIFIC', 'DT_SIN_PRI', 'DT_INICIO_', 'DT_CASO', 'ORIGEM_DT_CASO']
n = pd.read_csv(base.PRO / 'notificacoes.csv', dtype=str, keep_default_na=False, usecols=COLS)
conf = n[n.CLASSI_FIN.eq('1')].copy()
conf['ano'] = pd.to_datetime(conf.DT_CASO).dt.year

# ---------------------------------------------------------------- 1. funil do recorte
etapas = [('Notificações no Brasil (SINAN 2007–2026)', 257378),  # soma impressa por prepare_data.py
          ('Residentes em São Paulo', len(n)),
          ('Nos arquivos de 2019 e 2020', int(n.arquivo.isin(['EXANBR19.dbc', 'EXANBR20.dbc']).sum())),
          ('Confirmados como sarampo', int(conf.arquivo.isin(['EXANBR19.dbc', 'EXANBR20.dbc']).sum())),
          ('Caso em 2019 (data do caso)', int(conf.ano.eq(2019).sum()))]
fig, ax = plt.subplots(figsize=(11, 4.2))
y = np.arange(len(etapas))[::-1]
ax.barh(y, [v for _, v in etapas], color=AZUL, height=.6)
for yi, (rot, v) in zip(y, etapas):
    ax.text(v + 3000, yi, fmt(v), va='center', fontsize=11, color=TINTA)
ax.set_yticks(y, [r for r, _ in etapas])
ax.set_xlim(0, 300000); ax.set_xticks([]); ax.spines['bottom'].set_visible(False); ax.spines['left'].set_visible(False)
ax.tick_params(axis='y', length=0)
ax.set_title('Do arquivo nacional à coorte de 2019')
fig.savefig(OUT / '01_funil_recorte.png'); plt.close(fig)

# ---------------------------------------------------------------- 2. regra da data do caso
ex = conf[conf.ORIGEM_DT_CASO.eq('primeiros sintomas') & conf.DT_INICIO_.ne('') & conf.ano.eq(2019)]
ex = ex.assign(gap=(pd.to_datetime(ex.DT_NOTIFIC) - pd.to_datetime(ex.DT_INICIO_)).dt.days).nlargest(3, 'gap')
br = lambda s: pd.to_datetime(s).strftime('%d/%m/%Y')
linhas = [[br(r.DT_INICIO_), br(r.DT_SIN_PRI), br(r.DT_NOTIFIC), br(r.DT_CASO)] for r in ex.itertuples()]
linhas.append(['(vazio)', '—', '—', 'primeiros sintomas'])
ripsa = pd.read_csv(base.RAW / 'ripsa008mb.csv.zip', usecols=['co_anomes', 'co_uf', 'sg_categoria', 'vl_indicador_calculado_mun'])
ripsa19 = int(ripsa[(ripsa.co_uf == 35) & (ripsa.sg_categoria == 'TC') & (ripsa.co_anomes // 100 == 2019)].vl_indicador_calculado_mun.sum())
so_ex = int(pd.to_datetime(conf.DT_INICIO_, errors='coerce').dt.year.eq(2019).sum())
regra = int(conf.ano.eq(2019).sum())
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 3.9), gridspec_kw={'width_ratios': [1.45, 1]})
a1.axis('off')
t = a1.table(cellText=linhas, colLabels=['Exantema', 'Primeiros sintomas', 'Notificação', 'Data do caso usada'],
             loc='center', cellLoc='center', colColours=['#eef3fb'] * 4)
t.auto_set_font_size(False); t.set_fontsize(10.5); t.scale(1, 1.75)
for (r, c), cell in t.get_celld().items():
    cell.set_edgecolor(GRADE)
    if r > 0 and r <= len(ex) and c == 0:
        cell.get_text().set_color(LARANJA); cell.get_text().set_fontweight('bold')
a1.set_title('Exemplos reais: ano do exantema digitado errado')
a1.text(0, -.02, f'{(conf.ORIGEM_DT_CASO == "primeiros sintomas").sum()} confirmados corrigidos (2007–2026): '
        f'{(conf.DT_INICIO_ == "").sum()} sem exantema, {((conf.ORIGEM_DT_CASO == "primeiros sintomas") & conf.DT_INICIO_.ne("")).sum()} '
        'com exantema >365 dias antes ou >30 dias depois da notificação.', transform=a1.transAxes, fontsize=9, color=TINTA2)
vals = [('Só exantema\n(critério original)', so_ex, CINZA), ('Regra do projeto\n(data do caso)', regra, AZUL),
        ('RIPSA\n(indicador oficial)', ripsa19, TINTA2)]
a2.axis('off')
for i, (rot, v, cor) in enumerate(vals):
    yy = .78 - i * .3
    a2.text(.02, yy, fmt(v), fontsize=24, fontweight='bold', color=AZUL if cor == AZUL else TINTA, va='center', transform=a2.transAxes)
    a2.text(.42, yy, rot, fontsize=10.5, color=TINTA2, va='center', transform=a2.transAxes)
a2.set_title('Casos em 2019')
fig.tight_layout(); fig.savefig(OUT / '02_regra_data_do_caso.png'); plt.close(fig)

# ---------------------------------------------------------------- 3. população: degrau x série revisada
pa = pd.read_csv(base.PRO / 'municipio_ano.csv', usecols=['co_ibge', 'ano', 'populacao', 'populacao_ibge'], dtype={'co_ibge': str})
tot = pa.groupby('ano')[['populacao', 'populacao_ibge']].sum(min_count=645) / 1e6
tot = tot.loc[2012:2025]
g = pa.sort_values(['co_ibge', 'ano']).groupby('co_ibge').populacao_ibge.pct_change(fill_method=None)
saltos = int((g[pa.sort_values(['co_ibge', 'ano']).ano.eq(2022).values].abs() > .15).sum())
fig, ax = plt.subplots(figsize=(11, 4.6))
ib = tot.populacao_ibge.dropna()
ax.plot(ib.index, ib.values, color=LARANJA, lw=2, marker='o', ms=5, label='IBGE publicado na época (2022 = Censo)')
ax.plot(tot.index, tot.populacao, color=AZUL, lw=2, marker='o', ms=5, label='Ministério da Saúde, série revisada (usada)')
queda = f'{(ib.loc[2021] - ib.loc[2022]):.1f}'.replace('.', ',')
ax.annotate(f'−{queda} milhões em um ano\n{saltos} municípios mudam mais de 15%',
            xy=(2022, ib.loc[2022]), xytext=(2017.3, 43.0), fontsize=10, color=TINTA,
            arrowprops=dict(arrowstyle='->', color=TINTA2, lw=1))
ax.text(2025.15, tot.populacao.loc[2025], 'Ministério', color=TINTA2, va='center', fontsize=10)
ax.text(2020.1, ib.loc[2020] + .15, 'IBGE', color=TINTA2, va='bottom', ha='right', fontsize=10)
ax.set_ylabel('População do estado (milhões)'); ax.set_xticks(range(2012, 2026, 2))
ax.grid(axis='y', color=GRADE); ax.set_axisbelow(True); ax.legend(frameon=False, fontsize=9.5, loc='lower right')
ax.set_title('População: a quebra de 2022 e a série que a evita')
fig.savefig(OUT / '03_populacao_quebra.png'); plt.close(fig)

# ---------------------------------------------------------------- 4. cobertura: >100% e troca de sistema
cob = pd.read_csv(base.PRO / 'municipio_ano.csv', usecols=['ano', 'cob_triplice_d1'])
uf = pd.read_csv(base.PRO / 'cobertura_estado.csv').set_index('ano').loc[2012:2026]
d1 = cob.cob_triplice_d1.dropna()
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13.5, 4.6), gridspec_kw={'width_ratios': [1, 1.2]})
bins = np.arange(0, 205, 10)
h, _ = np.histogram(d1.clip(upper=200), bins=bins)
a1.bar(bins[:-1] + 5, h, width=9, color=[AZUL if b < 100 else LARANJA for b in bins[:-1]])
a1.axvline(100, color=TINTA2, lw=1, ls='--')
a1.text(103, h.max() * .92, f'{(d1 > 100).mean():.0%} acima de 100%\n({fmt((d1 > 100).sum())} de {fmt(len(d1))})', fontsize=10, color=TINTA)
a1.set_xlabel('Cobertura D1 municipal (%), 2012–2026 (≥200 agrupado)'); a1.set_ylabel('Município-anos')
a1.set_title('Cobertura municipal: valores impossíveis são comuns')
a1.grid(axis='y', color=GRADE); a1.set_axisbelow(True)
a2.axvspan(2019.5, 2022.5, color='#f3f2ee', zorder=0)
a2.text(2021, 101, 'TABNET\n"em revisão"', ha='center', fontsize=9, color=TINTA2)
a2.axvline(2022.5, color=TINTA2, lw=1)
a2.text(2022.6, 61, 'troca de sistema\nTABNET → InfoMS', fontsize=9, color=TINTA2)
for col, cor, rot in [('triplice_d1', AZUL, 'D1'), ('triplice_d2', LARANJA, 'D2')]:
    s = uf[col].dropna()
    a2.plot(s.index, s.values, color=cor, lw=2, marker='o', ms=4, label=rot)
    a2.text(2026.25, s.iloc[-1], f'{rot}', color=TINTA2, va='center', fontsize=10)
a2.axhline(95, color=TINTA2, lw=.8, ls=':'); a2.text(2012, 96, 'meta 95%', fontsize=8.5, color=TINTA2)
a2.set_ylim(58, 110); a2.set_ylabel('Cobertura no estado (%)'); a2.set_xlabel('Ano (2026 parcial)'); a2.legend(frameon=False, fontsize=9.5, loc='lower left')
a2.set_title(f'Cobertura estadual: na troca de sistema a D1 salta de {uf.triplice_d1.loc[2022]:.0f}% para {uf.triplice_d1.loc[2023]:.0f}%', fontsize=12)
a2.grid(axis='y', color=GRADE); a2.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT / '04_cobertura_problemas.png'); plt.close(fig)

# ---------------------------------------------------------------- 5. pipeline
fig, ax = plt.subplots(figsize=(14, 3.6)); ax.axis('off'); ax.set_xlim(0, 14); ax.set_ylim(0, 3.3)


def caixa(x, y, w, h, titulo, texto, cor):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.02,rounding_size=0.12', fc='white', ec=cor, lw=1.6))
    ax.text(x + .15, y + h - .2, titulo, fontsize=11, fontweight='bold', va='top', color=TINTA)
    ax.text(x + .15, y + h - .58, texto, fontsize=8.8, va='top', color=TINTA2, linespacing=1.35)


def seta(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>', mutation_scale=14, color=TINTA2, lw=1.2))


L = '\n'.join
caixa(.1, .1, 3.1, 3.0, 'data/raw  (fontes)', L(['SINAN 2007–2026 (20 DBC)', 'População Min. Saúde 2000–2025',
      'IBGE/SIDRA: estimativas, PIB, Censo', 'PNI: TABNET 1995–2022 e InfoMS', 'REGIC 2018 · malha IBGE',
      'RIPSA · SIH/SUS', '', 'scripts/coleta/ baixou cada uma', '38 arquivos com SHA-256']), AZUL)
caixa(3.85, .95, 2.6, 1.3, 'prepare_data.py', L(['limpeza e junção', 'travas de totais', 'manifesto de hashes']), LARANJA)
caixa(7.1, .1, 3.1, 3.0, 'data/processed', L(['notificacoes.csv — 94.429 linhas', '   (1 por notificação)',
      'municipio.csv — 645 linhas (fixo)', 'municipio_ano.csv — 9.675 linhas', '   (645 × 15 anos)',
      'cobertura_estado.csv', 'malha.json · vizinhos.json', '', 'chave: co_ibge (6 díg.) + ano']), AZUL)
caixa(10.85, 1.85, 3.05, 1.25, 'base.py', L(['decisões comuns:', '18.109 casos · cobertura 2016–18', '1 RRAS de fora por vez']), LARANJA)
caixa(10.85, .1, 3.05, 1.55, 'análises → notebook', L(['modelagem · clustering', 'classificador · gerações',
      'histórico 1997 · projeção', 'results/ → 19 seções']), AQUA)
seta(3.2, 1.6, 3.85, 1.6); seta(6.45, 1.6, 7.1, 1.6); seta(10.2, 2.5, 10.85, 2.5); seta(12.4, 1.85, 12.4, 1.65)
ax.set_title('Pipeline: das fontes ao notebook, reproduzível sem internet', loc='left')
fig.savefig(OUT / '05_pipeline.png'); plt.close(fig)
print('figuras em', OUT, ':', sorted(p.name for p in OUT.glob('*.png')))
