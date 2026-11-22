"""Extract auditable quarterly actuals and quantify the supply-definition gap.

The authoritative model is JSON. The Excel builder reads this model and links
each financial input or derivation to its original source observation.
"""
from __future__ import annotations
import datetime as dt
import json
from pathlib import Path
import re
import statistics
import lxml.html
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
RAW=ROOT/'raw'
OUT=ROOT/'results'
OUT.mkdir(exist_ok=True)
UTC=dt.timezone.utc
FLOW_LABELS={
 'reserve_income':['Reserve income'],
 'other_revenue':['Other revenue'],
 'total_revenue':['Total revenue and reserve income','Total revenue and reserve income from continuing operations'],
 'distribution_transaction_costs':['Distribution and transaction costs'],
 'other_costs':['Other costs'],
 'total_costs':['Total distribution, transaction and other costs','Total distribution, transaction, and other costs'],
}
KPI_LABELS={
 'usdc_end':['USDC in circulation, end of period'],
 'usdc_average':['USDC in circulation, average of period','Average USDC in circulation'],
 'reserve_return':['Reserve return rate'],
 'platform_weight':['USDC on platform, daily weighted-average percentage','Daily weighted-average percentage of USDC on platform'],
}
QUARTERS=[('2025Q1','2025-01-01','2025-03-31','ipo_prospectus'),('2025Q2','2025-04-01','2025-06-30','q2_2025_html'),
 ('2025Q3','2025-07-01','2025-09-30','q3_2025_html'),('2025Q4','2025-10-01','2025-12-31','fy2025_html'),
 ('2026Q1','2026-01-01','2026-03-31','q1_2026_html'),('2026Q2','2026-04-01','2026-06-30','q2_2026_html'),
 ('2026Q3','2026-07-01','2026-09-30','q3_2026_html')]

def write(name,obj):
 (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False),encoding='utf8')

def load_rows(path):
 doc=lxml.html.fromstring(path.read_bytes()); rows=[]
 for i,tr in enumerate(doc.xpath('//tr')):
  cells=[' '.join(' '.join(c.itertext()).split()) for c in tr.xpath('./td')]
  if not cells:continue
  label=re.sub(r'\s*\(\s*\d+\s*\)\s*$','',cells[0]).strip()
  nums=[]
  for cell in cells[1:]:
   if re.fullmatch(r'\d[\d,]*(?:\.\d+)?',cell):nums.append(float(cell.replace(',','')))
   elif re.fullmatch(r'\(\d[\d,]*(?:\.\d+)?\)',cell):nums.append(-float(cell.strip('()').replace(',','')))
  if nums:rows.append({'label':label,'numbers':nums,'html_tr_index':i,'cells':cells})
 return rows

def pick(rows,labels,index=0,flow=False):
 matches=[r for r in rows if r['label'] in labels and len(r['numbers'])>index]
 if flow and any('Total revenue' in x for x in labels):matches=[r for r in matches if r['numbers'][0]>100000]
 if not matches:raise KeyError((labels,index))
 return matches[0]

def main():
 manifests=json.loads((ROOT/'source_manifest.json').read_text())
 manifests+=json.loads((ROOT/'reconciliation_sources_manifest.json').read_text())
 manifests+=json.loads((ROOT/'release_images_manifest.json').read_text())
 sources={r['name']:r for r in manifests if r['status']=='received'}
 submissions=json.loads((RAW/'sec_submissions.json').read_text())['filings']['recent']
 filing_dates={submissions['primaryDocument'][i]:submissions['filingDate'][i] for i in range(len(submissions['form']))}
 source_files={'fy2025_html':'crcl-20251231.htm','q2_2025_html':'crcl-20250630.htm','q3_2025_html':'crcl-20250930.htm',
  'q1_2026_html':'crcl-20260331.htm','q2_2026_html':'crcl-20260630.htm','q3_2026_html':'crcl-20260930.htm','ipo_prospectus':'d737521d424b4.htm'}
 tables={name:load_rows(ROOT/sources[name]['file']) for name in source_files}
 checks=[]; observations=[]
 def check(name,passed,detail=None):checks.append({'check':name,'passed':bool(passed),'detail':detail})
 def obs(metric,period,value,unit,source,locator,source_value=None,source_unit=None,precision=None,published=None,note=''):
  record={'id':f'O{len(observations)+1:03d}','metric':metric,'period':period,'value':value,'unit':unit,
   'source_name':source,'source_url':sources[source]['url'] if source in sources else source,
   'source_file':sources[source].get('file') if source in sources else '',
   'published_by':published or filing_dates.get(source_files.get(source,'')),
   'locator':locator,'source_value':source_value if source_value is not None else value,
   'source_unit':source_unit or unit,'source_precision':precision,'note':note}
  observations.append(record);return record
 def extract_flow(source,metric,period,index=0):
  row=pick(tables[source],FLOW_LABELS[metric],index,True)
  val=row['numbers'][index]
  return obs(metric,period,val/1000,'USD million',source,f"HTML table row {row['html_tr_index']}: {row['label']}; numeric column {index+1}",val,'USD thousand',0.001)
 def extract_kpi(source,metric,period,index=0,note=''):
  row=pick(tables[source],KPI_LABELS[metric],index)
  val=row['numbers'][index];is_rate=metric in ['reserve_return','platform_weight']
  return obs(metric,period,val/100 if is_rate else val,'decimal' if is_rate else 'USDC million',source,
   f"HTML table row {row['html_tr_index']}: {row['label']}; numeric column {index+1}",val,'percent' if is_rate else 'USD million',0.001 if is_rate else 1,note=note)

 # Preserve both source periods needed for Q4 flow derivations.
 controls={}
 for period,source,index in [('2025FY','fy2025_html',0),('2025YTD9','q3_2025_html',2)]:
  controls[period]={m:extract_flow(source,m,period,index) for m in FLOW_LABELS}
 periods=[]
 for key,start,end,source in QUARTERS:
  q={'period':key,'start':start,'end':end,'days':(dt.date.fromisoformat(end)-dt.date.fromisoformat(start)).days+1,'metrics':{}}
  for metric in FLOW_LABELS:
   if key=='2025Q4':
    annual=controls['2025FY'][metric]; ytd=controls['2025YTD9'][metric]
    q['metrics'][metric]={'value':annual['value']-ytd['value'],'basis':'derived FY minus 9M',
     'operation':'subtract','input_ids':[annual['id'],ytd['id']],'unit':'USD million','published_by':annual['published_by']}
   else:
    r=extract_flow(source,metric,key)
    q['metrics'][metric]={'value':r['value'],'basis':'reported','input_ids':[r['id']],'unit':r['unit'],'published_by':r['published_by']}
  for metric in KPI_LABELS:
   if key=='2025Q4' and metric in ['usdc_average','reserve_return','platform_weight']:
    values={'usdc_average':(76.2,76200,'USDC million',100),'reserve_return':(3.8,0.038,'decimal',0.001),'platform_weight':(17.8,0.178,'decimal',0.001)}
    original,value,unit,precision=values[metric]
    r=obs(metric,key,value,unit,'q4_kpi_image2','Operating indicators image, Q4 2025 column; visually verified',original,
     'USD billion' if metric=='usdc_average' else 'percent',precision,published='2026-02-25',
     note='Average circulation is reported to USD 0.1 billion; do not imply million-level precision.' if metric=='usdc_average' else '')
   else:
    try:r=extract_kpi(source,metric,key)
    except KeyError:
     if key!='2025Q1':raise
     r=extract_kpi('q1_2026_html',metric,key,1,note='Later comparative. Earlier original publication of this KPI has not been established; do not use as a Q2 2025 forecast input.')
   q['metrics'][metric]={'value':r['value'],'basis':'reported; later comparative' if r['note'].startswith('Later') else 'reported',
    'input_ids':[r['id']],'unit':r['unit'],'published_by':r['published_by'],'precision':r['source_precision'],'note':r['note']}
  m=q['metrics']
  rldc=m['total_revenue']['value']-m['total_costs']['value']
  m['rldc']={'value':rldc,'basis':'calculated revenue less total costs','unit':'USD million'}
  m['rldc_margin']={'value':rldc/m['total_revenue']['value'],'basis':'calculated','unit':'decimal'}
  m['reserve_income_share']={'value':m['reserve_income']['value']/m['total_revenue']['value'],'basis':'calculated','unit':'decimal'}
  m['cost_ratio_to_reserve_income']={'value':m['total_costs']['value']/m['reserve_income']['value'],'basis':'calculated','unit':'decimal'}
  check(key+' revenue bridge',abs(m['reserve_income']['value']+m['other_revenue']['value']-m['total_revenue']['value'])<=0.002)
  check(key+' cost bridge',abs(m['distribution_transaction_costs']['value']+m['other_costs']['value']-m['total_costs']['value'])<=0.002)
  periods.append(q)
 for metric in FLOW_LABELS:
  check('FY2025 reconciles to four quarters: '+metric,abs(sum(q['metrics'][metric]['value'] for q in periods[:4])-controls['2025FY'][metric]['value'])<=0.002)
 # Independently check later comparative disclosures against original quarters.
 comparisons=[]
 for target,source,index in [('2025Q1','q1_2026_html',1),('2025Q2','q2_2026_html',1),('2025Q3','q3_2026_html',1)]:
  q=next(p for p in periods if p['period']==target)
  for metric in FLOW_LABELS:
   row=pick(tables[source],FLOW_LABELS[metric],index,True); later=row['numbers'][index]/1000
   gap=later-q['metrics'][metric]['value']; comparisons.append({'period':target,'metric':metric,'gap_usd_million':gap,'later_source':source})
   check(target+' original vs later comparative: '+metric,abs(gap)<=0.002)

 vendor=[]
 for name,field in [('circle_quarterly_revenue_period_fq','Total Revenue'),('circle_fundamentals_quarterly','Revenue from Business Activities - Total')]:
  rows=json.loads((ROOT/'licensed'/f'{name}.json').read_text())['data']
  for q in periods:
   matches=[r for r in rows if r['Date'][:10]==q['end']]
   good=len(matches)==1 and matches[0].get(field) is not None
   gap=matches[0][field]/1e6-q['metrics']['total_revenue']['value'] if good else None
   vendor.append({'period':q['period'],'query':name,'observations':len(matches),'gap_usd_million':gap,'matched':good and abs(gap)<=0.002})
   check(q['period']+' Workspace revenue check '+name,good and abs(gap)<=0.002)

 calendar=json.loads((ROOT/'earnings_calendar.json').read_text())
 for entry in calendar:
  q=next(p for p in periods if p['period']==entry['period'])
  end_date=dt.date.fromisoformat(q['end'])
  expected_text=end_date.strftime('%B')+f' {end_date.day}, {end_date.year}'
  check(q['period']+' original earnings filing identifies period',expected_text in entry.get('item_202_excerpt',''))
  check(q['period']+' earnings follows quarter end',entry['date']>q['end'])
  r=obs('earnings_release_date',q['period'],entry['date'],'date',entry['url'],'Original Form 8-K, Item 2.02',published=entry['date'],
        note='Original filing states the press-release date. Intraday press-release timestamp is not established here.')
  q['earnings_release_date']=entry['date'];q['earnings_release_input_id']=r['id']

 # Official reserve checkpoints. Large-number table order is checked against the
 # filing stock metric; exact component arithmetic is tested separately for Sep26.
 checkpoint_files={
  '2025-03-31':RAW/'attestation_2025_March.pdf','2025-06-30':RAW/'attestation_2025_June.pdf',
  '2025-09-30':RAW/'attestation_2025_September.pdf','2025-12-31':RAW/'attestation_2025_December.pdf',
  '2026-03-31':RAW/'attestation_2026_March.pdf',
  '2026-06-30':ROOT.parent/'feasibility/raw/attestation_2026_June.pdf',
  '2026-09-30':ROOT.parent/'feasibility/raw/attestation_2026_September.pdf'}
 llama=json.loads((ROOT.parent/'feasibility/raw/defillama_usdc.json').read_text())
 bydate={dt.datetime.fromtimestamp(int(v['date']),UTC).date():v for v in llama['tokens']}
 supply=[]; native_rows=[]
 for q in periods:
  end=dt.date.fromisoformat(q['end']); pdf=checkpoint_files[q['end']]
  reader=PdfReader(pdf); text=' '.join((reader.pages[1].extract_text() or '').split())
  nums=[int(x.replace(',','')) for x in re.findall(r'\d{1,3}(?:,\d{3})+',text)]
  circ,assets=nums[1],nums[3]
  check(q['period']+' official circulation vs filing stock',abs(circ/1e6-q['metrics']['usdc_end']['value'])<=0.5)
  same=bydate[end]['circulating']['peggedUSD']; following=bydate[end+dt.timedelta(days=1)]['circulating']['peggedUSD']
  days=[dt.date.fromisoformat(q['start'])+dt.timedelta(days=i) for i in range(q['days'])]
  check(q['period']+' daily supply coverage',all(d in bydate and d+dt.timedelta(days=1) in bydate for d in days))
  avg=statistics.mean(bydate[d]['circulating']['peggedUSD'] for d in days)
  avgnext=statistics.mean(bydate[d+dt.timedelta(days=1)]['circulating']['peggedUSD'] for d in days)
  supply.append({'period':q['period'],'end':q['end'],'official_circulation':circ,'official_reserve_assets':assets,
   'source_pdf':str(pdf.relative_to(ROOT.parent)),'source_pdf_page':2,'provider_same_date_bucket':same,
   'provider_following_date_bucket':following,'following_bucket_gap':following-circ,'following_bucket_gap_pct':following/circ-1,
   'provider_average_as_labeled':avg,'provider_average_next_date':avgnext,
   'reported_average_million':q['metrics']['usdc_average']['value'],
   'average_gap_pct':avg/(q['metrics']['usdc_average']['value']*1e6)-1,'materiality_flag':abs(following/circ-1)>0.001,
   'timing_note':'Daily bucket observation time is not proven to be UTC midnight or end of day.'})
  for metric,native_value in [('attested_circulation',circ),('reserve_assets',assets),('provider_same_date_bucket',same),('provider_following_date_bucket',following)]:
   value=native_value/1e6
   if metric.startswith('provider'):
    r=obs(metric,q['period'],value,'USDC million','https://stablecoins.llama.fi/stablecoin/2',
     f"Global tokens, date bucket {end if metric=='provider_same_date_bucket' else end+dt.timedelta(days=1)}",source_value=native_value,source_unit='USDC tokens',precision=0.000001,
     note='Provider daily bucket, not verified exact EOD state.')
   else:
    source=next((s for s,v in sources.items() if v.get('file') and (ROOT/v['file']).resolve()==pdf.resolve()),None)
    if not source:
     old=json.loads((ROOT.parent/'feasibility/checkpoint_manifest.json').read_text())['sources']
     match=next(r for r in old if r.get('file') and (ROOT.parent/'feasibility'/r['file']).resolve()==pdf.resolve())
     source=match['url']
    r=obs(metric,q['period'],value,'USD million' if metric=='reserve_assets' else 'USDC million',source,'Reserve report PDF page 2; month-end column',source_value=native_value,source_unit='USD' if metric=='reserve_assets' else 'USDC tokens',precision=0.000001,
     note='Signature date and historical first-publication timestamp not established by this extraction.')
   supply[-1].setdefault('input_ids',{})[metric]=r['id']

 # Aggregate decomposition of all chain fields at the Oct 1 daily bucket. The
 # API's minted category is not asserted to equal Circle's raw approved supply.
 stamp=1790812800; minted=0;unreleased=0;chaincirc=0
 for chain,obj in llama['chainBalances'].items():
  r=next((t for t in obj['tokens'] if int(t['date'])==stamp),None)
  if r is None:continue
  value=lambda field:r.get(field,{}).get('peggedUSD',0) if isinstance(r.get(field),dict) else 0
  a,b,c=value('minted'),value('unreleased'),value('circulating')
  minted+=a;unreleased+=b;chaincirc+=c
  native_rows.append({'chain':chain,'api_minted':a,'api_unreleased':b,'api_circulating':c,
    'minted_field_present':isinstance(r.get('minted'),dict),'unreleased_field_present':isinstance(r.get('unreleased'),dict)})
 att=json.loads((ROOT.parent/'feasibility/results/feasibility_summary.json').read_text())['attestation_reconciliation']
 global_value=bydate[dt.date(2026,10,1)]['circulating']['peggedUSD']
 residual=chaincirc-(minted-unreleased)
 parts=[('API minted minus Circle raw approved supply',minted-att['raw_approved_chain_supply']),
        ('Effect of different unreleased versus allowed-not-issued totals',att['tokens_allowed_but_not_issued']-unreleased),
        ('Circle access-denied exclusion',att['access_denied_tokens']),('Circle pending-burn exclusion',att['gateway_pending_burns']),
        ('API chain aggregation residual after minted less unreleased',residual),('API global versus chain sum rounding',global_value-chaincirc)]
 check('Supply aggregate decomposition arithmetic',abs(sum(v for _,v in parts)-(global_value-att['circulation']))<=1)
 decomposition={'date_bucket':'2026-10-01','official_period_end':'2026-09-30','api_minted_sum':minted,'api_unreleased_sum':unreleased,
  'api_circulating_chain_sum':chaincirc,'api_global_circulation':global_value,'official_raw_approved_supply':att['raw_approved_chain_supply'],
  'official_allowed_not_issued':att['tokens_allowed_but_not_issued'],'official_access_denied':att['access_denied_tokens'],
  'official_pending_burns':att['gateway_pending_burns'],'official_circulation':att['circulation'],
  'components':[{'component':k,'tokens':v} for k,v in parts],
  'qualification':'Exact algebraic decomposition of different snapshots and definitions. Component differences are not proven causal corrections, and the residual is not asserted to be entirely bridge error.'}
 official_ids={}
 september_source='https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2026/2026%20USDC_Examination%20Report%20September%2026.pdf'
 for metric,key in [('official_raw_supply','raw_approved_chain_supply'),('official_allowed_not_issued','tokens_allowed_but_not_issued'),
                    ('official_access_denied','access_denied_tokens'),('official_pending_burns','gateway_pending_burns')]:
  r=obs(metric,'2026Q3',att[key]/1e6,'USDC million',september_source,'September reserve report PDF page 2, criterion A',
        source_value=att[key],source_unit='USDC tokens',precision=0.000001)
  official_ids[metric]=r['id']
 decomposition['official_input_ids']=official_ids
 check('Quarter keys unique',len({q['period'] for q in periods})==len(periods))
 check('Observation ids unique',len({o['id'] for o in observations})==len(observations))
 model={'as_of_date':'2026-11-21','display_financial_unit':'USD million','supply_materiality_threshold':0.001,
  'quarters':periods,'source_observations':observations,'annual_controls':controls,
  'comparative_checks':comparisons,'workspace_crosschecks':vendor,'supply_checkpoints':supply,
  'supply_decomposition':decomposition,'chain_field_inventory':native_rows,
  'checks':checks,'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),
  'limitations':['Daily provider timestamps identify buckets, not exact EOD states.','Q4 average circulation is rounded to USD 0.1 billion.',
   'Q1 2025 reserve return and platform weight use later comparatives and are ineligible for an earlier forecast until earlier disclosure is found.',
   'Algebraic gap decomposition does not fully reconcile economic supply definitions or source observation times.',
   'The six earnings-release calendar dates are verified in original Item 2.02 filings. Intraday first-publication timestamps are not established.']}
 write('stage2_data_model.json',model)
 write('quarterly_actuals.json',periods)
 write('supply_reconciliation.json',{'checkpoints':supply,'decomposition':decomposition,'chain_fields':native_rows})
 write('validation_checks.json',checks)
 print(json.dumps({'quarters':[{q['period']:{k:q['metrics'][k]['value'] for k in ['reserve_income','other_revenue','total_revenue','total_costs','rldc','usdc_average']}} for q in periods],
  'checks_passed':model['checks_passed'],'checks_total':model['checks_total'],'supply_gaps_pct':{s['period']:100*s['following_bucket_gap_pct'] for s in supply},'decomposition':decomposition},indent=2))
 failed=[x for x in checks if not x['passed']]
 if failed:raise AssertionError(json.dumps(failed,indent=2))

if __name__=='__main__':main()
