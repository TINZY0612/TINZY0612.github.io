"""Dated Arc DEX activity comparison and user-selected revenue assumptions."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parent/'arc_activity';ROOT.mkdir(exist_ok=True)
RAW=ROOT/'raw';RAW.mkdir(exist_ok=True);manifest=json.loads((ROOT/'source_manifest.json').read_text()) if (ROOT/'source_manifest.json').exists() else []
def fetch(name,url):
    p=RAW/(name+'.json')
    if p.exists():return json.loads(p.read_text())
    rec={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'CircleAcademicResearch/0.7','Accept':'application/json'})
        with urllib.request.urlopen(req,timeout=25) as r:
            raw=r.read();rec.update(http_status=r.status,final_url=r.url)
        data=json.loads(raw);p.write_bytes(raw);rec.update(status='received',file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest())
    except Exception as e:rec.update(status='failed',error=str(e));data=None
    manifest.append(rec);(ROOT/'source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(rec),flush=True)
    return data
def day(t):return dt.datetime.fromtimestamp(int(t),dt.timezone.utc).date()
rows=[];cut=dt.date(2026,11,20);start=cut-dt.timedelta(days=29)
for chain in ['arc','ethereum','solana','base']:
    x=fetch('dex_'+chain,'https://api.llama.fi/overview/dexs/'+chain+'?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume')
    if not x:continue
    chart={day(t):float(v) for t,v in x.get('totalDataChart',[]) if v is not None}
    expected=[start+dt.timedelta(days=i) for i in range(30)]
    present=[d for d in expected if d in chart]
    rows.append({'chain':chain,'window_start':start.isoformat(),'window_end':cut.isoformat(),'observations':len(present),'missing_days':[d.isoformat() for d in expected if d not in chart],
      'sum_daily_dex_volume_usd':sum(chart[d] for d in present),'mean_daily_dex_volume_usd':sum(chart[d] for d in present)/len(present) if present else None,
      'latest_provider_24h_usd':x.get('total24h'),'latest_provider_7d_usd':x.get('total7d'),'latest_provider_30d_usd':x.get('total30d'),
      'daily_window':[{'date':d.isoformat(),'volume_usd':chart[d]} for d in present]})
result={'as_of':'2026-11-21','scope':'Provider tracked spot DEX volume; not all Arc payments, USDC transfers, bridging, perpetuals or token sales','rows':rows}
(ROOT/'activity_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'window':[start.isoformat(),cut.isoformat()],'summary':[{k:v for k,v in r.items() if k!='daily_window'} for r in rows]},indent=2))
