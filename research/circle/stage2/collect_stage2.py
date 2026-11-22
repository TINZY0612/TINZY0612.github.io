"""Download the stage-two public accounting and adapter sources, without keys."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'
RAW.mkdir(parents=True,exist_ok=True)

SOURCES=[
 ('sec_submissions','https://data.sec.gov/submissions/CIK0001876042.json'),
 ('fy2025_html','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm'),
 ('q3_2025_html','https://www.sec.gov/Archives/edgar/data/1876042/000187604225000047/crcl-20250930.htm'),
 ('q2_2025_html','https://www.sec.gov/Archives/edgar/data/1876042/000162828025039781/crcl-20250630.htm'),
 ('q1_2026_html','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000150/crcl-20260331.htm'),
 ('q2_2026_html','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000248/crcl-20260630.htm'),
 ('q3_2026_html','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm'),
 ('ipo_prospectus','https://www.sec.gov/Archives/edgar/data/1876042/000119312525135795/d737521d424b4.htm'),
 ('usdc_config','https://raw.githubusercontent.com/DefiLlama/peggedassets-server/master/src/adapters/peggedAssets/usd-coin/config.ts'),
 ('peggedassets_tree','https://api.github.com/repos/DefiLlama/peggedassets-server/git/trees/master?recursive=1'),
 ('circle_contracts','https://developers.circle.com/stablecoins/usdc-contract-addresses'),
]

def fetch(name,url):
 rec={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'CircleAcademicResearch/0.2 public financial research','Accept':'*/*'})
  with urllib.request.urlopen(req,timeout=30) as r:
   body=r.read(); rec.update(http_status=r.status,content_type=r.headers.get('Content-Type',''))
  ext='json' if 'json' in rec['content_type'] else 'html' if 'html' in rec['content_type'] else 'txt'
  path=RAW/(name+'.'+ext); path.write_bytes(body)
  rec.update(status='received',file=str(path.relative_to(ROOT)),sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
 except Exception as e: rec.update(status='failed',error=str(e))
 print(json.dumps({k:rec.get(k) for k in ['name','status','bytes','error']}),flush=True)
 return rec

if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  records=list(pool.map(lambda x:fetch(*x),SOURCES))
 (ROOT/'source_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf8')
