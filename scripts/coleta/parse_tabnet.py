import re, sys, csv
out = sys.argv[1]; rows = []
for col, f in zip(sys.argv[2::2], sys.argv[3::2]):
    t = open(f, encoding='latin1').read()
    hdr = re.search(r"data\.addColumn\('string'.*?;(.*?)data\.addRows", t, re.S)
    years = re.findall(r"addColumn\('number',\s*'(\d{4})'", t)
    for m in re.finditer(r'\["(\d{6}) ([^"]*)"\s*,(.*?)\]', t):
        vals = re.findall(r'\{v:\s*([^ ,]+)', m.group(3))
        for y, v in zip(years, vals):
            rows.append((m.group(1), m.group(2), int(y), col, v))
    print(f, 'anos', years, 'municipios', len({r[0] for r in rows if r[3]==col}))
data = {}
for cod, nome, y, col, v in rows:
    data.setdefault((cod, y), {'co_ibge': cod, 'no_municipio_pni': nome, 'ano': y})[col] = v
with open(out, 'w', newline='', encoding='utf-8') as fh:
    cols = ['co_ibge','no_municipio_pni','ano'] + list(sys.argv[2::2])
    w = csv.DictWriter(fh, fieldnames=cols); w.writeheader()
    for k in sorted(data): w.writerow(data[k])
print('linhas', len(data))
