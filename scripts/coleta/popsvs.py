"""Baixa a série revisada de população residente do Ministério da Saúde (DATASUS, POPSVS) e extrai SP.

Fonte: ftp://ftp.datasus.gov.br/dissemin/publicos/IBGE/POPSVS/POPSBRaa.zip (aa = 00 a 25), uma tabela por ano com
município (7 dígitos), sexo (1 = masculino, 2 = feminino), idade simples (0 a 80; 80 = 80 anos e mais) e população.
É a mesma série do TabNet "Estudo de Estimativas Populacionais por Município, Idade e Sexo 2000-2025"
(popsvs2024br.def). Metodologia: ftp://ftp.datasus.gov.br/dissemin/publicos/IBGE/doc/NT-POPULACAO-RESIDENTE-2000-2024.pdf
(cópia em docs/). Os zip (3,4 MB cada, Brasil inteiro) ficam em data/raw/popsvs/, fora do git.

Gera data/raw/pop_ms_sp.csv.gz: co_ibge (6 dígitos), ano, sexo (M/F), idade, pop.
Uso (na raiz do projeto): python scripts/coleta/popsvs.py
"""
import struct
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(__file__).resolve().parents[2] / 'data' / 'raw'
PASTA = RAW / 'popsvs'
URL = 'ftp://ftp.datasus.gov.br/dissemin/publicos/IBGE/POPSVS/'
ANOS = range(2000, 2026)


def ler_dbf(arquivo_zip, bloco=50_000):
    """Lê o DBF de largura fixa em blocos (pouca memória) e devolve só os municípios de SP (código 35...)."""
    z = zipfile.ZipFile(arquivo_zip)
    with z.open(z.namelist()[0]) as f:
        cab = f.read(32)
        n = struct.unpack('<I', cab[4:8])[0]
        h, l = struct.unpack('<HH', cab[8:12])
        cab += f.read(h - 32)
        campos, off = [('apagado', 1)], 32
        while cab[off] != 0x0D:
            campos.append((cab[off:off + 11].split(b'\0')[0].decode().upper(), cab[off + 16]))  # 2025 vem com nomes minúsculos
            off += 32
        assert sum(t for _, t in campos) == l
        tipo = np.dtype([(c, f'S{t}') for c, t in campos])
        partes, lidos = [], 0
        while lidos < n:
            k = min(bloco, n - lidos)
            a = np.frombuffer(f.read(k * l), dtype=tipo, count=k)
            partes.append(a[(a['apagado'] != b'*') & np.char.startswith(a['COD_MUN'], b'35')].copy())
            lidos += k
    a = np.concatenate(partes)
    return pd.DataFrame({c: np.char.strip(a[c].astype(str)) for c, _ in campos[1:]})


def main():
    PASTA.mkdir(exist_ok=True)
    partes = []
    for ano in ANOS:
        arq = PASTA / f'POPSBR{ano % 100:02d}.zip'
        if not arq.exists():
            arq.write_bytes(urllib.request.urlopen(URL + arq.name, timeout=600).read())
        d = ler_dbf(arq)
        d = d[d.COD_MUN.str.startswith('35')]
        d = pd.DataFrame({'co_ibge': d.COD_MUN.str[:6], 'ano': d.ANO.astype(int),
                          'sexo': d.SEXO.map({'1': 'M', '2': 'F'}), 'idade': d.IDADE.astype(int),
                          'pop': d.POP.astype(int)})
        assert d.co_ibge.nunique() == 645 and d.sexo.notna().all() and d.ano.eq(ano).all()
        partes.append(d)
        print(ano, f'{d["pop"].sum():,}')
    out = pd.concat(partes).sort_values(['co_ibge', 'ano', 'sexo', 'idade'])
    assert not out.duplicated(['co_ibge', 'ano', 'sexo', 'idade']).any()
    out.to_csv(RAW / 'pop_ms_sp.csv.gz', index=False)
    print('pop_ms_sp.csv.gz', len(out), 'linhas; idades', out.idade.min(), '-', out.idade.max())


if __name__ == '__main__':
    main()
