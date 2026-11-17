"""Internacoes SUS com diagnostico principal de sarampo (CID-9 055 ate 1997, CID-10 B05 em 1998) em SP, 1996-1998, por municipio de residencia.

Uso (na raiz do projeto):  python scripts/coleta/sih_sarampo_1996_1998.py  [pasta_dbc]
Baixa (se faltar) ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/199201_200712/Dados/RDSPaamm.dbc
para data/raw/sih_1996_1998/ (ou pasta_dbc; não versionada, 284 MB) e grava em data/raw/:
  sih_sarampo_1996_1998_mes.csv        - internacoes por mes de competencia e codigo
  sih_sarampo_1996_1998_municipio.csv  - internacoes por municipio de residencia e ano de internacao
O SIH registra a internacao no mes de competencia (processamento); por isso le ate 1998-12.
"""
import collections
import csv
import struct
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dbc import dbc_para_dbf  # noqa: E402

RAW = Path(__file__).resolve().parents[2] / 'data' / 'raw'
PASTA = Path(sys.argv[1]) if len(sys.argv) > 1 else RAW / 'sih_1996_1998'
PASTA.mkdir(parents=True, exist_ok=True)
URL = 'ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/199201_200712/Dados/'

por_mes = collections.Counter()
por_mun = collections.Counter()
proc = collections.Counter()
idade = collections.Counter()
for ano in ['96', '97', '98']:
    for mes in range(1, 13):
        nome = f'RDSP{ano}{mes:02d}.dbc'
        arq = PASTA / nome
        if not arq.exists():
            for tentativa in range(3):
                try:
                    urllib.request.urlretrieve(URL + nome, arq)
                    break
                except Exception as e:  # FTP do DATASUS cai as vezes
                    print('falha', nome, e)
        dbf = dbc_para_dbf(arq.read_bytes())
        nrec, hlen, rlen = struct.unpack('<IHH', dbf[4:12])
        off, p, pos = 32, 1, {}
        while dbf[off] != 0x0D:
            n = dbf[off:off + 11].split(b'\0')[0].decode()
            ln = dbf[off + 16]
            pos[n] = (p, p + ln)
            p += ln
            off += 32
        dg0, dg1 = pos['DIAG_PRINC']
        n_mes = 0
        for i in range(nrec):
            r = dbf[hlen + i * rlen: hlen + (i + 1) * rlen]
            dg = r[dg0:dg1]
            # ate 1997: CID-9 com zero a esquerda e digito verificador (0 + 055x + DV); 1998: CID-10 (B05x)
            if not (dg.startswith(b'0055') or dg.startswith(b'B05')):
                continue
            f = lambda k: r[pos[k][0]:pos[k][1]].decode('latin1').strip()
            dt = f('DT_INTER')
            por_mes[(f'19{ano}-{mes:02d}', f('DIAG_PRINC'))] += 1
            ano_int = dt[:4] if dt.startswith('19') and len(dt) == 8 else '19' + dt[:2]  # 1996-97: AAMMDD; 1998: AAAAMMDD
            por_mun[(f('MUNIC_RES'), ano_int)] += 1
            proc[f('PROC_REA')] += 1
            idade[(f('COD_IDADE'), f('IDADE'))] += 1
            n_mes += 1
        print(nome, nrec, 'internacoes;', n_mes, 'de sarampo', flush=True)

with open(RAW / 'sih_sarampo_1996_1998_mes.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['competencia', 'diag_princ', 'internacoes'])
    for (m, d), n in sorted(por_mes.items()):
        w.writerow([m, d, n])
with open(RAW / 'sih_sarampo_1996_1998_municipio.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh)
    w.writerow(['co_ibge', 'ano_internacao', 'internacoes'])
    for (c, a), n in sorted(por_mun.items()):
        w.writerow([c, a, n])
print('procedimentos mais frequentes:', proc.most_common(8))
print('idade (cod, valor) mais frequentes:', idade.most_common(10))
