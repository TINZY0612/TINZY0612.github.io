"""Verify exported Excel cached values without using an Excel authoring library."""
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
MODEL=json.loads((ROOT/'results/stage3_model.json').read_text())
WORKBOOK=ROOT.parent/'outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/Circle_Reserve_Income_Backtest.xlsx'
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
tests=[]
def check(name,ok,actual=None,expected=None):tests.append({'check':name,'passed':bool(ok),'actual':actual,'expected':expected})
with zipfile.ZipFile(WORKBOOK) as z:
    relations={r.attrib['Id']:r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
    sheets={}
    for s in ET.fromstring(z.read('xl/workbook.xml')).findall('s:sheets/s:sheet',ns):
        target=relations[s.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        name=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        cells={c.attrib['r']:c for c in ET.fromstring(z.read(name)).findall('.//s:sheetData/s:row/s:c',ns)}
        sheets[s.attrib['name']]=cells
    errors=[{'sheet':s,'cell':a,'value':c.findtext('s:v',namespaces=ns)} for s,cells in sheets.items() for a,c in cells.items() if c.attrib.get('t')=='e']
    check('export contains no Excel error cells',not errors,errors,[])
    def number(sheet,cell,expected):
        c=sheets[sheet][cell];raw=c.findtext('s:v',namespaces=ns)
        actual=float(raw) if raw is not None else None
        check(sheet+'!'+cell,actual is not None and abs(actual-expected)<1e-7,actual,expected)
    late=[r for r in MODEL['evaluations'] if r['phase']=='late'];early=[r for r in MODEL['evaluations'] if r['phase']=='early']
    methods=[('carry_forward',11,12),('lagged_implied_yield',14,15),('sofr',17,18),('treasury_3m',20,21),('sofr_lagged_spread',23,24),('fund_lagged_spread',26,27)]
    for i,(col,e) in enumerate(zip('DEFGHI',late)):
        number('Backtest',col+'9',e['actual_reserve_income'])
        for method,er,rr in methods:number('Backtest',col+str(er),e['estimates'][method]);number('Backtest',col+str(rr),e['errors'][method])
        number('Backtest',col+'30',early[i]['estimates']['fund_lagged_spread'])
        number('Backtest',col+'34',e['next_bucket_estimates_recalibrated_spreads']['sofr_lagged_spread'])
        for row,key in [(9,'reserve_estimate'),(10,'other_revenue_estimate'),(11,'total_revenue_estimate'),(13,'cost_ratio'),(19,'costs_estimate'),(20,'rldc_estimate'),(22,'actual_total_revenue'),(23,'total_revenue_error'),(25,'actual_rldc'),(26,'rldc_error')]:number('RLDC',col+str(row),e['rldc'][key])
        number('RLDC',col+'31',e['yield_25bp_income_effect'])
    for i,(method,_,_) in enumerate(methods):
        for col,key in [('L','mape'),('M','worst_abs_error'),('N','mae_million'),('O','wins_vs_carry')]:number('Backtest',col+str(i+8),MODEL['metrics']['late'][method][key])
    number('RLDC','D4',1)
    number('Source inputs','D4',0.005);number('Source inputs','G4',0.01)
result={'workbook':str(WORKBOOK),'checks_passed':sum(r['passed'] for r in tests),'checks_total':len(tests),'checks':tests,'native_excel_recalculation_tested':False}
(ROOT/'results/export_validation.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
assert all(r['passed'] for r in tests),[r for r in tests if not r['passed']]
