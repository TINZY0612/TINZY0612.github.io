"""Cache new public partner disclosures; never overwrite dated raw responses."""
import datetime as dt,hashlib,json,urllib.request
from pathlib import Path
from lxml import html
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parent;RAW=ROOT/'raw';RAW.mkdir(exist_ok=True)
MAN=ROOT/'source_manifest.json';records=json.loads(MAN.read_text()) if MAN.exists() else []
jobs=[
 ('coin_submissions','https://data.sec.gov/submissions/CIK0001679788.json'),
 ('coin_2025Q1','https://www.sec.gov/Archives/edgar/data/1679788/000167978825000088/q125shareholderletter.htm'),
 ('coin_2025Q2','https://www.sec.gov/Archives/edgar/data/1679788/000167978825000153/q225shareholderletter.htm'),
 ('coin_2025Q3','https://www.sec.gov/Archives/edgar/data/1679788/000167978825000207/q325shareholderletter.htm'),
 ('coin_2026Q2','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000087/q226earningsdeck_sec.htm'),
 ('coin_2026Q3','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000121/q326earningsdeck_vsec.htm'),
 ('coin_2026Q1_pdf','https://s27.q4cdn.com/397450999/files/doc_financials/2026/q1/v3/Q1-26-Earnings-Deck.pdf'),
 ('coin_quarterly','https://investor.coinbase.com/financials/quarterly-results/default.aspx'),
 ('coin_2025Q4_index_v2','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000011/0001679788-26-000011-index.html'),
 ('coin_2026Q1_index_v2','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000053/0001679788-26-000053-index.html'),
 ('coin_2026Q2_slide40','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000087/q226earningsdeck_sec040.jpg'),
 ('coin_2026Q3_slide36','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000121/q326earningsdeck_vsec036.jpg'),
 ('coin_2025Q4','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000011/q425shareholderletter.htm'),
 ('coin_2026Q1_original','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000053/q126earningsdeck-finalse.htm'),
 ('collaboration_agreement','https://www.sec.gov/Archives/edgar/data/1876042/000119312525070481/d737521dex101.htm'),
 ('ecosystem_agreement','https://www.sec.gov/Archives/edgar/data/1876042/000119312525070481/d737521dex102.htm'),
 ('coin_2026Q1_slide38','https://www.sec.gov/Archives/edgar/data/1679788/000167978826000053/q126earningsdeck-finalse038.jpg')]
for name,url in jobs:
    old=next((r for r in records if r['name']==name and r.get('status')=='received'),None)
    if old:continue
    record={'name':name,'url':url,'retrieved_at_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'CircleAcademicResearch/0.8 PublicFinancialResearch','Accept':'*/*'})
        with urllib.request.urlopen(req,timeout=25) as r:b=r.read();record.update(http_status=r.status,final_url=r.url)
        suffix='.pdf' if b.startswith(b'%PDF') else '.jpg' if b[:2]==b'\xff\xd8' else '.json' if b[:1] in [b'{',b'['] else '.html';p=RAW/(name+suffix);p.write_bytes(b)
        record.update(status='received',file=str(p.relative_to(ROOT)),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
    except Exception as e:record.update(status='failed',error=str(e))
    records.append(record);MAN.write_text(json.dumps(records,indent=2),encoding='utf8');print(json.dumps(record),flush=True)
for r in records:
    if r.get('status')!='received':continue
    p=ROOT/r['file']
    if p.suffix=='.html':
        tree=html.fromstring(p.read_bytes());text=' '.join(tree.text_content().split())
    elif p.suffix=='.pdf':text='\n'.join(f'\n--- PDF PAGE {i+1} ---\n'+(page.extract_text() or '') for i,page in enumerate(PdfReader(p).pages))
    else:continue
    (ROOT/'extracted'/(r['name']+'.txt')).write_text(text,encoding='utf8')
    if r['name']=='coin_quarterly':
        print('DISCOVERED PDF LINKS',[(a.text_content().strip(),a.get('href')) for a in tree.xpath('//a[@href]') if any(k in a.get('href','').lower() for k in ['2025','2026'])][:25],flush=True)
    if '_index' in r['name']:
        print(r['name'],'EXHIBITS',[(a.text_content().strip(),a.get('href')) for a in tree.xpath('//a[@href]') if '99' in a.text_content() or 'earnings' in a.get('href','').lower() or 'shareholder' in a.get('href','').lower()],flush=True)
