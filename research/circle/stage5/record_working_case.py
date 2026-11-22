"""Save the newly selected flat-other-revenue case without replacing earlier forecasts."""
from decimal import Decimal as D
import datetime as dt
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parent
ledger=json.loads((CIRCLE/'stage4/results/other_revenue_model.json').read_text())['ledger']
entries=[e for e in ledger if e['period']=='2026Q3' and e['classification']=='current']
latest=max(entries,key=lambda e:e['published_by']);m=latest['metrics']
services=D(str(m['subscription_services']['value']));transaction=D(str(m['transaction_revenue']['value']));other=D(str(m['other']['value']))
arc=D('181.8');flat=services+transaction+other-arc
guidance=json.loads((CIRCLE/'stage4/results/2026-11-21_Q4_other_revenue_forecast.json').read_text())['forecast']
record={'recorded_as_of':'2026-11-21','recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'role':'Latest user-directed working revenue case; independent of prior issuer-guidance benchmark',
 'units':'USD millions','flat_rule':'Hold non-ARC operating other revenue at Q3 2026 level in each future quarter; no separate incremental USYC uplift',
 'source':latest['source_url'],'baseline_period':'2026Q3','subscription_services':float(services),'transaction_revenue':float(transaction),
 'reported_other_product_bucket':float(other),'reported_q3_arc_recognition_rounded':float(arc),'non_arc_other_product_residual_approx':float(other-arc),
 'quarterly_non_arc_operating_other_revenue_approx':float(flat),'q4_existing_arc_recognition_assumption':60.4,'q4_total_operating_other_revenue_approx':float(flat+D('60.4')),
 'subsequent_quarter_operating_other_revenue_approx':float(flat),'annualized_non_arc_operating_other_revenue_approx':float(flat*4),
 'new_unannounced_arc_sales_assumed':0,'existing_arc_recognition_after_q4_assumed':0,'recognition_timing_verified':False,'q4_new_cash_from_existing_deferred_recognition':0,'q4_net_profit_effect':None,
 'issuer_guidance_implied_q4_other_revenue_range':[guidance['implied_q4_total_other_low'],guidance['implied_q4_total_other_high']],
 'limitations':['Residual ordinary other amount is approximate because ARC recognition is disclosed rounded to $0.1m','Flat revenue is a user-directed scenario, not demonstrated predictability','DEX activity does not determine future institutional token-sale decisions','Q4 ARC recognition is not a verified issuer timetable and is not automatically net profit','Other revenue excludes the separate non-operating other income/expense line','Prior dated forecasts are retained; do not blend the guidance benchmark into this case']}
p=ROOT/'results/2026-11-21_flat_other_ARC_working_case.json'
if p.exists():
    old=json.loads(p.read_text());old.pop('recorded_at_utc',None);new=record.copy();new.pop('recorded_at_utc',None);assert old==new,'Use a new dated version for changed assumptions.'
else:p.write_text(json.dumps(record,indent=2),encoding='utf-8')
activity=json.loads((ROOT/'arc_activity/activity_results.json').read_text());rows=activity['rows']
assert len(rows)==4 and all(r['observations']==30 and not r['missing_days'] for r in rows)
for r in rows:assert abs(sum(x['volume_usd'] for x in r['daily_window'])/30-r['mean_daily_dex_volume_usd'])<1e-6
manifest=json.loads((ROOT/'arc_activity/source_manifest.json').read_text());success=[r for r in manifest if r.get('status')=='received']
assert all(hashlib.sha256((ROOT/'arc_activity'/r['file']).read_bytes()).hexdigest()==r['sha256'] for r in success)
arcmean=rows[0]['mean_daily_dex_volume_usd'];ratios={r['chain']:arcmean/r['mean_daily_dex_volume_usd'] for r in rows[1:]}
(ROOT/'arc_activity/verification.json').write_text(json.dumps({'four_30day_series_complete':True,'daily_means_verified':True,'received_source_hashes_verified':len(success),'arc_spot_dex_volume_relative_to_peers':ratios,'flat_revenue_arithmetic_verified':abs(float(flat)-25.464)<1e-9},indent=2),encoding='utf-8')
print(json.dumps({'working_case':record,'arc_spot_dex_peer_ratios':ratios},indent=2))
