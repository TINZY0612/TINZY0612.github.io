"""Validate public fee units and aggregate currently available product histories."""
import calendar
import datetime as dt
from decimal import Decimal as D
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
def read(n):return json.loads((ROOT/'raw'/n).read_text())
reports=read('usyc_historical_prices.json')['data']
checks=[]
def check(name,value):checks.append({'name':name,'passed':bool(value)})
sample=reports[0];receipt=read('usyc_fee_receipt.json')['result']
token='0x136471a34f6ef19fe571effc1ca711fdb8e49f2b'
transfer='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
mints=[l for l in receipt['logs'] if l['address'].lower()==token and l['topics'][0]==transfer and int(l['topics'][1],16)==0]
fee_shares=D(sample['fee']);fee_usd=fee_shares*D(sample['price'])
check('receipt success',receipt['status']=='0x1')
check('receipt is issuer API transaction',receipt['transactionHash'].lower()==sample['txhash'].lower())
check('one official-token mint matches fee shares',any(D(int(l['data'],16))/10**6==fee_shares for l in mints))
check('latest fee equals ten percent of gross yield including embedded income',abs(fee_usd-D('.10')*(D(sample['interest'])+D(sample['embeddedIncome'])))<D('.000002'))
check('every returned price report has same fee identity',all(abs(D(x['fee'])*D(x['price'])-D('.10')*(D(x['interest'])+D(x.get('embeddedIncome','0'))))<D('.00001') for x in reports))
check('limit parameter did not extend history',read('usyc_history_limit_test.json')==read('usyc_historical_prices.json'))
check('offset parameter did not extend history',read('usyc_history_offset_test.json')==read('usyc_historical_prices.json'))

histories={
 'usyc_performance_fees':read('llama_usyc_revenue_history.json'),
 'usyc_gross_fund_yield':read('llama_usyc_fee_history.json'),
 'cctp_protocol_fees':read('llama_cctp_fee_history.json')}
quarters=[]
financial=json.loads((OUT/'other_revenue_model.json').read_text())
for e in financial['forecasts']:
    period=e['period'];year=int(period[:4]);quarter=int(period[-1]);month=3*quarter-2
    a=dt.date(year,month,1);b=dt.date(year+1,1,1) if quarter==4 else dt.date(year,month+3,1)
    row={'period':period,'ordinary_other_actual_scoring_only':e['actual_other_revenue']-(181.8 if period=='2026Q3' else 0)}
    for key,h in histories.items():
        v=[(dt.datetime.fromtimestamp(int(t),dt.timezone.utc).date(),D(str(v))) for t,v in h['totalDataChart'] if a<=dt.datetime.fromtimestamp(int(t),dt.timezone.utc).date()<b]
        check(key+' '+period+' dates unique',len(v)==len({d for d,_ in v}))
        row[key+'_usd']=float(sum((v for _,v in v),D(0)))
        row[key+'_days_present']=len(v)
        row[key+'_calendar_days']=(b-a).days
        row[key+'_missing_dates']=[(a+dt.timedelta(days=i)).isoformat() for i in range((b-a).days) if a+dt.timedelta(days=i) not in {d for d,_ in v}]
    row['tracked_fees_usd']=row['usyc_performance_fees_usd']+row['cctp_protocol_fees_usd']
    row['tracked_fees_share_ordinary_other']=row['tracked_fees_usd']/1e6/row['ordinary_other_actual_scoring_only']
    quarters.append(row)
latest_date=dt.datetime.fromtimestamp(int(sample['timestamp']),dt.timezone.utc).date().isoformat()
# Genuine forward arithmetic: no future Q4 actual is read or invented.
ytd=sum(e['actual_other_revenue'] for e in financial['forecasts'] if e['period'] in ['2026Q1','2026Q2','2026Q3'])
ordinary_ytd=ytd-181.8
forward={'as_of':'2026-11-21','period':'2026Q4','actual':None,'method':'Full-year guidance less reported nine months; conditional on guidance being achieved',
 'ytd_total_other':ytd,'total_other_fy_guidance':[310,330],
 'implied_q4_total_other_low':310-ytd,'implied_q4_total_other_high':330-ytd,'implied_q4_total_other_midpoint':320-ytd,
 'ordinary_ytd':ordinary_ytd,'ordinary_other_fy_guidance':[130,150],
 'implied_q4_ordinary_low':130-ordinary_ytd,'implied_q4_ordinary_high':150-ordinary_ytd,'implied_q4_ordinary_midpoint':140-ordinary_ytd,
 'incremental_arc_base_case':0,'remaining_existing_arc_consideration_approx':60.4,
 'guidance_source':'https://s206.q4cdn.com/265218871/files/doc_earnings/2026/q3/transcript/Q326-Earnings-Transcript.pdf',
 'public_by':'2026-11-04','locator':'printed page 9, guidance section (zero-based PDF page 8)',
 'limitations':['Total guidance and ordinary guidance plus actual ARC differ by $1.8m at both endpoints; preserve the disclosed ranges rather than force them to reconcile.','No announced recognition schedule established for remaining $60.4m; it is not automatically Q4 revenue.','This is management-guidance-based, not an independent on-chain point estimate.','Guidance can change, integration acceptance dates and fee terms are private.']}

result={'as_of':'2026-11-21','scope':'Current public data reconstruction, not historical-vintage backtest or audited product-revenue reconciliation',
 'usyc_issuer_api':{'rows':len(reports),'first_date':min(dt.datetime.fromtimestamp(int(x['timestamp']),dt.timezone.utc).date().isoformat() for x in reports),'last_date':latest_date,'history_limit':'Only 45 reports returned; limit=2000 and offset=45 unchanged'},
 'usyc_fee_mint_control':{'date':latest_date,'tx_hash':sample['txhash'],'block':int(receipt['blockNumber'],16),'token_address':token,
 'token_address_source':'https://developers.circle.com/tokenized/usyc/smart-contracts','fee_usyc_shares':str(fee_shares),'price_usd':sample['price'],'fee_usd':str(fee_usd),
 'gross_yield_usd':str(D(sample['interest'])+D(sample['embeddedIncome'])),'fee_recipient':('0x'+mints[0]['topics'][2][-40:]) if mints else None,
 'scope':'One transaction validates the unit conversion and fee mint, not all history or Circle consolidated GAAP recognition'},
 'quarterly_fee_observations':quarters,'q4_guidance_based_forecast':forward,
 'adapter_vintages':{k:{'sha':(r:=read(k+'_adapter_commit.json'))[0]['sha'],'commit_date':r[0]['commit']['committer']['date']} for k in ['llama_usyc','llama_cctp']},
 'checks':checks,'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks)}
(OUT/'product_fee_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'checks_passed':result['checks_passed'],'checks_total':len(checks),'fee_mint':result['usyc_fee_mint_control'],'quarters':[{k:v for k,v in x.items() if k in ['period','usyc_performance_fees_usd','cctp_protocol_fees_usd','tracked_fees_share_ordinary_other'] } for x in quarters],'forward':forward},indent=2))
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
