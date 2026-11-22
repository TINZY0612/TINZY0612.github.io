"""Preserve public factor inputs and current fee-policy evidence."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw';RAW.mkdir(exist_ok=True)
MAN=ROOT/'source_manifest.json'
records=json.loads(MAN.read_text()) if MAN.exists() else []
SOURCES=[
 ('total_stablecoin_history','https://stablecoins.llama.fi/stablecoincharts/all'),
 ('btc_fred_csv','https://fred.stlouisfed.org/graph/graph.csv?id=CBBTCUSD&cosd=2024-12-01&coed=2026-11-20'),
 ('redemption_policy','https://help.circle.com/support/en/usdc-eurc-redemption-structure?id=kb_article_view&sysparm_article=KB0010644&sysparm_language=en'),
 ('circle_economics','https://www.circle.com/blog/the-economics-of-usdc-and-why-our-partners-win'),
 ('usyc_fees','https://www.circle.com/usyc'),
]
def fetch(s):
    name,url=s;old=next((r for r in records if r['name']==name and r['status']=='received'),None)
    if old:return old
    rec={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'CircleAcademicResearch/0.5 public research'})
        with urllib.request.urlopen(req,timeout=30) as response:
            data=response.read();ct=response.headers.get('Content-Type','');rec.update(final_url=response.url,http_status=response.status,content_type=ct)
        ext='json' if 'json' in ct else 'csv' if 'csv' in ct or name.endswith('_csv') else 'html'
        p=RAW/(name+'.'+ext);p.write_bytes(data)
        rec.update(status='received',file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    except Exception as e:rec.update(status='failed',error=str(e))
    print(json.dumps({k:rec.get(k) for k in ['name','status','bytes','error']}),flush=True);return rec
if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:records.extend(pool.map(fetch,SOURCES))
    MAN.write_text(json.dumps(records,indent=2),encoding='utf8')
