import re, sys, csv, urllib.parse, urllib.request

src, out = sys.argv[1], sys.argv[2]
t = open(src, encoding='latin1').read()
sel = {}
for m in re.finditer(r'<select[^>]*name="?([^" >]+)"?[^>]*>(.*?)</select>', t, re.S | re.I):
    sel[m.group(1)] = re.findall(r'<option[^>]*value="([^"]*)"', m.group(2), re.I)

arquivos = [a for a in sel['Arquivos'] if '1201' <= a[4:8] <= '2607']
data = [('Linha', 'Munic\xedpio'), ('Coluna', 'Ano_atendimento'), ('Incremento', 'Interna\xe7\xf5es')]
data += [('Arquivos', a) for a in arquivos]
for name in sel:
    if name.startswith('S'):
        data.append((name, '47' if name == 'SLista_Morb__CID-10' else 'TODAS_AS_CATEGORIAS__'))
data += [('formato', 'prn'), ('mostre', 'Mostra')]
body = urllib.parse.urlencode(data, encoding='latin1').encode()
req = urllib.request.Request('https://tabnet.datasus.gov.br/cgi/tabcgi.exe?sih/cnv/nrsp.def', data=body,
                             headers={'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req, timeout=500).read().decode('latin1')
open(out + '.html', 'w', encoding='utf-8').write(html)
pre = re.search(r'<PRE>(.*?)</PRE>', html, re.S | re.I)
if not pre:
    print('sem bloco PRE; trecho:', re.sub(r'<[^>]+>', ' ', html)[:800]); sys.exit(1)
lines = [l for l in pre.group(1).strip().splitlines() if l.strip()]
hdr = [h.strip('"') for h in lines[0].split(';')]
print('cabecalho:', hdr, '| arquivos:', len(arquivos))
rows = []
for l in lines[1:]:
    p = [x.strip('"') for x in l.split(';')]
    m = re.match(r'(\d{6}) ', p[0])
    if not m:
        continue
    for ano, v in zip(hdr[1:], p[1:]):
        if ano.isdigit():
            rows.append((m.group(1), int(ano), int(v) if v not in ('-', '') else 0))
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['co_ibge', 'ano', 'internacoes_sarampo'])
    w.writerows(rows)
print('linhas', len(rows), 'municipios', len({r[0] for r in rows}))
tot = {}
for _, a, v in rows:
    tot[a] = tot.get(a, 0) + v
print('internacoes por ano:', dict(sorted(tot.items())))
