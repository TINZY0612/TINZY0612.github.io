"""First-30-day global supply projection; fixed rules and eligible calibration."""
import bisect
import datetime as dt
import json
from pathlib import Path
import statistics as st
ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parent;OUT=ROOT/'results'
q=json.loads((CIRCLE/'stage2/results/stage2_data_model.json').read_text())['quarters']
usdc=json.loads((ROOT/'raw/usdc_current_history.json').read_text())['tokens']
supply={dt.datetime.fromtimestamp(int(x['date']),dt.timezone.utc).date():x['circulating']['peggedUSD']/1e6 for x in usdc}
raw=json.loads((CIRCLE/'feasibility/raw/nyfed_sofr_2023_2026.json').read_text())
rates=raw['refRates'];rd={dt.date.fromisoformat(x['effectiveDate']):x['percentRate']/100 for x in rates};dates=sorted(rd)
def rate(d):return rd[dates[bisect.bisect_right(dates,d)-1]]

# SOFR is published on the following NY Fed business day. Use the next
# effective date in this continuous business-day series as publication date.
# The last observation lacks a next-day control and is not used here.
publication={effective:dates[i+1] for i,effective in enumerate(dates[:-1])}
def known_rate(d,cutoff):
    eligible=[effective for effective in dates[:-1] if effective<=d and publication[effective]<=cutoff]
    return rd[eligible[-1]]
def days(a,b):return [a+dt.timedelta(days=i) for i in range((b-a).days+1)]
rows=[];checks=[]
for i,cur in enumerate(q):
    if i<2:continue
    a=dt.date.fromisoformat(cur['start']);b=dt.date.fromisoformat(cur['end']);cut=a+dt.timedelta(days=29)
    eligible=[p for p in q[:i] if p['metrics']['reserve_income']['published_by']<=cut.isoformat()]
    if not eligible:continue
    base=eligible[-1];bd=days(dt.date.fromisoformat(base['start']),dt.date.fromisoformat(base['end']))
    base_usdc_days=sum(supply[d] for d in bd)
    base_sofr=sum(supply[d]*rate(d)/360 for d in bd)
    spread=(base['metrics']['reserve_income']['value']-base_sofr)/(base_usdc_days/365)
    observed=days(a,cut);future=days(cut+dt.timedelta(days=1),b)
    pace=(supply[cut]-supply[a-dt.timedelta(days=1)])/30
    actual=cur['metrics']['reserve_income']['value'];methods={};details={}
    for method in ['flat_last_supply','continue_first30_net_flow_pace']:
        proj={d:supply[d] for d in observed}
        for k,d in enumerate(future,1):proj[d]=supply[cut]+(pace*k if method.endswith('pace') else 0)
        assert min(proj.values())>0
        income=sum(s*known_rate(d,cut)/360 if d<=cut else s*known_rate(cut,cut)/360 for d,s in proj.items())+spread*sum(proj.values())/365
        methods[method]=income;details[method]={'estimated_mean_usdc_million':st.mean(proj.values()),'estimated_end_usdc_million':proj[b],'error':income/actual-1}
    checks.append({'name':cur['period']+' calibration public before cutoff','passed':base['metrics']['reserve_income']['published_by']<=cut.isoformat()})
    rows.append({'period':cur['period'],'cutoff':cut.isoformat(),'base_period':base['period'],'base_public_by':base['metrics']['reserve_income']['published_by'],
      'actual_reserve_income':actual,'last_known_sofr':known_rate(cut,cut),'lagged_annual_spread':spread,'first30_net_flow_pace_usdc_million_per_day':pace,
      'methods':methods,'details':details})
metrics={m:{'n':len(rows),'mape':st.mean(abs(r['details'][m]['error']) for r in rows),'mae_million':st.mean(abs(r['methods'][m]-r['actual_reserve_income']) for r in rows)} for m in rows[0]['methods']}
result={'scope':'Exploratory first-30-calendar-day reserve forecast from global chain-derived supply, not Ethereum-only gross flow extrapolation',
 'formula':'Sum projected USDC * observed/projected SOFR /360 plus eligible lagged annual spread * projected USDC-days /365',
 'rule':'Known first30 supply; future supply flat at day30 or daily net change over first30 continued. SOFR available only from next NY Fed business day, represented by next effective date in the continuous rate series. Future SOFR flat at latest available rate. No target-quarter financials in calibration.',
 'rows':rows,'metrics':metrics,'checks':checks,'limitations':['Fixed simple extrapolations, not optimized','Current historical supply/rate vintages','Net supply changes do not identify gross customer mint/redemption volume','Does not change the original Stage3 reserve backtest or the dated Q4 forecast']}
(OUT/'supply_projection_forecast.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'metrics':metrics,'rows':[{k:r[k] for k in ['period','base_period','methods']} for r in rows]},indent=2))
assert all(x['passed'] for x in checks)
