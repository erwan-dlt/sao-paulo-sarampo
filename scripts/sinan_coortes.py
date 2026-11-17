"""Casos confirmados do surto (2019-2020) por idade e situação vacinal registrada, e teste da cobertura histórica
das coortes que adoeceram (municipal, 1995-2004) contra o surto por município.

Uso: python scripts/sinan_coortes.py   ->  results/geracoes/sinan_coortes.txt
Entradas: data/processed/notificacoes.csv (via base.py); data/raw/cobertura_hist_1995_2011.csv (TABNET PNI,
vacina sarampo monovalente 1995-2003 e tríplice viral D1 2000-2011, por município).
"""
import numpy as np
import pandas as pd

import base

OUT = base.ROOT / 'results' / 'geracoes'
OUT.mkdir(parents=True, exist_ok=True)
LOG = []


def log(x=''):
    print(x)
    LOG.append(str(x))


c = base.notificacoes()
c = c[c.ano.isin([2019, 2020])].copy()
FAIXAS = [-1, 0.999, 4, 9, 14, 19, 24, 29, 39, 49, 200]
NOMES = ['<1', '1-4', '5-9', '10-14', '15-19', '20-24', '25-29', '30-39', '40-49', '50+']
c['faixa'] = pd.cut(c.idade, FAIXAS, labels=NOMES)
log(f'Casos confirmados de residentes de SP, ano do caso 2019-2020: {len(c)} ' + str(c.ano.value_counts().sort_index().to_dict()))
t = c.faixa.value_counts().reindex(NOMES)
vac = pd.crosstab(c.faixa, c.CS_VACINA.replace('', '9'), normalize='index').reindex(NOMES) * 100
tab = pd.DataFrame({'casos': t, 'pct': (t / t.sum() * 100).round(1),
                    'vacinado_%': vac.get('1', 0).round(0), 'nao_vacinado_%': vac.get('2', 0).round(0),
                    'ignorado_%': vac.get('9', 0).round(0)})
log('\nCasos por faixa etaria e situacao vacinal registrada (CS_VACINA):')
log(tab.to_string())
log('TPAUTOCTO (1 = autoctone do municipio de residencia, 2 = nao, 3 = indeterminado): '
    + str(c.TPAUTOCTO.value_counts().to_dict()))

# ---------- cobertura histórica municipal das coortes ----------
h = pd.read_csv(base.RAW / 'cobertura_hist_1995_2011.csv', dtype={'co_ibge': str})
h['dose1'] = np.where(h.ano <= 1999, h.sarampo, h.d1)  # 1995-99 monovalente; 2000+ tríplice D1
pv = h.pivot(index='co_ibge', columns='ano', values='dose1')
log('\nCobertura historica (1a dose), mediana municipal: ' + str(pv.median().round(1).to_dict()))
log(f'Municipio-anos 1995-2004 com cobertura > 100%: {(pv.loc[:, 1995:2004] > 100).mean().mean():.0%}')

m = base.base_municipal()
c['jovem'] = c.idade.between(15, 39)
m['jov'] = c[c.jovem].ID_MN_RESI.value_counts().reindex(m.index, fill_value=0)
m['cob_coorte_95_04'] = pv.loc[:, 1995:2004].mean(1)
m['cob_coorte_95_99'] = pv.loc[:, 1995:1999].mean(1)
m['cob_coorte_00_04'] = pv.loc[:, 2000:2004].mean(1)
AJUSTE = ['log_pop', 'dist_capital_km', 'log_pib', 'em_arranjo']
log('\nRazao de chances por 1 DP de cobertura, ajustada por log pop, distancia, log PIB pc e arranjo:')
for alvo, y in {'>=2 casos autoctones': m.autoctones_2019_20 >= 2, '>=1 caso de 15-39 anos': m.jov >= 1,
                '>=2 casos de 15-39 anos': m.jov >= 2}.items():
    y = y.astype(int).values
    log(f'  {alvo} ({y.sum()} municipios):')
    for col in ['d1_media', 'cob_coorte_95_04', 'cob_coorte_95_99', 'cob_coorte_00_04']:
        r = base.or_ajustado(m, [col] + AJUSTE, y).loc[col]
        log(f'    {col:18s} {r.OR:.2f} ({r.IC_inf:.2f}-{r.IC_sup:.2f}) p={r.p:.3f}')
(OUT / 'sinan_coortes.txt').write_text('\n'.join(LOG), encoding='utf-8')
