"""Public read-only snapshots. Run one collector process at a time."""
import datetime as dt
import hashlib
import gzip
import json
from pathlib import Path
import threading
import urllib.request
ROOT=Path(__file__).resolve().parent;RAW=ROOT/'raw';RAW.mkdir(exist_ok=True)
MAN=ROOT/'source_manifest.json'
records=json.loads(MAN.read_text()) if MAN.exists() else []
lock=threading.Lock()
def fetch(name,url,payload=None):
    old=next((r for r in records if r['name']==name and r.get('status')=='received'),None)
    if old and (ROOT/old['file']).exists():
        p=ROOT/old['file'];b=gzip.open(p,'rb').read() if p.suffix=='.gz' else p.read_bytes()
        return json.loads(b) if old.get('json') else b.decode('utf8')
    rec={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'method':'POST' if payload is not None else 'GET'}
    if payload is not None:rec['payload']=payload
    try:
        h={'User-Agent':'CircleAcademicResearch/0.6 public financial research','Accept':'*/*'}
        if payload is not None:h['Content-Type']='application/json'
        req=urllib.request.Request(url,data=json.dumps(payload).encode() if payload is not None else None,headers=h)
        with urllib.request.urlopen(req,timeout=35) as response:
            b=response.read();rec.update(final_url=response.url,http_status=response.status,content_type=response.headers.get('Content-Type',''))
        try:data=json.loads(b);js=True
        except Exception:data=b.decode('utf8');js=False
        p=RAW/(name+('.json' if js else '.txt'));p.write_bytes(b)
        rec.update(status='received',file=str(p.relative_to(ROOT)),bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),json=js)
    except Exception as e:
        rec.update(status='failed',error=str(e));data=None
    with lock:
        records.append(rec);MAN.write_text(json.dumps(records,indent=2),encoding='utf8')
    print(json.dumps({k:rec.get(k) for k in ['name','status','bytes','error']}),flush=True)
    if rec['status']!='received':raise RuntimeError(rec['error'])
    return data
def rpc(name,method,params,url='https://ethereum-rpc.publicnode.com'):
    assert method in {'web3_sha3','eth_chainId','eth_getBlockByNumber','eth_getLogs','eth_getTransactionReceipt','eth_call','eth_getCode','eth_blockNumber'}
    errors=[]
    providers=[('',url),('_tenderly','https://mainnet.gateway.tenderly.co'),('_drpc','https://eth.drpc.org')]
    if url=='https://ethereum-rpc.publicnode.com' and method in {'eth_call','eth_getLogs'}:
        providers=[providers[1],providers[0],providers[2]]
    for suffix,provider in providers:
        try:
            r=fetch(name+suffix,provider,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
            if 'error' in r:raise RuntimeError(str(r['error']))
            return r['result']
        except Exception as e:errors.append(str(e))
    raise RuntimeError(' | '.join(errors))
