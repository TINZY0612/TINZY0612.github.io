"""Independent saved-output arithmetic, chronology and source-integrity checks."""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import statistics
from lxml import html
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'
read=lambda n:json.loads((OUT/n).read_text())
m=read('other_revenue_model.json');f=read('product_fee_analysis.json');c=read('arc_chain_check.json')
checks=[]
def ck(name,ok):checks.append({'name':name,'passed':bool(ok)})
def close(x,y):return math.isclose(x,y,rel_tol=1e-10,abs_tol=1e-8)
quarters=['2025Q1','2025Q2','2025Q3','2025Q4','2026Q1','2026Q2','2026Q3']
for e in m['forecasts']:
    ix=quarters.index(e['period']);prev=quarters[ix-1]
    eligible=[x for x in m['ledger'] if x['period']==prev and x['published_by']<=e['cutoff']]
    lag=max(eligible,key=lambda x:x['published_by'])
    previous=sum(x['value'] for x in lag['metrics'].values())
    ck(e['period']+' independently recomputed flat forecast',close(previous,e['methods']['flat_prior_total']))
    if ix>=2:
        eligible2=[x for x in m['ledger'] if x['period']==quarters[ix-2] and x['published_by']<=e['cutoff']]
        if eligible2:
            lag2=max(eligible2,key=lambda x:x['published_by']);v2=sum(x['value'] for x in lag2['metrics'].values())
            ck(e['period']+' independently recomputed growth forecast',close(previous**2/v2,e['methods']['repeat_prior_total_growth']))
    for method,prediction in e['methods'].items():
        ck(e['period']+' '+method+' error recomputed',close(prediction/e['actual_other_revenue']-1,e['errors'][method]))
for method,metric in m['baseline_metrics'].items():
    errors=[abs(e['methods'][method]/e['actual_other_revenue']-1) for e in m['forecasts'] if method in e['methods']]
    ck(method+' MAPE independently recomputed',close(statistics.mean(errors),metric['mape']) and len(errors)==metric['n'])
for row in m['arc_q3_scenarios']:
    ck(row['arc_case']+' '+row['ordinary_method']+' total recomputed',close(row['ordinary_estimate']+row['arc_estimate'],row['total_other_revenue_estimate']))
    ck(row['arc_case']+' '+row['ordinary_method']+' error recomputed',close(row['total_other_revenue_estimate']/row['actual_other_revenue']-1,row['error']))
non_arc=sum(abs(e['methods']['flat_prior_total']/(e['actual_other_revenue']-(181.8 if e['period']=='2026Q3' else 0))-1) for e in m['forecasts'])/6
ck('ordinary non-ARC flat MAPE',close(non_arc,0.19941046840709906))
forward=f['q4_guidance_based_forecast']
ytd=sum(e['actual_other_revenue'] for e in m['forecasts'] if e['period'].startswith('2026'))
ck('forward total-guidance range recomputed',close(310-ytd,forward['implied_q4_total_other_low']) and close(330-ytd,forward['implied_q4_total_other_high']))
ck('forward outcome remains unknown',forward['actual'] is None)
ck('remaining ARC is not automatically Q4 revenue',forward['incremental_arc_base_case']==0 and close(forward['remaining_existing_arc_consideration_approx'],242.2-181.8))

timeline=read('arc_evidence_timeline.json')
for e in timeline['events']:
    ck(e['evidence'][:70]+' eligibility',e['q3_pre_earnings_eligible']==(e['public_by']<=timeline['historical_cutoff']))
ck('mint completion announcement eligible before earnings',any(e['public_by']=='2026-09-16' and 'mint' in e['evidence'] and e['q3_pre_earnings_eligible'] for e in timeline['events']))
ck('exact mint date separately kept as outcome disclosure',any(e['public_by']=='2026-11-04' and 'Exact September 14' in e['evidence'] and not e['q3_pre_earnings_eligible'] for e in timeline['events']))
launch=' '.join(html.fromstring((ROOT/'raw/arc_mainnet_launch_release.html').read_bytes()).text_content().split()).lower()
ck('saved launch source discloses mint and public-launch distinction','completed the genesis mint' in launch and '10 billion' in launch and 'not a commitment to publicly launch' in launch)
index=' '.join(html.fromstring((ROOT/'raw/july_2026_arc_8k_index.html').read_bytes()).text_content().split())
ck('second closing July 2 publication verified against index','Filing Date 2026-07-02' in index)
call=' '.join(PdfReader(ROOT/'raw/q2_2026_transcript.pdf').pages[8].extract_text().split())
ck('annual ARC guide is present on original Q2 call page 9','75%' in call and '$180 million' in call and '2026' in call)
ck('ARC issuer authentication remains unresolved',c['authenticated_arc_token_address'] is None)
ck('all saved chain controls pass',all(x['passed'] for x in c['checks']))
ck('all saved product controls pass',all(x['passed'] for x in f['checks']))

fee_rows=[]
for row in f['quarterly_fee_observations']:
    for key,file in [('usyc_performance_fees','llama_usyc_revenue_history.json'),('cctp_protocol_fees','llama_cctp_fee_history.json')]:
        raw=json.loads((ROOT/'raw'/file).read_text())
        values=[v for t,v in raw['totalDataChart'] if (d:=dt.datetime.fromtimestamp(int(t),dt.timezone.utc)).year==int(row['period'][:4]) and (d.month-1)//3+1==int(row['period'][-1])]
        ck(row['period']+' '+key+' independent sum',close(sum(values),row[key+'_usd']))
    fee_rows.append(row['tracked_fees_usd'])
ck('USYC fee source uses manager revenue rather than gross yield',json.loads((ROOT/'raw/llama_usyc_revenue_history.json').read_text())['totalDataChart']!=json.loads((ROOT/'raw/llama_usyc_fee_history.json').read_text())['totalDataChart'])

manifest=json.loads((ROOT/'source_manifest.json').read_text());unique={}
for r in manifest:
    if r.get('status')=='received':
        p=(ROOT/r['file']).resolve()
        ck('manifest path remains inside stage4 '+r['file'],p.is_relative_to(ROOT.resolve()))
        ck('source hash '+r['file'],hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'])
        unique[str(p)]=r['sha256']
dependencies={}
for p in [ROOT.parent/'stage2/results/stage2_data_model.json',ROOT.parent/'stage3/results/stage3_model.json']+list((ROOT.parent/'stage2/raw').glob('*.html')):
    dependencies[str(p.relative_to(ROOT.parent))]=hashlib.sha256(p.read_bytes()).hexdigest()
out={'as_of':'2026-11-21','checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'unique_hashed_public_files':len(unique),'dependency_hashes':dependencies,'ordinary_non_arc_flat_mape':non_arc,'checks':checks}
(OUT/'stage4_verification.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in out.items() if k not in ['checks','dependency_hashes']},indent=2))
assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
