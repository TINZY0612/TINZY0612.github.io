"""Publication-filtered Circle cost/RLDC comparison; eight fixed rules."""
import datetime as dt,hashlib,json,re,statistics as st
from pathlib import Path
from lxml import html
ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parents[1];OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf8')
core=read(CIRCLE/'stage2/results/stage2_data_model.json');s3=read(CIRCLE/'stage3/results/stage3_model.json');qs=core['quarters'];checks=[]
def ck(n,v):checks.append({'name':n,'passed':bool(v)})
manifest=read(ROOT/'source_manifest.json');sources={r['name']:r for r in manifest if r.get('status')=='received'}
sub=read(ROOT/'raw/coin_submissions.json')['filings']['recent'];dates_by_accession={a.replace('-',''):sub['filingDate'][i] for i,a in enumerate(sub['accessionNumber'])}
def text(n):return (ROOT/'extracted'/(n+'.txt')).read_text(encoding='utf8')
def source(n):return sources[n]['url']
partner=[]
names=['coin_2025Q1','coin_2025Q2','coin_2025Q3','coin_2025Q4','coin_2026Q1_original','coin_2026Q2','coin_2026Q3']
for q,n in zip(qs,names):
    t=text(n);accession=source(n).split('/')[-2];published=dates_by_accession[accession];quarter=q['period']
    if quarter.startswith('2025'):
        tree=html.fromstring((ROOT/sources[n]['file']).read_bytes());matches=[]
        for idx,tr in enumerate(tree.xpath('//tr')):
            cells=[' '.join(c.text_content().split()) for c in tr.xpath('./td')]
            if cells and cells[0]=='Stablecoin revenue':
                nums=[float(c.replace(',','')) for c in cells[1:] if re.fullmatch(r'[\d,]+(?:\.\d+)?',c)]
                if len(nums)>=5:matches.append((idx,nums))
        assert matches;idx,nums=matches[0];gross=nums[4]
        loc=f'Original shareholder letter HTML table row {idx}; Stablecoin revenue, current-quarter column (fifth quarterly number)'
        if quarter=='2025Q1':bal,total=12.3,54.;bal_note='Narrative precise product balance; rounded market-cap table'
        elif quarter=='2025Q2':bal,total=13.8,61.;bal_note='Narrative precise product balance; rounded market-cap table'
        elif quarter=='2025Q3':bal,total=15.,68.;bal_note='Original narrative and rounded market-cap table'
        else:bal,total=17.8,76.2;bal_note='Original narrative: product balance 17.8; total average cap 76.2'
    else:
        section=t[t.find('USDC Balances & Revenue'):];m=re.search(r'Total\s+((?:\d+(?:\.\d+)?\s+){10})',section);assert m,n
        vals=[float(x) for x in m.group(1).split()];total,gross=vals[4],vals[9]
        bal={'2026Q1':19.,'2026Q2':20.,'2026Q3':22.}[quarter]
        loc='Original SEC earnings exhibit; USDC Balances & Revenue; Total current quarter: combined stablecoin and corporate-balance USDC income; slide '+{'2026Q1':'38','2026Q2':'40','2026Q3':'36'}[quarter]
        bal_note='Rounded original presentation values; eligible product definition is not just labeled on-chain exchange wallets'
    ck(quarter+' original Coinbase filing precedes Circle release',published<q.get('earnings_release_date',q['metrics']['reserve_income']['published_by']))
    partner.append({'period':quarter,'published_by':published,'gross_usdc_income_million':gross,'product_balance_billion':bal,'total_average_usdc_billion':total,'product_share':bal/total,
      'source_name':n,'source_url':source(n),'source_file':sources[n]['file'],'locator':loc,'balance_precision_note':bal_note,'definition':'Before 2026: original stablecoin revenue includes corporate-balance USDC income. 2026: combined USDC total explicitly includes corporate-balance income.'})
save('coinbase_inputs.json',partner)

# The direct Circle-to-Coinbase ledger is diagnostic. Rounded/changed annual
# disclosures are not silently treated as an exact quarterly cost target.
circle_man={r['name']:r for r in read(CIRCLE/'stage2/source_manifest.json') if r.get('status')=='received'}
cb=[]
def add(period,value,pub,name,locator,kind='reported_rounded'):
    cb.append({'period':period,'value_usd_million':value,'published_by':pub,'source_url':circle_man[name]['url'],'source_file':'stage2/'+circle_man[name]['file'],'locator':locator,'kind':kind})
add('2025Q1',298.8,'2025-06-05','ipo_prospectus','MD&A distribution costs, quarter ended March 31, 2025')
add('2025H1',630.6,'2025-08-12','q2_2025_html','MD&A distribution costs, six months ended June 30, 2025')
add('2025Q2',331.8,'2025-08-12','q2_2025_html','630.6 H1 less previously public Q1 298.8; approximate','derived_from_public_cumulative')
add('2025M9',989.1,'2025-11-12','q3_2025_html','MD&A distribution costs, nine months ended September 30, 2025')
add('2025Q3',358.5,'2025-11-12','q3_2025_html','989.1 M9 less previously public H1 630.6; approximate','derived_from_public_cumulative')
add('2025FY',1362.9,'2026-03-09','fy2025_html','2024 comparative cost 924.5 plus disclosed annual increase 438.4; approximate','derived_from_reported_change')
add('2025Q4',373.8,'2026-03-09','fy2025_html','1362.9 annual reconstruction less previously public M9 989.1; not an exact same-vintage quarter','cross_vintage_cumulative_difference')
add('2025Q1',303.2,'2026-05-11','q1_2026_html','Later comparative, quarter ended March 31, 2025')
add('2026Q1',330.6,'2026-05-11','q1_2026_html','Current quarter ended March 31, 2026')
add('2025H1',635.5,'2026-08-05','q2_2026_html','Later comparative, six months ended June 30, 2025')
add('2025Q2',332.3,'2026-08-05','q2_2026_html','Later comparative, quarter ended June 30, 2025')
add('2026Q2',324.6,'2026-08-05','q2_2026_html','Current quarter ended June 30, 2026')
add('2026H1',655.3,'2026-08-05','q2_2026_html','Current six months ended June 30, 2026; rounded quarterly sum 655.2 differs by 0.1')
add('2025M9',996.8,'2026-11-04','q3_2026_html','Later comparative, nine months ended September 30, 2025')
add('2025Q3',361.3,'2026-11-04','q3_2026_html','Later comparative, quarter ended September 30, 2025')
add('2026Q3',331.3,'2026-11-04','q3_2026_html','Current quarter ended September 30, 2026')
save('circle_coinbase_cost_ledger.json',cb)

methods={
 'flat_cost':'Previous-quarter total costs held flat',
 'lag_ratio':'Latest cost / reserve-income ratio',
 'pool3_ratio':'Up-to-three-quarter pooled cost / reserve ratio',
 'ewma_ratio':'Cost / reserve ratios, fixed 0.5 exponential decay',
 'platform_change':'Latest ratio plus half the change in Coinbase product share',
 'partner_scaled_residual':'Current Coinbase gross USDC income plus reserve-scaled lag residual',
 'partner_total_scale':'Prior total costs scaled by current/prior Coinbase gross USDC income',
 'partner_flat_residual':'Current Coinbase gross USDC income plus flat lag dollar residual'}
early_methods=['flat_cost','lag_ratio','pool3_ratio','ewma_ratio'];late_methods=list(methods)

def estimates(i,R,history,part):
    prev=history[-1];lastR=prev['metrics']['reserve_income']['value'];lastC=prev['metrics']['total_costs']['value'];ratios=[h['metrics']['total_costs']['value']/h['metrics']['reserve_income']['value'] for h in history]
    weights=[.5**j for j in reversed(range(len(ratios)))];tail=history[-3:]
    out={'flat_cost':lastC,'lag_ratio':R*lastC/lastR,'pool3_ratio':R*sum(h['metrics']['total_costs']['value'] for h in tail)/sum(h['metrics']['reserve_income']['value'] for h in tail),'ewma_ratio':R*sum(a*w for a,w in zip(ratios,weights))/sum(weights)}
    p,lp=part[i],part[i-1];residual=lastC-lp['gross_usdc_income_million']
    out.update(platform_change=R*(lastC/lastR+.5*(p['product_share']-lp['product_share'])),partner_scaled_residual=p['gross_usdc_income_million']+residual*R/lastR,partner_total_scale=lastC*p['gross_usdc_income_million']/lp['gross_usdc_income_million'],partner_flat_residual=p['gross_usdc_income_million']+residual)
    return out,{'prior_reserve':lastR,'prior_costs':lastC,'last_ratio':lastC/lastR,'pool3_ratio':out['pool3_ratio']/R,'ewma_ratio':out['ewma_ratio']/R,'prior_partner_income':lp['gross_usdc_income_million'],'current_partner_income':p['gross_usdc_income_million'],'prior_partner_share':lp['product_share'],'current_partner_share':p['product_share'],'lag_residual':residual,'pool_periods':[h['period'] for h in tail]}

evaluations=[]
for i,q in enumerate(qs):
    if i==0:continue
    original=next(x for x in s3['evaluations'] if x['period']==q['period'] and x['phase']=='late');R=original['estimates']['sofr_lagged_spread'];cut=original['cutoff'];precut=(dt.date.fromisoformat(partner[i]['published_by'])-dt.timedelta(days=1)).isoformat()
    history=[h for h in qs[:i] if all(h['metrics'][k]['published_by']<=precut for k in ['reserve_income','total_costs','other_revenue'])]
    ck(q['period']+' all prior calibration figures public before partner cutoff',len(history)==i)
    ck(q['period']+' current partner publication eligible only for late nowcast',precut<partner[i]['published_by']<=cut)
    pred,drivers=estimates(i,R,history,partner);prev=history[-1];O=prev['metrics']['other_revenue']['value'];m=q['metrics'];actualC=m['total_costs']['value'];actualR=m['reserve_income']['value'];actualO=m['other_revenue']['value'];actualRLDC=m['rldc']['value']
    arc_actual=181.8 if q['period']=='2026Q3' else 0.;arc_scenario=180. if q['period']=='2026Q3' else 0.
    evaluations.append({'period':q['period'],'pre_partner_cutoff':precut,'late_cutoff':cut,'reserve_estimate':R,'reserve_actual':actualR,'other_estimate':O,'actual_other':actualO,'actual_cost':actualC,'actual_rldc':actualRLDC,'actual_arc_recognition_for_scoring_only':arc_actual,'annual_arc_guidance_timing_scenario':arc_scenario,
      'underlying_actual_rldc_for_scoring':actualRLDC-arc_actual,'drivers':drivers,'partner':partner[i],
      'calibration_public_by':{h['period']:max(h['metrics'][k]['published_by'] for k in ['reserve_income','total_costs','other_revenue']) for h in history},
      'predictions':{name:{'cost':C,'cost_error':C/actualC-1,'rldc':R+O-C,'rldc_error':(R+O-C)/actualRLDC-1,'underlying_rldc_error':(R+O-C)/(actualRLDC-arc_actual)-1,'arc_scenario_rldc':R+O+arc_scenario-C,'arc_scenario_rldc_error':(R+O+arc_scenario-C)/actualRLDC-1,'actual_revenue_cost_only_rldc':actualR+actualO-C,'cost_only_rldc_error':(actualR+actualO-C)/actualRLDC-1,'timing_class':'pre-partner eligible' if name in early_methods else 'late partner-dependent'} for name,C in pred.items()}})
    for name,C in pred.items():ck(q['period']+' '+name+' finite nonnegative cost and bridge',C>=0 and abs((R+O-C)+C-(R+O))<1e-8)

def metrics(rows,name):
    p=[r['predictions'][name] for r in rows]
    return {'n':len(rows),'cost_mape':st.mean(abs(x['cost_error']) for x in p),'cost_mae_million':st.mean(abs(x['cost']-r['actual_cost']) for x,r in zip(p,rows)),'cost_worst_abs_error':max(abs(x['cost_error']) for x in p),'cost_bias':st.mean(x['cost_error'] for x in p),'rldc_mape':st.mean(abs(x['rldc_error']) for x in p),'underlying_rldc_mape':st.mean(abs(x['underlying_rldc_error']) for x in p),'arc_scenario_rldc_mape':st.mean(abs(x['arc_scenario_rldc_error']) for x in p),'cost_only_rldc_mape':st.mean(abs(x['cost_only_rldc_error']) for x in p)}
summary={n:metrics(evaluations,n) for n in methods}
later={n:metrics(evaluations[-2:],n) for n in methods};earlier={n:metrics(evaluations[:4],n) for n in methods}
ck('old Stage3 lag-ratio RLDC outputs reproduced',all(abs(r['predictions']['lag_ratio']['rldc']-next(x for x in s3['evaluations'] if x['period']==r['period'] and x['phase']=='late')['rldc']['rldc_estimate'])<1e-8 for r in evaluations))
result={'as_of':'2026-11-21','units':'USD million, errors as decimal fractions','methods':methods,'pre_partner_methods':early_methods,'evaluations':evaluations,'metrics':summary,'first_four_retrospective_metrics':earlier,'last_two_retrospective_metrics':later,
 'limitations':['Six scored quarters; outcomes viewed before protocol, no blind holdout','Historical supply/rate sources are current vintages','Coinbase gross USDC income is a proxy, not an exact payable to Circle','Partner-dependent methods are unavailable before Coinbase reports','The platform rule assumes unchanged Circle share and residual economics; current Circle platform mix is not known','Underlying RLDC and actual-revenue cost-only results use actual revenue for scoring/diagnostics, not as forecast inputs','Approximately 180m ARC Q3 timing is a conditional allocation of pre-release annual guidance, not a verified quarter recognition amount','No model is validated solely by lowest error in six observations'],
 'checks':checks}
save('method_comparison.json',result)
print(json.dumps({'method_metrics':summary,'last_two_cost_mape':{n:m['cost_mape'] for n,m in later.items()},'checks':[sum(c['passed'] for c in checks),len(checks)],'quarterly':[{k:r[k] for k in ['period','actual_cost','reserve_estimate']}|{'costs':{n:round(p['cost'],3) for n,p in r['predictions'].items()}} for r in evaluations]},indent=2))
assert all(c['passed'] for c in checks)
