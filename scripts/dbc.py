"""Leitor de arquivos .dbc do DATASUS em Python puro (sem dependencias).

Um .dbc e um .dbf com o corpo comprimido pelo algoritmo PKWare DCL "implode".
Formato: os primeiros H bytes sao o cabecalho do DBF (H esta nos bytes 8-9), seguidos de 4 bytes de CRC
e do corpo comprimido. A descompressao segue o blast.c de Mark Adler (zlib/contrib/blast).

Uso como modulo:
    from dbc import ler_dbc
    campos, linhas = ler_dbc('EXANBR19.dbc')            # linhas: lista de dicts (texto latin-1)
Uso direto:
    py dbc.py ARQUIVO.dbc saida.csv
"""
import csv
import struct
import sys

MAXBITS = 13
LITLEN = [11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8,
          9, 7, 6, 7, 8, 7, 6, 55, 8, 23, 24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5,
          7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
          8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27,
          44, 253, 253, 253, 252, 252, 252, 13, 12, 45, 12, 45, 12, 61, 12, 45,
          44, 173]
LENLEN = [2, 35, 36, 53, 38, 23]
DISTLEN = [2, 20, 53, 230, 247, 151, 248]
BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]


def _tabela(rep, n_esperado):
    """Monta tabela de decodificacao: indice = proximos MAXBITS bits (LSB primeiro) -> (simbolo, comprimento)."""
    comp = []
    for b in rep:
        comp += [b & 15] * ((b >> 4) + 1)
    assert len(comp) == n_esperado, (len(comp), n_esperado)
    ordem = sorted((l, s) for s, l in enumerate(comp) if l)
    tab = [None] * (1 << MAXBITS)
    code, l_ant = 0, ordem[0][0]
    for l, s in ordem:
        code <<= (l - l_ant)
        l_ant = l
        # bits lidos: o 1o bit lido e o bit mais alto do codigo, invertido
        p = 0
        for i in range(l):
            bit = ((code >> (l - 1 - i)) & 1) ^ 1
            p |= bit << i
        for resto in range(1 << (MAXBITS - l)):
            tab[p | (resto << l)] = (s, l)
        code += 1
    return tab


TLIT = _tabela(LITLEN, 256)
TLEN = _tabela(LENLEN, 16)
TDIST = _tabela(DISTLEN, 64)


def blast(dados):
    """Descomprime um fluxo PKWare DCL implode."""
    n = len(dados)
    pos = 0
    buf = 0
    cnt = 0
    out = bytearray()
    mask13 = (1 << MAXBITS) - 1

    def precisa(k):
        nonlocal buf, cnt, pos
        while cnt < k:
            if pos < n:
                buf |= dados[pos] << cnt
                pos += 1
            cnt += 8  # alem do fim: completa com zeros (so pode acontecer no ultimo codigo)

    def bits(k):
        nonlocal buf, cnt
        precisa(k)
        v = buf & ((1 << k) - 1)
        buf >>= k
        cnt -= k
        return v

    def decode(tab):
        nonlocal buf, cnt
        precisa(MAXBITS)
        s, l = tab[buf & mask13]
        buf >>= l
        cnt -= l
        return s

    lit = bits(8)
    dic = bits(8)
    if lit > 1 or not 4 <= dic <= 6:
        raise ValueError('cabecalho blast invalido')
    while True:
        if bits(1):
            sym = decode(TLEN)
            ln = BASE[sym] + bits(EXTRA[sym])
            if ln == 519:
                break
            sh = 2 if ln == 2 else dic
            dist = (decode(TDIST) << sh) + bits(sh) + 1
            ini = len(out) - dist
            if ini < 0:
                raise ValueError('distancia invalida')
            if dist >= ln:
                out += out[ini:ini + ln]
            else:
                for i in range(ln):
                    out.append(out[ini + i])
        else:
            out.append(decode(TLIT) if lit else bits(8))
    return bytes(out)


def dbc_para_dbf(bruto):
    h = struct.unpack('<H', bruto[8:10])[0]
    return bruto[:h] + blast(bruto[h + 4:])


def ler_dbf(dbf, encoding='latin-1'):
    nrec, hlen, rlen = struct.unpack('<IHH', dbf[4:12])
    campos = []
    off = 32
    while dbf[off] != 0x0D:
        nome = dbf[off:off + 11].split(b'\0')[0].decode('ascii')
        tam = dbf[off + 16]
        campos.append((nome, tam))
        off += 32
    linhas = []
    for i in range(nrec):
        r = dbf[hlen + i * rlen: hlen + (i + 1) * rlen]
        if not r or r[0:1] == b'*':
            continue
        p = 1
        d = {}
        for nome, tam in campos:
            d[nome] = r[p:p + tam].decode(encoding).strip()
            p += tam
        linhas.append(d)
    return [c[0] for c in campos], linhas


def ler_dbc(caminho):
    with open(caminho, 'rb') as f:
        return ler_dbf(dbc_para_dbf(f.read()))


if __name__ == '__main__':
    campos, linhas = ler_dbc(sys.argv[1])
    with open(sys.argv[2], 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(linhas)
    print(len(linhas), 'linhas,', len(campos), 'campos')
