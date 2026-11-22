"""Confirm the six public-company release dates from original Item 2.02 filings."""
import concurrent.futures
import json
import lxml.html
from collect_stage2 import ROOT,RAW,fetch

if __name__=='__main__':
 recent=json.loads((RAW/'sec_submissions.json').read_text())['filings']['recent']
 selected=[]
 for i,form in enumerate(recent['form']):
  if form=='8-K' and '2.02' in recent['items'][i]:
   acc=recent['accessionNumber'][i];date=recent['filingDate'][i]
   selected.append({'date':date,'acceptance_datetime':recent['acceptanceDateTime'][i],'accession':acc,
    'url':f"https://www.sec.gov/Archives/edgar/data/1876042/{acc.replace('-','')}/{recent['primaryDocument'][i]}"})
 selected.sort(key=lambda x:x['date'])
 expected=['2025Q2','2025Q3','2025Q4','2026Q1','2026Q2','2026Q3']
 if len(selected)!=6:raise ValueError('Release list changed; inspect the report periods before mapping.')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  records=list(pool.map(lambda x:fetch('earnings_'+x['date'].replace('-','_'),x['url']),selected))
 for period,selected_row,record in zip(expected,selected,records):
  selected_row.update(period=period,download=record)
  if record['status']=='received':
   text=' '.join(lxml.html.fromstring((ROOT/record['file']).read_bytes()).text_content().split())
   pos=text.find('Item 2.02')
   selected_row['item_202_excerpt']=text[pos:pos+1500]
   print(json.dumps({'period':period,'release_date':selected_row['date'],'excerpt':selected_row['item_202_excerpt'][:850]}),flush=True)
 (ROOT/'earnings_calendar.json').write_text(json.dumps(selected,indent=2),encoding='utf8')
