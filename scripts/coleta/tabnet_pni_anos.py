# Igual a tabnet_pni.py, com o intervalo de anos como argumento: py tabnet_pni_anos.py form.html saida.html "<incremento>" ano_ini ano_fim
import re, sys, urllib.parse, urllib.request
src, out, incr, a0, a1 = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
t = open(src, encoding='latin1').read()
sel = {}
for m in re.finditer(r'<select[^>]*name="([^"]+)"[^>]*>(.*?)</select>', t, re.S|re.I):
    sel[m.group(1)] = re.findall(r'<option[^>]*value="([^"]*)"', m.group(2), re.I)
pick = lambda name, start: [v for v in sel[name] if v.startswith(start)]
data = [('Linha', pick('Linha','Munic')[0]), ('Coluna', pick('Coluna','Ano')[0])]
data += [('Incremento', v) for v in pick('Incremento', incr)]
data += [('PAno', f'{y}|{y}|4') for y in range(a0, a1 + 1)]
for name, opts in sel.items():
    if name.startswith('S'):
        if name == 'SUnidade da Federa\xe7\xe3o': data.append((name, pick(name, 'S\xe3o Paulo')[0]))
        else: data.append((name, 'TODAS_AS_CATEGORIAS__'))
data += [('nomedef','bd_pni/cpnibr.def'), ('grafico','')]
body = urllib.parse.urlencode(data, encoding='latin1').encode()
req = urllib.request.Request('https://tabnet.datasus.gov.br/cgi/webtabx.exe?bd_pni/cpnibr.def', data=body,
      headers={'Content-Type':'application/x-www-form-urlencoded','User-Agent':'Mozilla/5.0','Referer':'https://tabnet.datasus.gov.br/cgi/dhdat.exe?bd_pni/cpnibr.def'})
r = urllib.request.urlopen(req, timeout=300).read()
open(out,'wb').write(r); print(len(r), 'bytes; incremento =', [v[:25] for v in pick('Incremento', incr)])
