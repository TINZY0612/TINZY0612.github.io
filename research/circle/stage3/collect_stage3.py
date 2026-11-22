"""Download original public fund filings with bounded requests and provenance."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'; RAW.mkdir(parents=True,exist_ok=True)
MANIFEST=ROOT/'source_manifest.json'
records=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []

def fetch(name,url,ext='json'):
    existing=next((r for r in records if r['name']==name and r.get('status')=='received'),None)
    if existing and (ROOT/existing['file']).exists(): return existing
    r={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'CircleAcademicResearch/0.3 public financial research','Accept':'*/*'})
        with urllib.request.urlopen(req,timeout=30) as response:
            body=response.read(); r.update(http_status=response.status,content_type=response.headers.get('Content-Type'))
        p=RAW/(name+'.'+ext);p.write_bytes(body)
        r.update(status='received',file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
    except Exception as e:r.update(status='failed',error=str(e))
    print(json.dumps({k:r.get(k) for k in ['name','status','bytes','error']}),flush=True)
    return r

def save():MANIFEST.write_text(json.dumps(records,indent=2),encoding='utf8')

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else 'index'
    if mode=='index':
        q=urllib.parse.urlencode({'q':'"Circle Reserve Fund"','dateRange':'custom','startdt':'2025-01-01','enddt':'2026-11-21','forms':'N-MFP3','ciks':'0000844779','from':0,'size':100})
        records.append(fetch('fund_search','https://efts.sec.gov/LATEST/search-index?'+q))
        records.append(fetch('fund_submissions','https://data.sec.gov/submissions/CIK0000844779.json'))
        save()
    elif mode=='funds':
        search=json.loads((RAW/'fund_search.json').read_text())
        hits=search['hits']['hits']
        candidates=[]
        for h in hits:
            s=h['_source']; acc=s['adsh']; report=s.get('period_ending')
            if report and '2024-12-01'<=report<='2026-09-30':
                candidates.append({'accession':acc,'report_date':report,'filed':s['file_date'],'search_source':s,
                  'url':f"https://www.sec.gov/Archives/edgar/data/844779/{acc.replace('-','')}/primary_doc.xml"})
        # Search is series-specific, XML series identity is checked again after download.
        candidates=list({x['accession']:x for x in candidates}.values())
        (ROOT/'fund_candidates.json').write_text(json.dumps(candidates,indent=2))
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            fetched=list(pool.map(lambda c:fetch('fund_'+c['accession'],c['url'],'xml'),candidates))
        records.extend(fetched);save()
        valid=[]
        for c,r in zip(candidates,fetched):
            if r['status']!='received':continue
            tree=ET.parse(ROOT/r['file']); txt=lambda tag:tree.findtext('.//{*}'+tag)
            if txt('seriesId')!='S000077205':continue
            assert txt('reportDate')==c['report_date']
            c.update(file=r['file'],sha256=r['sha256'],series_id=txt('seriesId'),fund_name=txt('nameOfSeries'))
            valid.append(c)
        (ROOT/'fund_filings.json').write_text(json.dumps(valid,indent=2))
        print(json.dumps({'valid_filings':len(valid),'months':sorted({v['report_date'] for v in valid})}))

if __name__=='__main__':main()
