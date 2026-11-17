"""Reconstrói data/processed somente a partir das fontes locais em data/raw (sem rede).

Saídas (todas com chave co_ibge de 6 dígitos):
  notificacoes.csv   uma linha por notificação de residente de SP, arquivos SINAN 2007-2026
  municipio.csv      uma linha por município: nome, regiões, área, REGIC, centroide, distância à capital
  municipio_ano.csv  uma linha por município e ano (2012-2026): casos, internações (SIH), cobertura, população, PIB
  cobertura_estado.csv  cobertura estadual 1995-2026 (TABNET até 2022, InfoMS a partir de 2023)
  vizinhos.json      municípios que fazem fronteira
  malha.json         anéis dos polígonos municipais (para os mapas)
  manifesto_processamento.json  hashes SHA-256 de fontes e derivados, versões e recorte

Fontes já tabulares e limpas (população por sexo e idade pop_ms_sp.csv.gz, cobertura municipal 1995-2011, SIH 1996-1998)
não são copiadas: são lidas direto de data/raw por scripts/base.py.
Uso: python scripts/prepare_data.py
"""
from pathlib import Path
from importlib.metadata import version
import hashlib
import json
import math
import platform
import re

import numpy as np
import openpyxl
import pandas as pd
from shapely.geometry import shape
from shapely.strtree import STRtree

from dbc import ler_dbc

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/processed'
ANOS = list(range(2012, 2027))
CAPITAL = '355030'

# Campos do SINAN exportados. Nomes, endereços e texto livre não são exportados.
COLUNAS = ['arquivo', 'NU_ANO', 'SG_UF', 'SG_UF_NOT', 'ID_MN_RESI', 'CLASSI_FIN', 'CRITERIO',
           'DT_NOTIFIC', 'DT_SIN_PRI', 'DT_INICIO_', 'DT_INVEST', 'DT_ENCERRA', 'DT_INTERNA',
           'DT_OBITO', 'DT_DOSE_N', 'NU_IDADE_N', 'ANO_NASC', 'CS_SEXO', 'CS_RACA', 'CS_ESCOL_N', 'CS_VACINA',
           'CS_VACINAL', 'INT_TEMPO', 'ID_HOSPIT', 'EVOLUCAO', 'ID_TOSSE', 'ID_CORIZA',
           'ID_CONJUNT', 'ID_ARTRALG', 'ID_GANGLIO', 'ID_RETRO', 'TPAUTOCTO', 'NDUPLIC_N']
DATAS = [c for c in COLUNAS if c.startswith('DT_')]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notificacoes():
    """SINAN exantemáticas: todas as notificações de residentes de SP (SG_UF = UF de residência)."""
    partes = []
    for arq in sorted((RAW / 'sinan').glob('EXANBR*.dbc')):
        campos, linhas = ler_dbc(arq)
        d = pd.DataFrame(linhas, columns=campos)
        d = d[d.SG_UF.eq('35')].copy()
        d['arquivo'] = arq.name
        partes.append(d)
        print(f'  {arq.name}: {len(linhas):,} notificações no Brasil, {len(d):,} de residentes de SP')
    n = pd.concat(partes, ignore_index=True)
    for c in DATAS:  # DBF guarda AAAAMMDD; exporta ISO e deixa vazio o que não for data válida
        n[c] = pd.to_datetime(n[c], format='%Y%m%d', errors='coerce').dt.strftime('%Y-%m-%d').fillna('')

    # Data do caso (regra do projeto, não do SINAN): início do exantema; se faltar ou for incompatível com a
    # notificação (mais de 365 dias antes ou mais de 30 dias depois), usa a data dos primeiros sintomas.
    # Motivo: há exantemas digitados com o ano errado (ex.: 2012-08-10 com sintomas em 2019-08-10).
    # Conferência: com a regra, 2019 tem 18.109 casos (RIPSA: 18.113); só com o exantema, 18.025.
    ex, sp, no = (pd.to_datetime(n[c], errors='coerce') for c in ['DT_INICIO_', 'DT_SIN_PRI', 'DT_NOTIFIC'])
    plausivel = lambda d: d.notna() & (no - d).dt.days.between(-30, 365)
    usa_ex = plausivel(ex)
    caso = ex.where(usa_ex, sp.where(plausivel(sp)))
    n['DT_CASO'] = caso.dt.strftime('%Y-%m-%d').fillna('')
    n['ORIGEM_DT_CASO'] = np.select([usa_ex, caso.notna()], ['exantema', 'primeiros sintomas'], '')
    return n


def ripsa_municipios():
    """Nome, região de saúde e RRAS de cada município (RIPSA MRB.1.01). Também devolve os casos por ano,
    usados só para conferir a recontagem a partir do SINAN."""
    cols = ['co_anomes', 'co_ibge', 'co_uf', 'no_municipio', 'co_regiao_saude', 'no_regiao_saude', 'no_macro',
            'sg_categoria', 'vl_indicador_calculado_mun']
    r = pd.read_csv(RAW / 'ripsa008mb.csv.zip', usecols=cols, dtype={'co_ibge': str})
    r = r[r.co_uf.eq(35) & r.sg_categoria.eq('TC')].copy()
    r['ano'] = r.co_anomes // 100
    mun = (r.drop_duplicates('co_ibge').set_index('co_ibge')[['no_municipio', 'co_regiao_saude', 'no_regiao_saude', 'no_macro']]
           .rename(columns={'no_macro': 'rras'}))
    return mun, r.groupby('ano').vl_indicador_calculado_mun.sum()


def regic():
    ws = openpyxl.load_workbook(RAW / 'REGIC2018_Municipios_Hierarquia_e_regiao.xlsx', read_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    rg = pd.DataFrame(rows[1:], columns=rows[0])
    rg = rg[rg.coduf.eq('35')]
    ordem = {'1A': 1, '1B': 2, '1C': 3, '2A': 4, '2B': 5, '2C': 6, '3A': 7, '3B': 8, '4A': 9, '4B': 10, '5': 11}
    hier = rg['Hierarquia 3'].str.split(' ').str[0]
    return pd.DataFrame({'regic_hierarquia': hier.values, 'regic_nivel': hier.map(ordem).values,
                         'regic_grupo': rg['Hierarquia - grupo'].str[0].astype(int).values,
                         'arranjo_populacional': rg['Arranjo Populacional'].values,
                         'regic_regiao_influencia': rg['Região de influência 1'].values},
                        index=pd.Index(rg.codmun.str[:6].values, name='co_ibge'))


def geometria():
    """Malha IBGE (API v3): centroide (ou ponto interno), distância à capital, vizinhos e anéis para mapas."""
    g = json.loads((RAW / 'malha_sp.json').read_text(encoding='utf-8'))
    geoms = {f['properties']['codarea'][:6]: shape(f['geometry']) for f in g['features']}
    cent = {k: (v.centroid if v.centroid.within(v) else v.representative_point()) for k, v in geoms.items()}

    def km(a, b):  # distância de grande círculo (haversine), raio 6371 km
        lon1, lat1, lon2, lat2 = map(math.radians, [a.x, a.y, b.x, b.y])
        h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
        return 2 * 6371 * math.asin(math.sqrt(h))

    keys = sorted(geoms)
    tree = STRtree([geoms[k] for k in keys])
    viz = {k: sorted(keys[j] for j in tree.query(geoms[k]) if keys[j] != k and geoms[k].intersects(geoms[keys[j]]))
           for k in keys}
    geo = pd.DataFrame({'lat': [round(cent[k].y, 5) for k in keys], 'lon': [round(cent[k].x, 5) for k in keys],
                        'dist_capital_km': [round(km(cent[k], cent[CAPITAL]), 1) for k in keys],
                        'n_vizinhos': [len(viz[k]) for k in keys]}, index=pd.Index(keys, name='co_ibge'))
    aneis = {}
    for k in keys:
        polys = getattr(geoms[k], 'geoms', [geoms[k]])
        aneis[k] = [np.round(np.asarray(p.exterior.coords), 5).tolist() for p in polys]
    return geo, viz, aneis


def cobertura_infoms():
    """Planilhas exportadas do painel InfoMS (cobertura por residência), uma por ano. O ano não vem escrito
    no arquivo e foi identificado pelos denominadores (ver FONTES.md). Devolve município x ano com num/den."""
    arquivos = {2023: 'cobertura_infoms_2023.xlsx', 2024: 'cobertura_infoms_2024.xlsx',
                2025: 'cobertura_infoms_2025.xlsx', 2026: 'cobertura_infoms_2026_parcial.xlsx'}
    alvo = {'Tríplice Viral - 1° Dose': 'd1', 'Tríplice Viral - 2° Dose': 'd2'}
    medida = {'Cobertura Vacinal (%)': 'cob', 'Numerador': 'num', 'Denominador': 'den'}
    out = []
    for ano, nome in arquivos.items():
        rows = openpyxl.load_workbook(RAW / nome, read_only=True).worksheets[0].iter_rows(values_only=True)
        vac, med = next(rows), next(rows)
        cols = {(alvo[v], medida[m]): i for i, (v, m) in enumerate(zip(vac, med)) if v in alvo}
        for r in rows:
            if r[2] != 'SP' or not r[5] or r[5] == 'Totais':
                continue
            rec = {'co_ibge': re.match(r'(\d{6}) - ', r[5]).group(1), 'ano': ano}
            for dose in ('d1', 'd2'):
                c = r[cols[(dose, 'cob')]]
                rec[f'cob_triplice_{dose}'] = None if c is None else c * 100
                rec[f'num_{dose}'] = r[cols[(dose, 'num')]]
                rec[f'den_{dose}'] = r[cols[(dose, 'den')]]
            out.append(rec)
    d = pd.DataFrame(out)
    assert d.groupby('ano').size().eq(645).all()
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    # 1) Notificações SINAN
    print('SINAN:')
    n = notificacoes()
    conf = n[n.CLASSI_FIN.eq('1')].copy()
    conf['ano'] = pd.to_datetime(conf.DT_CASO, errors='coerce').dt.year
    assert pd.to_datetime(conf.DT_INICIO_, errors='coerce').dt.year.eq(2019).sum() == 18025,         'O recorte de 2019 mudou: revise a versão das fontes.'
    assert conf.ano.eq(2019).sum() == 18109 and conf.ano.notna().all()
    assert not conf[conf.ano.eq(2019)].drop(columns='arquivo').duplicated().any()
    print('Origem da data do caso (confirmados):', conf.ORIGEM_DT_CASO.value_counts().to_dict())
    n[COLUNAS + ['DT_CASO', 'ORIGEM_DT_CASO']].to_csv(OUT / 'notificacoes.csv', index=False)

    # 2) Municípios (atributos fixos)
    mun, casos_ripsa = ripsa_municipios()
    geo, viz, aneis = geometria()
    censo = pd.read_csv(RAW / 'sidra_censo2022.csv', dtype={'co_ibge': str})
    area = censo[censo.var_id.eq(6318)].set_index('co_ibge').valor.astype(float).rename('area_km2')
    mun = mun.join(area, validate='one_to_one').join(regic(), validate='one_to_one').join(geo, validate='one_to_one')
    assert len(mun) == 645 and mun.drop(columns='arranjo_populacional').notna().all().all()
    mun.sort_index().to_csv(OUT / 'municipio.csv', encoding='utf-8')
    (OUT / 'vizinhos.json').write_text(json.dumps(viz), encoding='utf-8')
    (OUT / 'malha.json').write_text(json.dumps(aneis, separators=(',', ':')), encoding='utf-8')

    # 3) Painel município x ano
    idx = pd.MultiIndex.from_product([sorted(mun.index), ANOS], names=['co_ibge', 'ano'])
    p = pd.DataFrame(index=idx)
    p['casos'] = conf.groupby(['ID_MN_RESI', 'ano']).size().rename_axis(['co_ibge', 'ano']).reindex(idx, fill_value=0)
    fora = conf[conf.ano.isin(ANOS) & ~conf.ID_MN_RESI.isin(mun.index)]
    assert fora.empty, f'{len(fora)} casos com município de residência fora da lista'

    # Internações SUS com diagnóstico principal de sarampo (CID-10 B05), SIH/TABNET, por residência e ano de atendimento.
    # É uma ESTIMATIVA de internações: o diagnóstico hospitalar não passa pela confirmação da vigilância e o SIH só
    # cobre o SUS (2019: 582 no SIH x 2.256 internados no SINAN; 2021-2024: internações sem caso confirmado).
    sih = pd.read_csv(RAW / 'sih_sarampo.csv', dtype={'co_ibge': str}).set_index(['co_ibge', 'ano'])
    p['internacoes_sih'] = sih.internacoes_sarampo.reindex(idx)
    # A consulta TABNET cobriu 2012-2024 e omite linhas e colunas vazias: município ausente = 0 internações;
    # 2017 ausente = nenhuma internação no ano (coerente com zero caso confirmado no SINAN em 2017).
    consultados = p.index.get_level_values('ano') <= 2024
    p.loc[consultados, 'internacoes_sih'] = p.loc[consultados, 'internacoes_sih'].fillna(0)

    tab = pd.read_csv(RAW / 'cobertura_scr_2012_2022.csv', dtype={'co_ibge': str})
    tab['fonte_cobertura'] = 'TABNET PNI'
    inf = cobertura_infoms()
    inf['fonte_cobertura'] = np.where(inf.ano.eq(2026), 'InfoMS (parcial)', 'InfoMS')
    cob = pd.concat([tab, inf])[['co_ibge', 'ano', 'cob_triplice_d1', 'cob_triplice_d2', 'fonte_cobertura']]
    p = p.join(cob.set_index(['co_ibge', 'ano']), validate='one_to_one')

    # População principal: série revisada do Ministério da Saúde (POPSVS, método RIPSA), 2000-2025, uma só fonte
    # para todos os anos, ajustada às projeções estaduais do IBGE (revisão 2024). Ver docs/NT-POPULACAO-RESIDENTE-2000-2024.pdf.
    ms = pd.read_csv(RAW / 'pop_ms_sp.csv.gz', dtype={'co_ibge': str})
    p['populacao'] = ms.groupby(['co_ibge', 'ano'])['pop'].sum().astype(float).reindex(idx)
    # Sensibilidade: números do IBGE publicados na época (estimativas anuais; 2022 = contagem do Censo; 2023 sem dado).
    est = pd.read_csv(RAW / 'sidra_pop_estim.csv', dtype={'co_ibge': str}).set_index(['co_ibge', 'ano']).valor.astype(float)
    c22 = censo[censo.var_id.eq(93)].assign(ano=2022).set_index(['co_ibge', 'ano']).valor.astype(float)
    p['populacao_ibge'] = pd.concat([est, c22]).reindex(idx)

    pib = pd.read_csv(RAW / 'sidra_pib.csv', dtype={'co_ibge': str}).set_index(['co_ibge', 'ano'])
    pib = pib.valor.astype(float).rename('pib_mil_reais').to_frame()
    pib['fonte_pib'] = 'IBGE'
    # PIB municipal de 2024 ainda não publicado (previsão dez/2026). Estimativa:
    # PIB 2023 x 1,034 (crescimento real de SP em 2024, Seade) x 1,0408 (deflator implícito Brasil 2024, SIDRA 1846/6612).
    # Supõe que todos os municípios cresceram como o estado.
    p24 = pib.xs(2023, level='ano').assign(pib_mil_reais=lambda d: d.pib_mil_reais * 1.034 * 1.0408,
                                            fonte_pib='estimado (2023 x 1,034 x 1,0408)')
    p24.index = pd.MultiIndex.from_product([p24.index, [2024]], names=['co_ibge', 'ano'])
    p = p.join(pd.concat([pib, p24]), validate='one_to_one')
    p.to_csv(OUT / 'municipio_ano.csv', encoding='utf-8')

    # 4) Cobertura estadual: TABNET (linha = UF) até 2022; InfoMS = soma de numeradores / soma de denominadores
    uf = pd.read_csv(RAW / 'cobertura_uf_sp_1995_2022.csv').assign(fonte='TABNET PNI')
    s = inf.groupby('ano')[['num_d1', 'den_d1', 'num_d2', 'den_d2']].sum()
    uf2 = pd.DataFrame({'ano': s.index, 'triplice_d1': (s.num_d1 / s.den_d1 * 100).round(2).values,
                        'triplice_d2': (s.num_d2 / s.den_d2 * 100).round(2).values,
                        'fonte': np.where(s.index == 2026, 'InfoMS (parcial)', 'InfoMS')})
    pd.concat([uf, uf2]).to_csv(OUT / 'cobertura_estado.csv', index=False)

    # 5) Conferências
    total = p.casos.groupby('ano').sum()
    print('Casos confirmados por ano (DT_CASO) x RIPSA:')
    print(pd.DataFrame({'SINAN': total, 'RIPSA': casos_ripsa.reindex(total.index)}).T.to_string())
    print(f'Municípios com caso em 2019-2020: {(p.casos.unstack()[[2019, 2020]].sum(axis=1) > 0).sum()}')

    # 6) Manifesto de integridade
    pacotes = ['pandas', 'numpy', 'openpyxl', 'shapely']
    paths = sorted(q for q in RAW.rglob('*') if q.is_file() and q.parent.name not in ('popsvs', 'sih_1996_1998')) + \
        sorted(q for q in OUT.iterdir() if q.name != 'manifesto_processamento.json')
    manifesto = {'python': platform.python_version(), 'pacotes': {k: version(k) for k in pacotes},
                 'recorte': 'Residentes de SP (SG_UF=35), arquivos SINAN 2007-2026; caso = CLASSI_FIN=1; ano = ano de DT_CASO (exantema, ou sintomas se o exantema for implausível)',
                 'casos_2019': int(total[2019]),
                 'arquivos': [{'arquivo': q.relative_to(ROOT).as_posix(), 'sha256': sha(q), 'bytes': q.stat().st_size}
                              for q in paths]}
    (OUT / 'manifesto_processamento.json').write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Concluído:', ', '.join(q.name for q in sorted(OUT.iterdir())))


if __name__ == '__main__':
    main()
