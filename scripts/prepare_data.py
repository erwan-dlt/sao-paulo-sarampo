"""Reconstrói data/processed somente a partir das fontes locais em data/raw."""
from pathlib import Path
import hashlib
import json
import tempfile
import platform
from importlib.metadata import version

import pandas as pd
from dbctodbf import DBCDecompress
from dbfread import DBF
from leitura_fontes import tabnet, municipios, malha, GRUPOS

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/processed'
COLUNAS = ['arquivo','SG_UF','SG_UF_NOT','ID_MN_RESI','CLASSI_FIN','CRITERIO',
 'DT_NOTIFIC','DT_SIN_PRI','DT_INICIO_','DT_INVEST','DT_ENCERRA','DT_INTERNA',
 'DT_OBITO','DT_DOSE_N','NU_IDADE_N','CS_SEXO','CS_RACA','CS_ESCOL_N','CS_VACINA',
 'CS_VACINAL','INT_TEMPO','ID_HOSPIT','EVOLUCAO','ID_TOSSE','ID_CORIZA',
 'ID_CONJUNT','ID_ARTRALG','ID_GANGLIO','ID_RETRO','TPAUTOCTO','NDUPLIC_N']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fontes = []
    frames = []
    with tempfile.TemporaryDirectory() as tmp:
        for nome in ['EXANBR19.dbc', 'EXANBR20.dbc']:
            destino = Path(tmp) / nome.replace('.dbc', '.dbf')
            destino.write_bytes(DBCDecompress().decompress((RAW / nome).read_bytes()))
            df = pd.DataFrame(iter(DBF(str(destino), encoding='latin1', char_decode_errors='replace')))
            fontes.append({'arquivo':'data/raw/'+nome,'sha256':sha(RAW/nome),'linhas':len(df),'colunas':len(df.columns)})
            df['arquivo'] = nome
            frames.append(df)
            print(f'{nome}: {len(df):,} registros')
    base = pd.concat(frames, ignore_index=True)
    dates = pd.to_datetime(base.DT_INICIO_, errors='coerce')
    cohort = base[base.SG_UF.eq('35') & base.CLASSI_FIN.eq('1') & dates.dt.year.eq(2019)]
    assert len(cohort) == 18025, 'O recorte mudou: revise a versão das fontes.'
    assert cohort.drop(columns='arquivo').duplicated().sum() == 0
    base[COLUNAS].to_csv(OUT/'notificacoes.csv', index=False)
    # Os códigos municipais SINAN usam os seis primeiros dígitos do código IBGE.
    meta, polys = malha()
    pop = municipios(tabnet('pop_idade'))
    sex = municipios(tabnet('pop_sexo'))
    mun = meta[['NM_MUN','area_km2']].rename(columns={'NM_MUN':'municipio'})
    mun = mun.join(pop[['Total']].rename(columns={'Total':'populacao'}), validate='one_to_one')
    alt = pd.read_excel(RAW/'pop2019.xls',sheet_name='Municípios',header=1,dtype=str)
    alt = alt[alt.UF.eq('SP')].copy()
    alt['codigo'] = (alt['COD. UF'].str.zfill(2)+alt['COD. MUNIC'].str.zfill(5)).str[:6]
    alt['pop_original'] = alt['POPULAÇÃO ESTIMADA'].str.replace(r'\s*\(.*','',regex=True).str.replace('.','',regex=False).astype(float)
    mun = mun.join(alt.set_index('codigo')[['pop_original']],validate='one_to_one')
    assert len(mun)==645 and mun.notna().all().all()
    mun.to_csv(OUT/'municipios.csv')
    ages={c:0 if 'Menos' in c else int(c.split()[0]) for c in pop.columns if c not in ['Total','territorio']}
    pa=pd.DataFrame({g:pop[[c for c,a in ages.items() if lo<=a<=hi]].sum(axis=1) for g,(lo,hi) in GRUPOS.items()})
    assert pa.sum(axis=1).equals(pop.Total)
    pa.to_csv(OUT/'pop_idade.csv')
    sex.to_csv(OUT/'pop_sexo.csv')
    for origem,destino in [('mmr_2016_2018.csv','mmr.csv'),('gdp_per_capita_2016.csv','pib.csv')]:
        (OUT/destino).write_bytes((RAW/origem).read_bytes())
        fontes.append({'arquivo':'data/raw/'+origem,'sha256':sha(RAW/origem),'linhas':len(pd.read_csv(RAW/origem))})
    vac=pd.read_csv(OUT/'mmr.csv')
    assert len(vac)==3870 and not vac.duplicated(['municipality_ibge','year','dose']).any()
    (OUT/'malha.json').write_text(json.dumps({k:[p.tolist() for p in parts] for k,parts in polys.items()}),encoding='utf-8')
    (OUT/'fontes.json').write_text(json.dumps(fontes,ensure_ascii=False,indent=2),encoding='utf-8')
    paths=sorted(RAW.iterdir())+sorted(p for p in OUT.iterdir() if p.name!='manifesto_processamento.json')
    manifest={'python':platform.python_version(),
        'pacotes':{p:version(p) for p in ['pandas','numpy','scipy','dbfread','dbc-to-dbf','xlrd']},
        'recorte':'SG_UF=35, CLASSI_FIN=1, ano(DT_INICIO_)=2019; arquivos 2019 e 2020',
        'casos':len(cohort),'arquivos':[{'arquivo':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in paths if p.is_file()]}
    (OUT/'manifesto_processamento.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Concluído: 18.025 casos no recorte, 645 municípios; dados em data/processed.')

if __name__=='__main__':
    main()
