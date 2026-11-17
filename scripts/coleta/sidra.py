import json, sys, csv, urllib.request
tab, per, var, out = sys.argv[1:5]
url = f"https://servicodados.ibge.gov.br/api/v3/agregados/{tab}/periodos/{per}/variaveis/{var}?localidades=N6[N3[35]]"
d = json.load(urllib.request.urlopen(url, timeout=300))
rows = []
for v in d:
    for r in v['resultados']:
        for s in r['series']:
            for ano, val in s['serie'].items():
                rows.append((s['localidade']['id'][:6], s['localidade']['nome'], ano, v['id'], v['variavel'], v.get('unidade'), val))
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['co_ibge','nome','ano','var_id','variavel','unidade','valor']); w.writerows(rows)
print(out, len(rows), 'linhas', sorted({r[3]+':'+r[4][:40] for r in rows}))
