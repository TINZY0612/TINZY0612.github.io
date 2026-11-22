"""Three-factor subscription/services OLS using quarterly averages."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics as st
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
circle=ROOT.parent
ledger=json.loads((circle/'stage4/results/other_revenue_model.json').read_text())['ledger']
qs=json.loads((circle/'stage2/results/stage2_data_model.json').read_text())['quarters']
stable_file=circle/'stage4/transactions/raw/total_stablecoin_history.json'
stable_raw=json.loads(stable_file.read_text());usdc_raw=json.loads((ROOT/'raw/usdc_current_history.json').read_text())
def day(t):return dt.datetime.fromtimestamp(int(t),dt.timezone.utc).date()
stable={day(x['date']):sum(x['totalCirculatingUSD'].values()) for x in stable_raw}
usdc={day(x['date']):x['circulating']['peggedUSD'] for x in usdc_raw['tokens']}
btc={};checks=[]
def ck(name,v):checks.append({'name':name,'passed':bool(v)})
for q in qs:
    a=dt.date.fromisoformat(q['start']);b=dt.date.fromisoformat(q['end'])
    rows=json.loads((ROOT/'raw'/('btc_'+q['period']+'.json')).read_text())
    for row in rows:
        d=day(row[0])
        if not a<=d<=b:continue # Coinbase can include preceding/extra buckets.
        ck('valid BTC OHLC '+d.isoformat(),len(row)>=6 and row[1]<=row[4]<=row[2] and row[1]<=row[3]<=row[2])
        if d in btc:ck('overlap BTC values agree '+d.isoformat(),btc[d]==row[4])
        btc[d]=row[4]

daily=[];quarters=[]
for q in qs:
    a=dt.date.fromisoformat(q['start']);b=dt.date.fromisoformat(q['end'])
    dates=[a+dt.timedelta(days=i) for i in range((b-a).days+1)]
    ck(q['period']+' complete stablecoin/BTC/USDC daily coverage',all(d in stable and d in btc and d in usdc for d in dates))
    rows=[]
    for d in dates:
        x={'date':d.isoformat(),'period':q['period'],'stablecoin_usd':stable[d],'btc_usd_close':btc[d],'usdc_par_usd':usdc[d],'usdc_share':usdc[d]/stable[d]}
        ck('positive denominator and valid market share '+d.isoformat(),stable[d]>0 and 0<x['usdc_share']<1)
        rows.append(x);daily.append(x)
    entries=[e for e in ledger if e['period']==q['period'] and e['classification']=='current']
    chosen=min(entries,key=lambda e:e['published_by']) if q['period']=='2025Q1' else max(entries,key=lambda e:e['published_by'])
    quarters.append({'period':q['period'],'days':len(rows),'services_actual_usd_million':chosen['metrics']['subscription_services']['value'],
      'target_public_by':chosen['published_by'],'target_source_url':chosen['source_url'],
      'stablecoin_mean_usd_billion':st.mean(x['stablecoin_usd'] for x in rows)/1e9,
      'btc_mean_usd_thousand':st.mean(x['btc_usd_close'] for x in rows)/1000,
      'usdc_mean_share_pct':st.mean(x['usdc_share'] for x in rows)*100,
      'stablecoin_end_usd_billion':rows[-1]['stablecoin_usd']/1e9,'btc_end_usd':rows[-1]['btc_usd_close'],'usdc_end_share_pct':rows[-1]['usdc_share']*100})

def ols(y,x,labels):
    y=np.array(y,float);x=np.array(x,float);A=np.column_stack([np.ones(len(y)),x]);n,p=A.shape
    beta,_,rank,_=np.linalg.lstsq(A,y,rcond=None);fitted=A@beta;resid=y-fitted
    sse=float(resid@resid);tss=float(((y-y.mean())**2).sum());r2=1-sse/tss;df=n-p
    se=np.sqrt(np.diag(np.linalg.inv(A.T@A))*(sse/df)) if df>0 and rank==p else np.full(p,np.nan)
    vifs=[]
    for j in range(x.shape[1]):
        z=np.column_stack([np.ones(n),np.delete(x,j,axis=1)]);b=np.linalg.lstsq(z,x[:,j],rcond=None)[0]
        rr=1-float(((x[:,j]-z@b)**2).sum())/float(((x[:,j]-x[:,j].mean())**2).sum())
        vifs.append(1/(1-rr))
    loo=[]
    for i in range(n):
        mask=np.arange(n)!=i;bb=np.linalg.lstsq(A[mask],y[mask],rcond=None)[0]
        loo.append(float(A[i]@bb))
    press=float(((y-np.array(loo))**2).sum())
    z=(x-x.mean(axis=0))/x.std(axis=0,ddof=1)
    return {'n':n,'parameters_including_intercept':p,'rank':int(rank),'residual_degrees_of_freedom':df,
      'coefficients':[{'name':name,'coefficient':float(b),'standard_error':float(s)} for name,b,s in zip(['intercept']+labels,beta,se)],
      'r_squared':r2,'adjusted_r_squared':1-(1-r2)*(n-1)/df if df>0 else None,
      'in_sample_mape':float(np.mean(abs((fitted-y)/y))),
      'fitted':fitted.tolist(),'residuals':resid.tolist(),'loo_predictions':loo,'loo_mape':float(np.mean(abs((np.array(loo)-y)/y))),
      'loo_predictive_r_squared':1-press/tss,'negative_loo_predictions':sum(v<0 for v in loo),
      'predictor_correlation':np.corrcoef(x,rowvar=False).tolist(),'vif':[{'name':a,'vif':float(b)} for a,b in zip(labels,vifs)],
      'standardized_design_condition_number':float(np.linalg.cond(np.column_stack([np.ones(n),z]))),
      'sse':sse,'tss':tss,'interpretation':'In-sample association; leave-one-out is a small-sample diagnostic, not a forward-time validation.'}

labels=['stablecoin_mean_usd_billion','btc_mean_usd_thousand','usdc_mean_share_pct']
x=[[q[k] for k in labels] for q in quarters];y=[q['services_actual_usd_million'] for q in quarters]
primary=ols(y,x,labels)
later_y=y.copy();later_entry=max((e for e in ledger if e['period']=='2025Q1' and e['classification']=='current'),key=lambda e:e['published_by'])
later_y[0]=later_entry['metrics']['subscription_services']['value']
sensitivity=ols(later_y,x,labels)
changes=[]
for prev,q in zip(quarters,quarters[1:]):
    changes.append({'period':q['period'],'services_growth_pct':(q['services_actual_usd_million']/prev['services_actual_usd_million']-1)*100,
     'stablecoin_growth_pct':(q['stablecoin_mean_usd_billion']/prev['stablecoin_mean_usd_billion']-1)*100,
     'btc_mean_price_growth_pct':(q['btc_mean_usd_thousand']/prev['btc_mean_usd_thousand']-1)*100,
     'usdc_share_change_pp':q['usdc_mean_share_pct']-prev['usdc_mean_share_pct']})
cl=['stablecoin_growth_pct','btc_mean_price_growth_pct','usdc_share_change_pp']
change_model=ols([q['services_growth_pct'] for q in changes],[[q[k] for k in cl] for q in changes],cl)
lagged=ols(y[1:],x[:-1],labels)
ck('seven-quarter primary sample',primary['n']==7 and primary['residual_degrees_of_freedom']==3)
ck('full rank primary fit',primary['rank']==4)
ck('regression fitted plus residual equals target',all(abs(a+b-c)<1e-9 for a,b,c in zip(primary['fitted'],primary['residuals'],y)))
hashes={str(p.relative_to(circle)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [stable_file,ROOT/'raw/usdc_current_history.json',circle/'stage4/results/other_revenue_model.json']+list((ROOT/'raw').glob('btc_*.json'))}
result={'as_of':'2026-11-21','target':'Subscription and services revenue, USD millions; excludes ARC and transaction revenue',
 'definition':'Daily provider-date observations averaged by calendar quarter. USDC valued at $1 par. Stablecoin total sums all tracked totalCirculatingUSD peg categories; not Circle narrow fiat-backed market-share definition.',
 'quarterly_inputs':quarters,'daily_inputs':daily,'primary_levels_ols':primary,'changes_inputs':changes,'changes_ols':change_model,
 'lagged_levels_ols':lagged,'later_q1_target_sensitivity':{'q1_value':later_y[0],'q1_public_by':later_entry['published_by'],'model':sensitivity},
 'sources':{'stablecoin_total':'https://stablecoins.llama.fi/stablecoincharts/all','usdc':'https://stablecoins.llama.fi/stablecoin/2','btc':'https://api.exchange.coinbase.com/products/BTC-USD/candles','btc_documentation':'https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles'},
 'checks_passed':sum(z['passed'] for z in checks),'checks_total':len(checks),'checks':checks,'source_hashes':hashes,
 'limitations':['Only seven quarterly targets and three residual degrees of freedom','Coefficients and R2 are in-sample; no causal interpretation','Trending levels and correlated predictors can inflate apparent explanatory power','Current historical datasets are not archived vintages','LOO trains on future observations relative to the held-out quarter; it is not a deployable historical forecast','Later Q1 comparative changes category allocation; sensitivity disclosed','No p-values or reliable statistical-significance claim is made from this short sample']}
(OUT/'subscription_regression.json').write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf8')
print(json.dumps({'quarterly_inputs':quarters,'primary':{k:v for k,v in primary.items() if k not in ['fitted','residuals','loo_predictions']},'changes_r2':change_model['r_squared'],'changes_adjusted_r2':change_model['adjusted_r_squared'],'lagged_r2':lagged['r_squared'],'later_q1_r2':sensitivity['r_squared'],'checks':result['checks_passed']},indent=2))
assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
