"""Independently recompute fee bridges and inspect exported XLSX cached results."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics as st
import xml.etree.ElementTree as ET
import zipfile
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results';S4=ROOT.parent
m=json.loads((OUT/'transaction_backtest.json').read_text());ledger=json.loads((S4/'results/other_revenue_model.json').read_text())['ledger']
raw=json.loads((S4/'raw/llama_cctp_fee_history.json').read_text())['totalDataChart']
fee={dt.datetime.fromtimestamp(t,dt.timezone.utc).date():v/1e6 for t,v in raw}
tests=[]
def ck(n,x):tests.append({'name':n,'passed':bool(x)})
def close(a,b):return a is not None and abs(a-b)<1e-8
def quarter_fee(q):
    a=dt.date.fromisoformat(q['start']);b=dt.date.fromisoformat(q['end']);dates=[a+dt.timedelta(days=i) for i in range((b-a).days+1)]
    return sum(fee[d] for d in dates if d in fee),all(d in fee for d in dates)
for i,e in enumerate(m['late'],2):
    prev=m['quarters'][i-1];cur=m['quarters'][i]
    s=max((x for x in ledger if x['period']==prev['period'] and x['published_by']<=e['cutoff'] and 'transaction_revenue' in x['metrics']),key=lambda x:x['published_by'])
    lag=s['metrics']['transaction_revenue']['value'];now,complete=quarter_fee(cur);old,oldcomplete=quarter_fee(prev)
    ck(e['period']+' independent flat input',close(lag,e['methods']['prior_quarter_flat']))
    ck(e['period']+' independent current fee sum',close(now,e['current_cctp']))
    if complete and oldcomplete:
        expected=now+lag-old
        ck(e['period']+' independent fee bridge',close(expected,e['methods']['observed_cctp_plus_flat_residual']))
        ck(e['period']+' independent scaled fee bridge',close(now+(lag-old)*cur['days']/prev['days'],e['methods']['observed_cctp_plus_day_scaled_residual']))
    else:ck(e['period']+' incomplete history excluded','observed_cctp_plus_flat_residual' not in e['methods'])
for e in m['early']:
    if 'first30_cctp_plus_latest_public_residual' not in e['methods']:continue
    q=next(x for x in m['quarters'] if x['period']==e['period']);base=next(x for x in m['quarters'] if x['period']==e['base_period'])
    cutoff=dt.date.fromisoformat(e['cutoff']);a=dt.date.fromisoformat(q['start']);observed=sum(v for d,v in fee.items() if a<=d<=cutoff)
    old,_=quarter_fee(base);expected=observed*q['days']/30+(e['base_actual']-old)*q['days']/base['days']
    ck(e['period']+' independent early estimate',close(expected,e['methods']['first30_cctp_plus_latest_public_residual']))
    ck(e['period']+' early financial eligibility',e['base_public_by']<=e['cutoff'])
ck('first quarter absent fees preserved as missing',m['quarters'][0]['cctp']['sum_observed'] is None)
for name,s in m['late_common_metrics'].items():
    sample=[e for e in m['late'] if e['period'] in s['periods']]
    ck(name+' independently recomputed common MAPE',close(st.mean(abs(e['methods'][name]/e['actual']-1) for e in sample),s['mape']))

source_hashes={}
for p in [S4/'raw/llama_cctp_fee_history.json',S4/'raw/llama_cctp_adapter.txt',S4/'raw/llama_cctp_adapter_commit.json',S4/'results/other_revenue_model.json',S4.parent/'stage2/results/stage2_data_model.json']:
    source_hashes[str(p.relative_to(S4.parent))]=hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((S4/'source_manifest.json').read_text())
rec=next(x for x in manifest if x['name']=='llama_cctp_fee_history' and x['status']=='received')
ck('CCTP cached response matches original manifest hash',hashlib.sha256((S4/rec['file']).read_bytes()).hexdigest()==rec['sha256'])

book=S4.parent/'outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/Circle_Transaction_Revenue_Backtest.xlsx'
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(book) as z:
    rels={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheets={}
    for s in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns):
        target=rels[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        sheets[s.attrib['name']]={c.attrib['r']:c for c in ET.fromstring(z.read(target)).findall('.//s:sheetData/s:row/s:c',ns)}
    ck('saved workbook has three intended sheets',list(sheets)==['Transaction backtest','Quarter inputs','Daily CCTP'])
    ck('export contains no Excel error cells',not [(sn,addr) for sn,cells in sheets.items() for addr,c in cells.items() if c.attrib.get('t')=='e'])
    def value(sn,a):
        c=sheets[sn][a];v=c.findtext('s:v',namespaces=ns)
        return float(v) if v is not None and c.attrib.get('t') not in ['s','str','inlineStr'] else None
    for i,e in enumerate(m['late']):
        col='DEFGH'[i]
        ck(e['period']+' exported actual',close(value('Transaction backtest',col+'9'),e['actual']))
        for key,r in [('prior_quarter_flat',13),('observed_cctp_plus_flat_residual',17),('observed_cctp_plus_day_scaled_residual',21),('prior_quarter_day_scaled',25),('repeat_prior_growth',29)]:
            if key in e['methods']:
                ck(e['period']+' exported '+key,close(value('Transaction backtest',col+str(r)),e['methods'][key]))
    for i,key in enumerate(['prior_quarter_flat','prior_quarter_day_scaled','observed_cctp_plus_flat_residual','observed_cctp_plus_day_scaled_residual'],9):
        ck(key+' exported MAPE',close(value('Transaction backtest','M'+str(i)),m['late_common_metrics'][key]['mape']))
    for i,e in enumerate(m['early']):
        for key,r in [('latest_public_flat',49),('latest_public_day_scaled',57),('first30_cctp_plus_latest_public_residual',53)]:
            if key in e['methods']:ck(e['period']+' exported early '+key,close(value('Transaction backtest','DEFGH'[i]+str(r)),e['methods'][key]))

result={'as_of':'2026-11-21','checks_passed':sum(x['passed'] for x in tests),'checks_total':len(tests),'source_hashes':source_hashes,'workbook_sha256':hashlib.sha256(book.read_bytes()).hexdigest(),'native_excel_recalculation_tested':False,'checks':tests}
(OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ['checks','source_hashes']},indent=2))
assert all(x['passed'] for x in tests),[x for x in tests if not x['passed']]
