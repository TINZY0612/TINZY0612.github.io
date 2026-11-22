"""Independent verification of costs, publication cutoffs, forward daily build and XLSX."""
import contextlib,copy,datetime as dt,hashlib,io,json,runpy,statistics as st,zipfile
from pathlib import Path
from lxml import html
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parents[1];OUT=ROOT/'results';checks=[]
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def ck(n,x):checks.append({'name':n,'passed':bool(x)})
def near(a,b,t=1e-8):return abs(a-b)<t
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=read(OUT/'method_comparison.json');q=read(CIRCLE/'stage2/results/stage2_data_model.json')['quarters'];p=read(OUT/'coinbase_inputs.json');f=read(OUT/'2026-11-21_Q4_RLDC_forecast.json');d=read(OUT/'q4_daily_build_inputs.json')
manifest=read(ROOT/'source_manifest.json');ok=[r for r in manifest if r.get('status')=='received']
ck('all received source response hashes verified',all(sha(ROOT/r['file'])==r['sha256'] for r in ok))
ck('dated forecast source input hashes unchanged',all(sha(CIRCLE/name)==value for name,value in f['source_hashes'].items()))
ck('seven original partner dates and six scored quarters',len(p)==7 and len(m['evaluations'])==6)
for j,r in enumerate(m['evaluations'],1):
    hist=q[max(0,j-3):j];ratio=sum(h['metrics']['total_costs']['value'] for h in hist)/sum(h['metrics']['reserve_income']['value'] for h in hist);estimate=r['reserve_estimate']*ratio
    ck(r['period']+' independent pooled-ratio estimate',near(estimate,r['predictions']['pool3_ratio']['cost']))
    ck(r['period']+' calibration was public before partner report',all(v<=r['pre_partner_cutoff'] for v in r['calibration_public_by'].values()))
    ck(r['period']+' partner original publication eligible for late cutoff',r['pre_partner_cutoff']<p[j]['published_by']<=r['late_cutoff'])
    ck(r['period']+' original Stage3 reserve estimate preserved',near(r['reserve_estimate'],next(x for x in read(CIRCLE/'stage3/results/stage3_model.json')['evaluations'] if x['period']==r['period'] and x['phase']=='late')['estimates']['sofr_lagged_spread']))
    for name,x in r['predictions'].items():
        ck(r['period']+' '+name+' bridge and error',near(x['rldc'],r['reserve_estimate']+r['other_estimate']-x['cost']) and near(x['cost_error'],x['cost']/r['actual_cost']-1))
for name,metric in m['metrics'].items():
    ck(name+' aggregate cost and underlying errors recomputed',near(metric['cost_mape'],st.mean(abs(r['predictions'][name]['cost']/r['actual_cost']-1) for r in m['evaluations'])) and near(metric['underlying_rldc_mape'],st.mean(abs(r['predictions'][name]['rldc']/r['underlying_actual_rldc_for_scoring']-1) for r in m['evaluations'])) )

# Exercise the actual prediction routine with target financials changed. Such
# changes may affect scoring but must never alter that quarter's predictions.
with contextlib.redirect_stdout(io.StringIO()):env=runpy.run_path(str(ROOT/'analyze.py'))
for j in [1,3,6]:
    R=m['evaluations'][j-1]['reserve_estimate'];history=env['qs'][:j];before,_=env['estimates'](j,R,history,env['partner']);saved=copy.deepcopy(env['qs'][j]['metrics'])
    for k in ['reserve_income','total_costs','other_revenue']:env['qs'][j]['metrics'][k]['value']*=3
    after,_=env['estimates'](j,R,history,env['partner']);env['qs'][j]['metrics']=saved
    ck(q[j]['period']+' target actual mutation leaves predictions unchanged',before==after)
saved=copy.deepcopy(env['partner'][6]);R=m['evaluations'][-1]['reserve_estimate'];before,_=env['estimates'](6,R,env['qs'][:6],env['partner']);env['partner'][6]['gross_usdc_income_million']+=10;after,_=env['estimates'](6,R,env['qs'][:6],env['partner']);env['partner'][6]=saved
ck('current partner income cannot change pre-partner rules',all(near(before[n],after[n]) for n in m['pre_partner_methods']))
ck('current partner income changes intended late proxy rule',near(after['partner_scaled_residual']-before['partner_scaled_residual'],10))

cal=[r for r in d['rows'] if r['role']=='Calibration'];forecast=[r for r in d['rows'] if r['role']=='Forecast'];cut=f['observed_supply_through']
ck('184 distinct quarter-role dates with 51 observed and 41 projected Q4 days',len(cal)==92 and len(forecast)==92 and len({r['date'] for r in d['rows']})==184 and sum(r['observed_supply_million'] is not None for r in forecast)==51)
S=[r['observed_supply_million'] if r['date']<=cut else f['last_observed_usdc_million'] for r in forecast];Y=[r['available_sofr'] if r['date']<=cut else f['last_available_sofr'] for r in forecast]
spread=f['lag_reserve_income']/f['lag_reported_average_usdc_million']*365/92-sum(r['observed_supply_million']*r['available_sofr'] for r in cal)/sum(r['observed_supply_million'] for r in cal)*365/360
R=sum(s*y/360 for s,y in zip(S,Y))+sum(S)*spread/365
ck('daily forward reserve arithmetic matches immutable forecast',near(R,f['reserve_income_forecast']))
rd={r['effectiveDate']:r['percentRate']/100 for r in read(CIRCLE/'feasibility/raw/nyfed_sofr_2023_2026.json')['refRates']};dates=sorted(rd);published=[e for j,e in enumerate(dates[:-1]) if dates[j+1]<=f['as_of']]
ck('future SOFR uses only a published effective date',near(rd[published[-1]],f['last_available_sofr']))
ratio=sum(x['cost'] for x in f['cost_calibration_rows'][-3:])/sum(x['reserve'] for x in f['cost_calibration_rows'][-3:]);C=R*ratio;under=R+25.464-C
ck('Q4 pooled ratio and both RLDC cases independently reconcile',near(C,f['estimates']['pool3_ratio']['total_costs']) and near(under,f['estimates']['pool3_ratio']['underlying_rldc']) and near(under+60.4,f['estimates']['pool3_ratio']['rldc_including_arc']))
ck('forecast keeps actual unknown and future partner earnings unavailable',f['actual'] is None and f['selected_method']=='pool3_ratio')

book=CIRCLE/'outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/Circle_RLDC_Projection.xlsx';ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
with zipfile.ZipFile(book) as z:
    sheetnames=sorted(n for n in z.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml'));trees=[ET.fromstring(z.read(n)) for n in sheetnames]
    ck('four exported sheets and no cached error cells',len(trees)==4 and not any(c.attrib.get('t')=='e' for t in trees for c in t.findall('.//s:c',ns)))
    cells=[{c.attrib['r']:c for c in t.findall('.//s:c',ns)} for t in trees]
    value=lambda c:float(c.find('s:v',ns).text)
    ck('exported cost MAPE and Q4 RLDC cache match analysis',near(value(cells[0]['D11']),m['metrics']['pool3_ratio']['cost_mape']) and near(value(cells[0]['E38']),f['estimates']['pool3_ratio']['rldc_including_arc']))
    ck('exported forecast and cost estimates contain live formulas',all(cells[0][a].find('s:f',ns) is not None for a in ['E26','E32','E35','E36','E38']) and cells[1]['D24'].find('s:f',ns) is not None)
    charts=[n for n in z.namelist() if '/charts/chart' in n and n.endswith('.xml')];ct=ET.fromstring(z.read(charts[0])) if charts else None
    ck('native chart has two source-bound series',len(charts)==1 and len(ct.findall('.//c:ser',ns))==2 and all(ser.find('.//c:f',ns) is not None for ser in ct.findall('.//c:ser',ns)))
qa=read(OUT/'workbook_qa.json');ck('workbook input changes and zero-ARC test passed',all(x['passed'] for x in qa['checks']) and 'matched 0 entries' in qa['formula_error_scan'])
result={'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'received_source_hashes_checked':len(ok),'workbook_sha256':sha(book),'native_excel_application_recalculation_tested':False,'interpretation':'Controls verify source integrity, calculations and input separation, not future predictive accuracy.'}
(OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps({k:result[k] for k in ['checks_passed','checks_total','received_source_hashes_checked']},indent=2));assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
