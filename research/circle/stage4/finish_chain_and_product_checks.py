"""Summarize the saved mint scan, validate it, and test public product endpoints.

Read-only calls. Product current snapshots are feasibility evidence, not historical
forecast inputs. An ARC candidate is never promoted to issuer-authenticated here.
"""
import datetime as dt
import json
import sys
from pathlib import Path
from collect_stage4 import fetch, records, MANIFEST, ROOT
from check_arc_chain import decode_string, TRANSFER, ZERO

OUT=ROOT/'results'
if '--retry-network-denied' in sys.argv:
    # Preserve rejected attempts under a distinct name, then retry only socket-denied
    # requests in this script under the approved network execution context.
    for rec in records:
        if rec.get('status')=='failed' and '10013' in rec.get('error','') and (rec['name'].startswith(('usyc_','cctp_current_','product_snapshot_')) or rec['name']=='chain_cross_provider_mints'):
            rec['name']=rec['name']+'_sandbox_denied'
    MANIFEST.write_text(json.dumps(records,indent=2),encoding='utf8')
checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
def get(name,url,payload=None):
    rec=fetch(name,url,payload);records.append(rec)
    MANIFEST.write_text(json.dumps(records,indent=2),encoding='utf8')
    if rec['status']!='received':return {'error':rec.get('error')}
    try:return json.loads((ROOT/rec['file']).read_text())
    except Exception:return {'error':'response is not JSON','file':rec['file']}
def rpc(name,method,params,url='https://rpc.mainnet.arc.io'):
    response=get(name,url,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
    return response.get('result',response)

logs=json.loads((OUT/'arc_september14_mint_logs.json').read_text())
first,last=20731906,20900405
ranges=[]
for p in (ROOT/'raw').glob('chain_mints_*.json'):
    _,_,a,b=p.stem.split('_');a,b=int(a),int(b)
    arr=json.loads(p.read_text())['result']
    check(f'log filter and range {a}',all(a<=int(x['blockNumber'],16)<=b and x['topics'][:2]==[TRANSFER,ZERO] and not x.get('removed',False) for x in arr))
    ranges.append({'first':a,'last':b,'events':len(arr)})
ranges.sort(key=lambda x:x['first'])
check('ranges span the requested day',ranges[0]['first']==first and ranges[-1]['last']==last)
check('ranges contiguous',all(x['last']+1==y['first'] for x,y in zip(ranges,ranges[1:])))
check('no duplicate logs',len(logs)==len({(x['transactionHash'],x['logIndex']) for x in logs}))
check('saved aggregate matches range counts',len(logs)==sum(x['events'] for x in ranges))

candidate_logs=[x for x in logs if len(x['topics'])==3 and any(int(x.get('data','0x0'),16)==10_000_000_000*10**d for d in range(25))]
addresses=sorted({x['address'].lower() for x in candidate_logs})
metadata=[]
for a in addresses:
    m={'address':a,'authentication':'unverified'}
    for field in ['decimals','symbol','name']:
        p=ROOT/'raw'/f'chain_candidate_{a}_{field}.json'
        if not p.exists():continue
        r=json.loads(p.read_text()).get('result')
        if not r:continue
        try:m[field]=int(r,16) if field=='decimals' else decode_string(r)
        except Exception:pass
    if len(m)>2:metadata.append(m)

# Compare an independent provider for the first 500 blocks of the saved scan.
end=first+499
other=rpc('chain_cross_provider_mints','eth_getLogs',[{'fromBlock':hex(first),'toBlock':hex(end),'topics':[TRANSFER,ZERO]}], 'https://rpc.drpc.mainnet.arc.io')
if not isinstance(other,list):
    other=rpc('chain_quicknode_mints','eth_getLogs',[{'fromBlock':hex(first),'toBlock':hex(end),'topics':[TRANSFER,ZERO]}], 'https://rpc.quicknode.mainnet.arc.io')
local=[x for x in logs if first<=int(x['blockNumber'],16)<=end]
if isinstance(other,list):
    check('independent-provider 500-block subset agrees', {(x['transactionHash'],x['logIndex'],x['address'],x['data']) for x in other}=={(x['transactionHash'],x['logIndex'],x['address'],x['data']) for x in local})
else:pass  # Endpoint availability is reported separately, not as a data-integrity assertion.

result={'retrieved_as_of':'2026-11-21','scope':'Arc mainnet, ERC-20-style zero-address Transfer logs, UTC 2026-09-14 only',
 'chain_id':5042,'first_block':first,'last_block':last,'block_count':last-first+1,
 'zero_address_transfer_events':len(logs),'ten_billion_raw_amount_matches':len(candidate_logs),'distinct_candidate_addresses':len(addresses),
 'metadata_contracts_sampled':len(metadata),'metadata_sample':metadata,'authenticated_arc_token_address':None,
 'ranges':ranges,'checks':checks,'cross_provider_subset_events':len(other) if isinstance(other,list) else None,
 'cross_provider_status':'subset compared' if isinstance(other,list) else 'not verified: alternate public providers returned errors',
 'conclusion':'The saved scan is technically queryable, but token identity and investor/escrow wallets are not authenticated. This does not establish ARC token transfers or revenue.',
 'limits':['Not all chains or dates','ERC-20 events do not cover native genesis allocations or nonstandard accounting','Provider agreement tested on only a 500-block subset; no claim of exhaustive provider completeness','Metadata exploration stopped after the completed log scan to avoid redundant lookups','Historic transaction data retrieved now does not prove timely public visibility before earnings']}
(OUT/'arc_chain_check.json').write_text(json.dumps(result,indent=2),encoding='utf8')

products={}
for name,url in [('usyc_current_price','https://usyc.hashnote.com/api/price'),('usyc_historical_prices','https://usyc.hashnote.com/api/price-reports'),('cctp_current_fee_ethereum_avalanche','https://iris-api.circle.com/v2/burn/USDC/fees/0/1')]:
    products[name]=get(name,url)
usyc='0x8a5D989Bbb96929F689B0200f435f53dA42bF490'
height=rpc('product_snapshot_height','eth_blockNumber',[])
if isinstance(height,str):
    values={}
    for key,selector in [('symbol','0x95d89b41'),('decimals','0x313ce567'),('total_supply','0x18160ddd')]:
        v=rpc('usyc_arc_'+key,'eth_call',[{'to':usyc,'data':selector},height])
        try:values[key]=decode_string(v) if key=='symbol' else int(v,16)
        except Exception:values[key]=v
    products['usyc_arc_snapshot']={'official_address':usyc,'address_source':'https://developers.circle.com/tokenized/usyc/smart-contracts','block':int(height,16),'values':values,'use':'current read-only feasibility snapshot, not Q3 forecast input or total cross-chain AUM'}
(OUT/'product_endpoint_checks.json').write_text(json.dumps(products,indent=2),encoding='utf8')
print(json.dumps({'chain_checks_passed':sum(c['passed'] for c in checks),'chain_checks_total':len(checks),'mint_logs':len(logs),'candidate_contracts':len(addresses),'metadata_sampled':len(metadata),'products':{k:({'entity':v.get('entity'),'rows':len(v['data'])} if isinstance(v,dict) and isinstance(v.get('data'),list) else v) for k,v in products.items()}},indent=2))
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
