"""Read-only Arc RPC checks and a bounded September 14 ERC-20 mint search.

This checks one chain and one day. Matching a name/supply is a candidate, not
issuer authentication. No private keys, signing or transaction submissions.
"""
import datetime as dt
import json
from pathlib import Path
import time
from collect_stage4 import fetch,records,MANIFEST,ROOT

OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
RPC='https://rpc.mainnet.arc.io'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
ZERO='0x'+'0'*64

def rpc(name,method,params):
    assert method in {'eth_chainId','eth_blockNumber','eth_getBlockByNumber','eth_getLogs','eth_call','eth_getCode'}
    rec=fetch('chain_'+name,RPC,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
    records.append(rec);MANIFEST.write_text(json.dumps(records,indent=2),encoding='utf8')
    if rec['status']!='received':raise RuntimeError(rec.get('error'))
    data=json.loads((ROOT/rec['file']).read_text())
    if 'error' in data:raise RuntimeError(json.dumps(data['error']))
    return data['result']

cache={}
def block(n):
    if n not in cache:cache[n]=rpc('block_'+str(n),'eth_getBlockByNumber',[hex(n),False])
    return cache[n]

def first_at_or_after(timestamp,lo,hi):
    while lo<hi:
        mid=(lo+hi)//2;b=block(mid)
        if int(b['timestamp'],16)<timestamp:lo=mid+1
        else:hi=mid
    return lo

def decode_string(x):
    b=bytes.fromhex(x.removeprefix('0x'))
    if len(b)==32:return b.rstrip(b'\0').decode('utf8',errors='replace')
    if len(b)>=64:
        off=int.from_bytes(b[:32],'big');length=int.from_bytes(b[off:off+32],'big')
        return b[off+32:off+32+min(length,200)].decode('utf8',errors='replace')
    return x

def main():
    result={'scope':'Arc mainnet ERC-20 zero-address Transfer events on 14 September 2026 only','authenticated_arc_token_address':None,'mint_candidates':[]}
    try:
        chain=rpc('identity','eth_chainId',[]);assert int(chain,16)==5042
        latest=int(rpc('height','eth_blockNumber',[]),16)
        result.update(chain_id=5042,latest_block=latest,latest_utc=dt.datetime.fromtimestamp(int(block(latest)['timestamp'],16),dt.timezone.utc).isoformat())
        # Known official USDC address provides a read-only contract-call control.
        usdc='0x3600000000000000000000000000000000000000'
        sym=decode_string(rpc('usdc_symbol','eth_call',[{'to':usdc,'data':'0x95d89b41'},'latest']))
        dec=int(rpc('usdc_decimals','eth_call',[{'to':usdc,'data':'0x313ce567'},'latest']),16)
        result['usdc_control']={'address':usdc,'symbol':sym,'erc20_decimals':dec};assert sym=='USDC' and dec==6
        start=int(dt.datetime(2026,9,14,tzinfo=dt.timezone.utc).timestamp());stop=start+86400
        first=first_at_or_after(start,0,latest);last=first_at_or_after(stop,first,latest)-1
        result.update(first_block=first,last_block=last,first_block_utc=dt.datetime.fromtimestamp(int(block(first)['timestamp'],16),dt.timezone.utc).isoformat(),last_block_utc=dt.datetime.fromtimestamp(int(block(last)['timestamp'],16),dt.timezone.utc).isoformat())
        # Check brackets explicitly; no block cadence assumption substitutes for timestamps.
        assert int(block(first-1)['timestamp'],16)<start<=int(block(first)['timestamp'],16)
        assert int(block(last)['timestamp'],16)<stop<=int(block(last+1)['timestamp'],16)
        logs=[];ranges=[]
        for a in range(first,last+1,9999):
            b=min(a+9998,last)
            got=rpc(f'mints_{a}_{b}','eth_getLogs',[{'fromBlock':hex(a),'toBlock':hex(b),'topics':[TRANSFER,ZERO]}])
            logs.extend(got);ranges.append({'first':a,'last':b,'events':len(got)})
        result.update(log_ranges=ranges,zero_address_transfer_events=len(logs))
        (OUT/'arc_september14_mint_logs.json').write_text(json.dumps(logs,indent=2))
        addresses=sorted({l['address'].lower() for l in logs if len(l.get('topics',[]))==3})
        result['erc20_style_mint_contracts']=len(addresses)
        candidates=[]; metadata_cache={}
        # First filter raw amounts for a 10-billion-token mint at a conventional precision.
        for l in logs:
            if len(l.get('topics',[]))!=3:continue
            amount=int(l.get('data','0x0'),16)
            possible=[d for d in range(0,25) if amount==10_000_000_000*10**d]
            if not possible:continue
            a=l['address'];item={'address':a,'tx_hash':l['transactionHash'],'block':int(l['blockNumber'],16),'log_index':int(l['logIndex'],16),'raw_amount':str(amount),'possible_decimals':possible,'authentication':'unverified candidate'}
            if a in metadata_cache:
                item.update(metadata_cache[a]);candidates.append(item);continue
            if len(metadata_cache)>=64:
                item['metadata_status']='not queried: 64-contract exploratory budget reached'
                candidates.append(item);continue
            try:
                decimals=int(rpc('candidate_'+a+'_decimals','eth_call',[{'to':a,'data':'0x313ce567'},'latest']),16)
                item.update(decimals=decimals,symbol=decode_string(rpc('candidate_'+a+'_symbol','eth_call',[{'to':a,'data':'0x95d89b41'},'latest'])),name=decode_string(rpc('candidate_'+a+'_name','eth_call',[{'to':a,'data':'0x06fdde03'},'latest'])),mint_tokens=str(amount//10**decimals))
            except Exception as e:item['metadata_error']=str(e)
            metadata_cache[a]={k:v for k,v in item.items() if k in {'decimals','symbol','name','mint_tokens','metadata_error'}}
            candidates.append(item)
        result['mint_candidates']=candidates;result['status']='bounded search completed'
    except Exception as e:result.update(status='partial check',error=str(e))
    (OUT/'arc_chain_check.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
