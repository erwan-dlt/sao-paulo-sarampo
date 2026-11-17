"""Projeção 2026-2027: quantas crianças ficam sem a 1ª e sem a 2ª dose da tríplice viral, por cenário de cobertura.

Uso: python scripts/projecao.py   ->  results/projecao/ (cenarios_estado.csv, cenarios_rras.csv, resumo.txt, projecao.png)

O que é dado e o que é suposição:
  * dado: numeradores (doses aplicadas) e denominadores (população-alvo do PNI) do InfoMS, por município, 2023-2025;
    2026 é parcial e aparece só como referência. Agregados por RRAS e estado como soma de doses / soma da população-alvo
    (doses aplicadas a residentes de um município vizinho se compensam dentro da região).
  * suposição 1: a população-alvo de 2026 e de 2027 é igual à de 2025 (tamanho das coortes constante).
  * suposição 2 (cenários, escolha do projeto, não previsões):
      - "mantém 2023-2025": cobertura média do triênio (soma das doses / soma da população-alvo) em cada RRAS;
      - "repete o pior ano": o menor valor de 2023-2025 em cada RRAS;
      - "meta de 95%": 95% nas RRAS abaixo da meta; as demais mantêm a média do triênio.
  * resultado: crianças da população-alvo SEM a dose = população-alvo x (1 - cobertura), com cobertura limitada a 100%.
    Não é número de suscetíveis: vacinados podem não responder à vacina e não vacinados podem ter tido sarampo.
  * contexto: tamanho, em 2025, da geração nascida em 1989-2001 (dose única na rotina; 93 casos por 100 mil em
    2019-2020), pela série de população do Ministério da Saúde. Não há dado aberto sobre quantos foram vacinados depois.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import base
from prepare_data import cobertura_infoms

OUT = base.ROOT / 'results' / 'projecao'
OUT.mkdir(parents=True, exist_ok=True)
ANOS_OBS = [2023, 2024, 2025]
ANOS_PROJ = [2026, 2027]

mun = base.municipios()
inf = cobertura_infoms().join(mun[['rras']], on='co_ibge')
for c in ['num_d1', 'den_d1', 'num_d2', 'den_d2']:
    inf[c] = pd.to_numeric(inf[c], errors='coerce').fillna(0)


def agrega(d, por):
    g = d.groupby(por)[['num_d1', 'den_d1', 'num_d2', 'den_d2']].sum()
    g['cob_d1'] = g.num_d1 / g.den_d1 * 100
    g['cob_d2'] = g.num_d2 / g.den_d2 * 100
    return g


obs = agrega(inf[inf.ano.isin(ANOS_OBS)], ['rras', 'ano'])
estado_obs = agrega(inf, ['ano'])
media = agrega(inf[inf.ano.isin(ANOS_OBS)], ['rras'])
alvo = obs.xs(2025, level='ano')[['den_d1', 'den_d2']]                    # suposição 1
cen = {
    'mantém 2023-2025': media[['cob_d1', 'cob_d2']],
    'repete o pior ano': obs.groupby('rras')[['cob_d1', 'cob_d2']].min(),
    'meta de 95%': media[['cob_d1', 'cob_d2']].clip(lower=95),
}

linhas = []
for nome, cob in cen.items():
    for ano in ANOS_PROJ:
        for d in ('d1', 'd2'):
            sem = alvo[f'den_{d}'] * (1 - cob[f'cob_{d}'].clip(upper=100) / 100)
            linhas += [{'cenario': nome, 'ano': ano, 'dose': d.upper(), 'rras': r, 'populacao_alvo': alvo.loc[r, f'den_{d}'],
                        'cobertura': cob.loc[r, f'cob_{d}'], 'sem_dose': v} for r, v in sem.items()]
for ano in ANOS_OBS:
    for d in ('d1', 'd2'):
        o = obs.xs(ano, level='ano')
        sem = o[f'den_{d}'] * (1 - o[f'cob_{d}'].clip(upper=100) / 100)
        linhas += [{'cenario': 'observado', 'ano': ano, 'dose': d.upper(), 'rras': r, 'populacao_alvo': o.loc[r, f'den_{d}'],
                    'cobertura': o.loc[r, f'cob_{d}'], 'sem_dose': v} for r, v in sem.items()]
rr = pd.DataFrame(linhas)
rr.to_csv(OUT / 'cenarios_rras.csv', index=False)

est = rr.groupby(['cenario', 'ano', 'dose']).agg(populacao_alvo=('populacao_alvo', 'sum'), sem_dose=('sem_dose', 'sum')).reset_index()
est['cobertura_implicita'] = 100 * (1 - est.sem_dose / est.populacao_alvo)
est.round(1).to_csv(OUT / 'cenarios_estado.csv', index=False)

# geração de dose única em 2025 (contexto)
pop25 = base.pop_idade(2025).sum()
dose_unica = pop25.loc[2025 - 2001:2025 - 1989].sum()   # nascidos 1989-2001 têm 24 a 36 anos em 2025

L = ['Cobertura estadual (soma de doses / soma da populacao-alvo, InfoMS):']
L += [f'  {a}: D1 {r.cob_d1:.1f}%  D2 {r.cob_d2:.1f}%' + ('  (parcial)' if a == 2026 else '') for a, r in estado_obs.iterrows()]
L.append('\nCriancas da populacao-alvo sem a dose, estado (soma das RRAS; cobertura de cada RRAS limitada a 100%):')
tab = est.pivot_table(index=['cenario', 'ano'], columns='dose', values='sem_dose').round(0)
L.append(tab.to_string())
proj = est[est.ano.isin(ANOS_PROJ)].groupby(['cenario', 'dose']).sem_dose.sum().unstack()
obs_tot = est[est.cenario.eq('observado')].groupby('dose').sem_dose.sum()
L.append('\nAcumulado 2026-2027 por cenario (e somando 2023-2025 observado):')
for c in cen:
    L.append(f'  {c:18s}: sem D1 {proj.loc[c, "D1"]:8,.0f} ({proj.loc[c, "D1"] + obs_tot["D1"]:8,.0f}) | '
             f'sem D2 {proj.loc[c, "D2"]:8,.0f} ({proj.loc[c, "D2"] + obs_tot["D2"]:8,.0f})')
base_r = rr[rr.cenario.eq('mantém 2023-2025') & rr.ano.isin(ANOS_PROJ)].pivot_table(index='rras', columns='dose', values='sem_dose', aggfunc='sum')
base_r['por_mil_alvo_D2'] = base_r.D2 / (2 * alvo.den_d2) * 1000
L.append('\nCenario "mantem 2023-2025", 2026-2027, RRAS com mais criancas sem D2:')
L.append(base_r.sort_values('D2', ascending=False).head(8).round(0).to_string())
L.append(f'\nGeracao nascida em 1989-2001 (24 a 36 anos em 2025), serie do Ministerio da Saude: {dose_unica:,.0f} pessoas '
         f'({dose_unica / pop25.sum():.1%} da populacao do estado).')
print('\n'.join(L))
(OUT / 'resumo.txt').write_text('\n'.join(L), encoding='utf-8')

# ---------------- figura ----------------
AZUL, LARANJA, CINZA, TINTA2 = '#2a78d6', '#eb6834', '#b9b8b2', '#52514e'
CORES = {'repete o pior ano': '#a93f62', 'mantém 2023-2025': AZUL, 'meta de 95%': '#5e8b3a'}
plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.titlelocation': 'left',
                     'axes.titleweight': 'bold'})
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 5), gridspec_kw={'width_ratios': [1.3, 1]})
uf = pd.read_csv(base.PRO / 'cobertura_estado.csv').set_index('ano')
for d, cor in [('d1', AZUL), ('d2', LARANJA)]:
    s = uf[f'triplice_{d}'].loc[2012:2025].dropna()
    a1.plot(s.index, s.values, marker='o', ms=3, color=cor, label=f'{d.upper()} observada')
    a1.plot([2026], [uf.loc[2026, f'triplice_{d}']], marker='o', mfc='white', color=cor, ls='none')
    for c, cc in CORES.items():
        v = est[(est.cenario == c) & (est.dose == d.upper())].set_index('ano').cobertura_implicita.loc[ANOS_PROJ]
        a1.plot([2025] + ANOS_PROJ, [s.loc[2025]] + list(v.values), color=cc, ls='--', lw=1.2)
a1.axhline(95, color=TINTA2, lw=.8, ls=':'); a1.text(2012.1, 95.6, 'meta 95%', fontsize=8, color=TINTA2)
a1.axvline(2022.5, color=CINZA, lw=.8); a1.text(2022.6, 58, 'TABNET → InfoMS', fontsize=8, color=TINTA2)
a1.set_ylim(55, 110); a1.set_ylabel('Cobertura no estado (%)')
a1.set_title('Cobertura da tríplice viral: observada e cenários 2026–2027')
a1.plot([], [], color=CINZA, ls='--', label='cenários (cores à direita)')
a1.plot([], [], marker='o', mfc='white', color=CINZA, ls='none', label='2026 parcial (só referência)')
a1.legend(fontsize=8, frameon=False, loc='lower left')
x = np.arange(len(CORES))
for k, d in enumerate(['D1', 'D2']):
    vals = [proj.loc[c, d] for c in CORES]
    a2.bar(x + (k - .5) * .38, vals, width=.36, color=[CORES[c] for c in CORES], alpha=1 if d == 'D2' else .45,
           label=f'sem {d}')
    for xi, v in zip(x + (k - .5) * .38, vals):
        a2.text(xi, v, f'{v / 1000:.0f} mil', ha='center', va='bottom', fontsize=8)
a2.set_xticks(x, list(CORES)); a2.set_ylabel('Crianças (coortes vacinadas em 2026 e 2027)')
a2.set_title('Crianças sem 1ª dose (claro) e sem 2ª dose (escuro)')
fig.tight_layout(); fig.savefig(OUT / 'projecao.png', dpi=200, bbox_inches='tight')
print('figura: results/projecao/projecao.png')
