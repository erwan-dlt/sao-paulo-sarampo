"""Leitura única dos dados processados e das variáveis derivadas usadas em todas as análises.

Decisões do projeto (valem para o notebook, os modelos e o clustering):
  * caso = notificação confirmada (CLASSI_FIN = 1) de residente de SP; ano do caso = ano de DT_CASO
    (início do exantema; primeiros sintomas se o exantema for implausível; ver prepare_data.py). 2019 = 18.109 casos.
  * cobertura "antes do surto" = média municipal de 2016 a 2018 (D1 e D2); diferença 2018 - 2016.
  * validação espacial principal = deixar uma RRAS de fora por vez (19 regiões oficiais).
  * população = série revisada do Ministério da Saúde (POPSVS); denominador de 2019 = população de 2019.
"""
from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans

ROOT = Path(__file__).resolve().parents[1]
PRO = ROOT / 'data' / 'processed'
RAW = ROOT / 'data' / 'raw'
ANO_SURTO = 2019
JANELA_COB = (2016, 2018)
CAPITAL = '355030'
# Faixas etárias da população (rótulo: idade mínima, idade máxima); 80 = 80 anos e mais na série do Ministério.
FAIXAS = {'<1 Ano': (0, 0), '1-4': (1, 4), '5-9': (5, 9), '10-14': (10, 14), '15-19': (15, 19), '20-29': (20, 29),
          '30-39': (30, 39), '40-49': (40, 49), '50-59': (50, 59), '60-64': (60, 64), '65-69': (65, 69),
          '70-79': (70, 79), '80 e +': (80, 80)}


def municipios():
    return pd.read_csv(PRO / 'municipio.csv', dtype={'co_ibge': str, 'co_regiao_saude': str}).set_index('co_ibge')


def painel():
    """Município x ano (2012-2026) com os atributos fixos do município."""
    p = pd.read_csv(PRO / 'municipio_ano.csv', dtype={'co_ibge': str})
    return p.join(municipios(), on='co_ibge')


def idade_anos(nu_idade_n):
    """NU_IDADE_N do SINAN: milhar = unidade (1 hora, 2 dia, 3 mês, 4 ano), resto = quantidade. Fora do domínio = NaN."""
    cod = pd.to_numeric(nu_idade_n, errors='coerce')
    u, v = cod // 1000, cod % 1000
    return pd.Series(np.select([u.eq(1) & v.between(0, 23), u.eq(2) & v.between(0, 30), u.eq(3) & v.between(0, 11),
                                u.eq(4) & v.between(0, 120)], [v / 24 / 365.25, v / 365.25, v / 12, v], np.nan),
                     index=cod.index)


def notificacoes(confirmados=True):
    """Notificações de residentes de SP (SINAN 2007-2026). Acrescenta ano do caso, idade em anos e ano de nascimento."""
    n = pd.read_csv(PRO / 'notificacoes.csv', dtype=str, keep_default_na=False)
    if confirmados:
        n = n[n.CLASSI_FIN.eq('1')].copy()
    n['ano'] = pd.to_datetime(n.DT_CASO, errors='coerce').dt.year.astype('Int64')
    n['idade'] = idade_anos(n.NU_IDADE_N)
    n['ano_nasc'] = pd.to_numeric(n.ANO_NASC, errors='coerce')
    return n


def pop_idade(ano, sexo=None):
    """População (série do Ministério) por município e idade simples (0 a 80 = 80 e mais). sexo: None, 'M' ou 'F'."""
    p = pd.read_csv(RAW / 'pop_ms_sp.csv.gz', dtype={'co_ibge': str})
    p = p[p.ano.eq(ano) & (p.sexo.eq(sexo) if sexo else True)]
    return p.pivot_table(index='co_ibge', columns='idade', values='pop', aggfunc='sum')


def pop_faixas(ano, sexo=None):
    p = pop_idade(ano, sexo)
    return pd.DataFrame({f: p.loc[:, lo:hi].sum(axis=1) for f, (lo, hi) in FAIXAS.items()})


def cobertura_janela(pa, tratamento='original'):
    """Médias e diferenças da cobertura D1/D2 na janela pré-surto. tratamento: 'original', 'limitada' (teto 100)
    ou 'ausente' (valores > 100 viram ausentes). A fração > 100 é sempre calculada nos valores originais."""
    a0, a1 = JANELA_COB
    w = pa[pa.ano.between(a0, a1)].pivot(index='co_ibge', columns='ano', values=['cob_triplice_d1', 'cob_triplice_d2'])
    out = pd.DataFrame(index=w.index)
    out['fracao_cob_acima100'] = (w > 100).mean(axis=1)
    if tratamento == 'limitada':
        w = w.clip(upper=100)
    elif tratamento == 'ausente':
        w = w.where(w <= 100)
    for d in ('d1', 'd2'):
        v = w[f'cob_triplice_{d}']
        out[f'{d}_media'] = v.mean(axis=1)
        out[f'{d}_delta'] = v[a1] - v[a0]
    return out


def base_municipal(tratamento='original'):
    """Uma linha por município (645), com desfechos do surto e todas as variáveis usadas nos modelos."""
    m = municipios()
    pa = pd.read_csv(PRO / 'municipio_ano.csv', dtype={'co_ibge': str})
    n = notificacoes()
    surto = n[n.ano.isin([ANO_SURTO, ANO_SURTO + 1])]
    m['casos'] = surto[surto.ano.eq(ANO_SURTO)].ID_MN_RESI.value_counts().reindex(m.index, fill_value=0)
    m['casos_2019_20'] = surto.ID_MN_RESI.value_counts().reindex(m.index, fill_value=0)
    m['autoctones_2019_20'] = surto[surto.TPAUTOCTO.eq('1')].ID_MN_RESI.value_counts().reindex(m.index, fill_value=0)

    p19 = pa[pa.ano.eq(ANO_SURTO)].set_index('co_ibge')
    m['populacao'] = p19.populacao
    m['incidencia'] = m.casos / m.populacao * 1e5
    m['incidencia_2019_20'] = m.casos_2019_20 / m.populacao * 1e5
    fx = pop_faixas(ANO_SURTO)
    for nome, cols in [('frac_0a4', ['<1 Ano', '1-4']), ('frac_5a19', ['5-9', '10-14', '15-19']),
                       ('frac_20a39', ['20-29', '30-39']), ('frac_60mais', ['60-64', '65-69', '70-79', '80 e +'])]:
        m[nome] = fx[cols].sum(axis=1) / m.populacao
    m['log_pop'] = np.log(m.populacao)
    m['log_densidade'] = np.log(m.populacao / m.area_km2)
    a0, a1 = JANELA_COB
    j = pa[pa.ano.between(a0, a1)].assign(pib_pc=lambda d: d.pib_mil_reais * 1000 / d.populacao)
    m['log_pib'] = np.log(j.groupby('co_ibge').pib_pc.mean())
    m['em_arranjo'] = m.arranjo_populacional.notna().astype(int)
    m = m.join(cobertura_janela(pa, tratamento))

    # Partições alternativas (sensibilidade): 5 blocos k-means das coordenadas e 5 faixas de longitude.
    xy = np.column_stack([m.lon * np.cos(np.deg2rad(m.lat.mean())), m.lat])
    lab = KMeans(n_clusters=5, n_init=20, random_state=42).fit_predict(xy)
    ordem = np.argsort([m.lon[lab == i].mean() for i in range(5)])
    m['bloco'] = [dict(zip(ordem, range(1, 6)))[i] for i in lab]
    m['faixa_longitude'] = pd.qcut(m.lon.rank(method='first'), 5, labels=False).astype(int) + 1

    assert len(m) == 645 and m.index.is_unique and m.casos.sum() == 18109
    assert m[['populacao', 'log_pib', 'frac_0a4']].notna().all().all()
    if tratamento != 'ausente':  # com > 100 como ausente, municípios sem nenhum ano válido ficam vazios
        assert m[['d1_media', 'd2_media', 'd1_delta', 'd2_delta']].notna().all().all()
    return m


def vizinhos():
    return json.loads((PRO / 'vizinhos.json').read_text(encoding='utf-8'))


# ---------------------------------------------------------------- utilitários dos modelos de município
def cv_rras(df):
    """Partições 'deixar uma RRAS de fora' (validação espacial principal do projeto)."""
    from sklearn.model_selection import LeaveOneGroupOut
    return list(LeaveOneGroupOut().split(df, groups=df.rras))


def auc_espacial(df, cols, y, modelo=None):
    """AUC das previsões fora da amostra (uma RRAS de fora por vez) de uma regressão logística padronizada."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    modelo = modelo or make_pipeline(StandardScaler(), LogisticRegression(max_iter=3000))
    pr = cross_val_predict(modelo, df[cols].values, y, cv=cv_rras(df), method='predict_proba')[:, 1]
    return roc_auc_score(y, pr)


def or_ajustado(df, cols, y):
    """Regressão logística (Newton-Raphson) com variáveis padronizadas. Devolve, para cada variável,
    razão de chances por 1 desvio-padrão, IC 95% e p-valor (Wald)."""
    from scipy import stats
    X = df[cols].to_numpy(float)
    X = np.column_stack([np.ones(len(X)), (X - X.mean(0)) / X.std(0)])
    b = np.zeros(X.shape[1])
    for _ in range(100):
        pr = 1 / (1 + np.exp(-X @ b))
        H = X.T @ (X * (pr * (1 - pr))[:, None])
        passo = np.linalg.solve(H, X.T @ (np.asarray(y) - pr))
        b += passo
        if abs(passo).max() < 1e-10:
            break
    se = np.sqrt(np.diag(np.linalg.inv(H)))
    return pd.DataFrame({'OR': np.exp(b[1:]), 'IC_inf': np.exp(b[1:] - 1.96 * se[1:]),
                         'IC_sup': np.exp(b[1:] + 1.96 * se[1:]), 'p': 2 * stats.norm.sf(abs(b[1:] / se[1:]))}, index=cols)


ESTRUTURA = ['log_pop', 'log_densidade', 'dist_capital_km', 'regic_nivel', 'em_arranjo', 'log_pib']
COBERTURA = ['d1_media', 'd2_media']
