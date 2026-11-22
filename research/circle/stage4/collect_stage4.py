"""Bounded public-source collection for other revenue and ARC evidence."""
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw';RAW.mkdir(exist_ok=True)
MANIFEST=ROOT/'source_manifest.json'
records=json.loads(MANIFEST.read_text()) if MANIFEST.exists() else []
SOURCES=[
 ('q1_2026_release','https://www.circle.com/pressroom/circle-reports-first-quarter-2026-results'),
 ('may_2026_8k','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000148/crcl-20260511.htm'),
 ('may_2026_8k_index','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000148/0001876042-26-000148-index.htm'),
 ('arc_mainnet_announcement','https://www.arc.io/blog/arc-mainnet-goes-live-on-september-16-2026'),
 ('arc_home','https://www.arc.io/'),
 ('arc_docs_home','https://docs.arc.io/'),
 ('arc_token_whitepaper_page','https://www.circle.com/arc-token'),
 ('arc_node_readme','https://raw.githubusercontent.com/circlefin/arc-node/main/README.md'),
 ('arc_node_config','https://raw.githubusercontent.com/circlefin/arc-node/main/assets/mainnet/config.json'),
 ('arc_node_genesis','https://raw.githubusercontent.com/circlefin/arc-node/main/assets/mainnet/genesis.json'),
 ('arc_node_tree','https://api.github.com/repos/circlefin/arc-node/git/trees/main?recursive=1'),
 ('arc_node_commits','https://api.github.com/repos/circlefin/arc-node/commits?path=assets/mainnet/genesis.json&per_page=100'),
 ('cctp_fees_docs','https://developers.circle.com/cctp/fees'),
 ('usyc_docs','https://developers.circle.com/usyc'),
]

def fetch(name,url,payload=None):
    old=next((r for r in reversed(records) if r['name']==name),None)
    if old and (old.get('status')=='failed' or (ROOT/old['file']).exists()):return old
    r={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'method':'POST' if payload else 'GET'}
    if payload:r['request_payload']=payload
    try:
        headers={'User-Agent':'CircleAcademicResearch/0.4 public financial research','Accept':'*/*'}
        if payload:headers['Content-Type']='application/json'
        request=urllib.request.Request(url,data=json.dumps(payload).encode() if payload else None,headers=headers)
        with urllib.request.urlopen(request,timeout=30) as response:
            body=response.read();r.update(http_status=response.status,content_type=response.headers.get('Content-Type',''),final_url=response.url)
        ext='json' if 'json' in r['content_type'] else 'pdf' if 'pdf' in r['content_type'] else 'html' if 'html' in r['content_type'] else 'txt'
        p=RAW/(name+'.'+ext);p.write_bytes(body)
        r.update(status='received',file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
    except Exception as e:r.update(status='failed',error=str(e))
    print(json.dumps({k:r.get(k) for k in ['name','status','bytes','error']}),flush=True)
    return r

def run(sources):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        got=list(pool.map(lambda s:fetch(*s),sources))
    records.extend(got);MANIFEST.write_text(json.dumps(records,indent=2),encoding='utf8')

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='extra':
        sources=json.loads((ROOT/'extra_sources.json').read_text())
        run([(r['name'],r['url'],r.get('payload')) for r in sources])
    else:run(SOURCES)
