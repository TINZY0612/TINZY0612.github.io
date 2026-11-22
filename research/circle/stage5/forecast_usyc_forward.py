"""Record a genuine forward Q4 USYC fee-component scenario as of November 21."""
import datetime as dt
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
source=ROOT.parent/'stage4/raw/usyc_historical_prices.json'
rows=json.loads(source.read_text())['data'];reports=[]
for r in rows:
    d=dt.datetime.fromtimestamp(int(r['timestamp']),dt.timezone.utc).date()
    reports.append({'date':d,'round':int(r['roundId']),'fee':D(r['fee'])*D(r['price']),
      'gross':D(r['interest'])+D(r.get('embeddedIncome','0')),'aum':D(r['totalSupply'])*D(r['price'])})
reports.sort(key=lambda r:r['date']);last=reports[-1]
assert max(r['round'] for r in reports)-min(r['round'] for r in reports)+1==len(reports)
assert last['date']==dt.date(2026,11,20)
trailing_start=last['date']-dt.timedelta(days=27);trailing=[r for r in reports if trailing_start<=r['date']<=last['date']]
known=[r for r in reports if dt.date(2026,10,1)<=r['date']<=last['date']]
known_fee=sum(r['fee'] for r in known);remaining=(dt.date(2026,12,31)-last['date']).days
pace=sum(r['fee'] for r in trailing)/D(28)
mean_aum=sum(r['aum'] for r in trailing)/D(len(trailing))
gross=sum(r['gross'] for r in trailing)
implied_yield=gross/mean_aum*D(365)/D(28)
pred1=known_fee+pace*remaining
pred2=known_fee+last['aum']*implied_yield*D('.1')*D(remaining)/D(365)
record={'as_of':'2026-11-21','period':'2026Q4','actual':None,'scope':'USYC performance-fee component only; not total subscription/services or net profit',
 'last_report_date':last['date'].isoformat(),'known_q4_reports':len(known),'known_q4_fees_usd_million':float(known_fee/D(1e6)),
 'remaining_calendar_days':remaining,'trailing_calendar_days':28,'trailing_start':trailing_start.isoformat(),'trailing_report_count':len(trailing),
 'trailing_mean_report_aum_usd_million':float(mean_aum/D(1e6)),'last_report_aum_usd_million':float(last['aum']/D(1e6)),
 'trailing_implied_gross_annual_yield':float(implied_yield),'assumed_performance_fee_fraction':.1,
 'flat_trailing_daily_fee_q4_estimate_usd_million':float(pred1/D(1e6)),
 'flat_last_aum_and_trailing_yield_q4_estimate_usd_million':float(pred2/D(1e6)),
 'method':'Known Q4 fee observations plus an explicit remaining-period projection; second case fixes NAV at latest reported value and gross yield at trailing observed rate.',
 'limitations':['Historical source is a current issuer API snapshot, not archived intraday vintage','Price-report dates may differ from economic accrual and company revenue-recognition timing','Future NAV, yields, fee terms and redemptions can change','Not a forecast for undisclosed integration, maintenance or license contracts','Does not revise the earlier total other-revenue forecast or the separate ARC scenario'],
 'source_url':'https://usyc.hashnote.com/api/price-reports','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(ROOT/'results/usyc_forward_build_inputs.json').write_text(json.dumps({'known_fee_usd_million':float(known_fee/D(1e6)),
 'trailing_fee_usd_million':float(sum(r['fee'] for r in trailing)/D(1e6)),
 'trailing_gross_income_usd_million':float(gross/D(1e6)),'trailing_mean_aum_usd_million':float(mean_aum/D(1e6)),
 'last_aum_usd_million':float(last['aum']/D(1e6)),'remaining_calendar_days':remaining,'trailing_calendar_days':28,'fee_fraction':.1,'annual_day_basis':365},indent=2),encoding='utf8')
p=ROOT/'results/2026-11-21_Q4_USYC_fee_forecast.json'
if p.exists():assert json.loads(p.read_text())==record,'Use a separately dated forecast for new information.'
else:p.write_text(json.dumps(record,indent=2),encoding='utf8')
print(json.dumps(record,indent=2))
