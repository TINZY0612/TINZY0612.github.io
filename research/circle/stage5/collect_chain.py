"""Bounded read-only Ethereum USDC flows, CCTP messages and USYC reports."""
import datetime as dt
import json
from public_data import fetch,rpc,ROOT
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
USDC='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
USYC='0x136471a34f6ef19fe571effc1ca711fdb8e49f2b'
REPORTER='0x9fde717a21c5b272b8956d3aa0c3551e1ffd23d7'
TM1='0xbd3fa81b58ba92a82136038b25adec7066af3155'
TM2='0x28b5a0e9c621a5badaa536219b3a228c8168cf5d'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
def sha(sig):return rpc('keccak_'+sig.split('(')[0]+'_'+str(len(sig)),'web3_sha3',['0x'+sig.encode().hex()])
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2),encoding='utf8')
cache={}
def block(n):
    if n not in cache:cache[n]=rpc('block_'+str(n),'eth_getBlockByNumber',[hex(n),False])
    return cache[n]
def boundary(day):
    stamp=int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp())
    h=fetch('lookup_'+day,'https://coins.llama.fi/block/ethereum/'+str(stamp))['height']
    for _ in range(100):
        if int(block(h)['timestamp'],16)>=stamp:h-=1
        elif int(block(h+1)['timestamp'],16)<stamp:h+=1
        else:return h
    raise RuntimeError('Block lookup did not bracket date '+day)
def logs(label,a,b,address,topics):
    try:
        got=rpc(f'{label}_{a}_{b}','eth_getLogs',[{'fromBlock':hex(a),'toBlock':hex(b),'address':address,'topics':topics}])
        if len(got) in {10000,20000,50000} and b-a>1000:raise RuntimeError('Possible exact provider result cap; split range')
        assert all(a<=int(x['blockNumber'],16)<=b and x['address'].lower()==address.lower() and not x.get('removed',False) for x in got)
        return got
    except Exception:
        if b-a<2000:raise
        mid=(a+b)//2
        return logs(label,a,mid,address,topics)+logs(label,mid+1,b,address,topics)
def scan(label,a,b,address,topics,step=50000):
    all_logs=[]
    for first in range(a,b+1,step):
        all_logs.extend(logs(label,first,min(b,first+step-1),address,topics))
    assert len(all_logs)==len({(x['transactionHash'],x['logIndex']) for x in all_logs})
    return all_logs

def main():
    identity=int(rpc('ethereum_identity','eth_chainId',[]),16);assert identity==1
    assert sha('Transfer(address,address,uint256)')==TRANSFER
    source1=fetch('cctp_v1_source','https://raw.githubusercontent.com/circlefin/evm-cctp-contracts/master/src/TokenMessenger.sol')
    source2=fetch('cctp_v2_source','https://raw.githubusercontent.com/circlefin/evm-cctp-contracts/master/src/v2/TokenMessengerV2.sol')
    dates=['2025-01-01','2025-04-01','2025-07-01','2025-10-01','2026-01-01','2026-04-01','2026-07-01','2026-10-01']
    bounds={d:boundary(d) for d in dates};save('ethereum_boundaries.json',bounds)
    selector=sha('localMinter()')[:10]
    minters={}
    for name,address in [('v1',TM1),('v2',TM2)]:
        for day in ['2026-07-01','2026-10-01']:
            result=rpc('minter_'+name+'_'+day,'eth_call',[{'to':address,'data':selector},hex(bounds[day])])
            minters[name+'_'+day]='0x'+result[-40:]
    assert minters['v2_2026-10-01'].lower()=='0xfd78ee919681417d192449715b2594ab58f5d002'
    save('authenticated_contracts.json',{'usdc':USDC,'usyc':USYC,'usyc_reporter':REPORTER,'token_messengers':{'v1':TM1,'v2':TM2},'minters':minters,
      'sources':['https://developers.circle.com/stablecoins/usdc-contract-addresses','https://developers.circle.com/cctp/references/contract-addresses','https://developers.circle.com/cctp/v1/evm-smart-contracts','https://developers.circle.com/tokenized/usyc/smart-contracts'],
      'usyc_reporter_authentication':'Reporter appears in transaction hash supplied by issuer USYC API, verified in prior stage; token filter uses official USYC address.'})
    # Complete-quarter flagship-chain issuance decomposition.
    a=bounds['2026-07-01']+1;b=bounds['2026-10-01']
    mint=sha('Mint(address,address,uint256)');burn=sha('Burn(address,uint256)')
    flow=scan('usdc_flow',a,b,USDC,[[mint,burn]])
    save('usdc_q3_2026_mint_burn_logs.json',{'first':a,'last':b,'mint_topic':mint,'burn_topic':burn,'logs':flow})
    supplies={}
    for day in ['2026-07-01','2026-10-01']:
        supplies[day]=rpc('supply_'+day,'eth_call',[{'to':USDC,'data':'0x18160ddd'},hex(bounds[day])])
    save('usdc_flow_controls.json',{'bounds':{'first':a,'last':b},'raw_supplies':supplies,'events':len(flow)})
    # Destination-chain fee observation; fees may be zero for non-paying transfers.
    fee_topic=sha('MintAndWithdraw(address,uint256,address,uint256)')
    fee_logs=scan('cctp_incoming_fees',a,b,TM2,[fee_topic])
    save('ethereum_cctp_q3_fee_logs.json',{'topic':fee_topic,'logs':fee_logs})
    # Derive source-route event signature from official source rather than assume docs match ABI.
    import re
    event=re.search(r'event\s+DepositForBurn\s*\((.*?)\)\s*;',source2,re.S)
    if event:
        fields=[' '.join(x.split()) for x in event.group(1).split(',')]
        signature='DepositForBurn('+','.join(x.split()[0] for x in fields)+')'
        route_logs=scan('cctp_source_routes',a,b,TM2,[sha(signature)])
        save('ethereum_cctp_q3_routes.json',{'fields':fields,'signature':signature,'logs':route_logs})
    # Fund reporter history: both pre- and post-July 2026 ABI versions.
    sigs=[
     'Transmitted(address,uint256,uint256,uint256,uint256,uint256,uint256,uint256)',
     'Transmitted(address,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256)']
    topics=[sha(s) for s in sigs];token_topic='0x'+USYC[2:].rjust(64,'0')
    fund=scan('usyc_reports',bounds['2025-01-01']+1,b,REPORTER,[topics,token_topic],step=50000)
    save('usyc_2025_2026_reporter_logs.json',{'signatures':sigs,'topics':topics,'logs':fund})
    # Save actual block timestamps for every report to enforce knowledge cutoffs.
    nums=sorted({int(x['blockNumber'],16) for x in fund});times={}
    for start in range(0,len(nums),20):
        batch=nums[start:start+20]
        payload=[{'jsonrpc':'2.0','id':n,'method':'eth_getBlockByNumber','params':[hex(n),False]} for n in batch]
        try:
            response=fetch('usyc_block_batch_'+str(batch[0]),'https://ethereum-rpc.publicnode.com',payload)
            byid={x['id']:x for x in response};assert set(byid)==set(batch)
            for n in batch:
                value=byid[n]['result'];assert int(value['number'],16)==n
                times[str(n)]=int(value['timestamp'],16)
        except Exception:
            for n in batch:times[str(n)]=int(block(n)['timestamp'],16)
    save('usyc_report_block_times.json',times)
    print(json.dumps({'status':'completed','usdc_flow_events':len(flow),'cctp_fee_events':len(fee_logs),'usyc_reports':len(fund)}),flush=True)
if __name__=='__main__':main()
