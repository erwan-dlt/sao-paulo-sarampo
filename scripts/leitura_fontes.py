"""Preparação auditável dos dados públicos. Nenhuma observação é simulada."""
from pathlib import Path
import io, re, html, struct, zipfile, json
import numpy as np
import pandas as pd
from scipy.stats import chi2
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
PRO=ROOT/'data/processed'
MESES=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
GRUPOS={'<1 Ano':(0,0),'1-4':(1,4),'5-9':(5,9),'10-14':(10,14),'15-19':(15,19),'20-29':(20,29),'30-39':(30,39),'40-49':(40,49),'50-59':(50,59),'60-64':(60,64),'65-69':(65,69),'70-79':(70,79),'80 e +':(80,80)}
def tabnet(nome):
    s=(RAW/(nome+'.html')).read_bytes().decode('latin1')
    linhas=[html.unescape(x.strip()) for x in s.splitlines() if x.strip().startswith('"')]
    d=pd.read_csv(io.StringIO('\n'.join(linhas)),sep=';',dtype=str)
    d=d.rename(columns={d.columns[0]:'territorio'})
    for c in d.columns[1:]:
        d[c]=pd.to_numeric(d[c].replace('-', '0'),errors='raise')
    assert (d.iloc[:,1:]>=0).all().all()
    assert np.array_equal(d.drop(columns=['territorio','Total']).sum(axis=1),d.Total)
    return d

def municipios(d):
    d=d[d.territorio.str.match(r'^35\d{4} ')].copy()
    d['codigo']=d.territorio.str[:6]
    assert len(d)==645 and d.codigo.is_unique
    return d.set_index('codigo')

def malha():
    z=zipfile.ZipFile(RAW/'sp_municipios.zip')
    b=z.read('SP_Municipios_2019.dbf');n=struct.unpack_from('<I',b,4)[0];h,l=struct.unpack_from('<HH',b,8)
    campos=[(b[i:i+11].split(b'\0')[0].decode(),b[i+16]) for i in range(32,h-1,32)]
    rows=[]
    for j in range(n):
        r=b[h+j*l:h+(j+1)*l];o=1;v={}
        for nome,tam in campos:v[nome]=r[o:o+tam].decode('utf8',errors='replace').strip();o+=tam
        rows.append(v)
    s=z.read('SP_Municipios_2019.shp');o=100;geoms=[]
    while o<len(s):
        rec,words=struct.unpack_from('>II',s,o);o+=8;c=s[o:o+words*2];o+=words*2
        tipo=struct.unpack_from('<I',c)[0];assert tipo==5, tipo
        nparts,npoints=struct.unpack_from('<II',c,36)
        parts=list(struct.unpack_from('<'+'I'*nparts,c,44))+[npoints]
        points=np.frombuffer(c,dtype='<f8',offset=44+4*nparts,count=npoints*2).reshape(-1,2)
        geoms.append([points[parts[k]:parts[k+1]].copy() for k in range(nparts)])
    assert len(rows)==len(geoms)==645
    meta=pd.DataFrame(rows);meta['codigo']=meta.CD_MUN.str[:6];meta['area_km2']=pd.to_numeric(meta.AREA_KM2)
    assert meta.codigo.is_unique
    return meta.set_index('codigo'),dict(zip(meta.codigo,geoms))

def poisson_interval(casos,pop):
    k=np.asarray(casos,float);p=np.asarray(pop,float)
    low=np.where(k>0,chi2.ppf(.025,2*k)/2,0)/p*1e5
    high=chi2.ppf(.975,2*(k+1))/2/p*1e5
    return low,high

