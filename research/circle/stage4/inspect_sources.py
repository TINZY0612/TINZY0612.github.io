"""Extract bounded research locators from saved sources; no accounting forecasts."""
import datetime as dt
import json
from pathlib import Path
import re
import lxml.html
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
results={}
for name in ['q1_2026_release','q2_2026_release','q3_2026_release','arc_mainnet_announcement','arc_whitepaper_library','may_2026_8k']:
    p=ROOT/'raw'/(name+'.html')
    if not p.exists():continue
    doc=lxml.html.fromstring(p.read_bytes());text=' '.join(' '.join(doc.itertext()).split())
    excerpts=[]
    for term in ['ARC','presale','recogniz','75%','guidance','reclassified']:
        for hit in list(re.finditer(re.escape(term),text,re.I))[:12]:
            excerpts.append({'term':term,'offset':hit.start(),'text':text[max(0,hit.start()-150):hit.start()+900]})
    links=[{'text':a.text_content().strip()[:100],'url':a.get('href')} for a in doc.xpath('//a[@href]') if any(k in a.get('href').lower() for k in ['whitepaper','pdf','earnings','transcript','token'])]
    results[name]={'excerpts':excerpts,'links':links}
for name in ['q3_2026_transcript','q2_2026_transcript','arc_whitepaper']:
    p=ROOT/'raw'/(name+'.pdf')
    if not p.exists():continue
    reader=PdfReader(p);pages=[{'page':i+1,'text':' '.join((p.extract_text() or '').split())} for i,p in enumerate(reader.pages)]
    (OUT/(name+'_text.txt')).write_text('\n\n'.join('PAGE '+str(p['page'])+'\n'+p['text'] for p in pages),encoding='utf8')
    results[name]={'page_count':len(pages),'relevant_pages':[p for p in pages if any(k in p['text'].lower() for k in ['presale','181.8','recogniz','75%','contract address'])]}
for name in ['arc_rpc_circle','arc_rpc_drpc','arc_rpc_quicknode']:
    p=ROOT/'raw'/(name+'.json')
    if p.exists():results[name]=json.loads(p.read_text())
p=ROOT/'raw/arc_node_genesis.txt'
if p.exists():
    g=json.loads(p.read_text())
    results['genesis']={'chain_id':g['config']['chainId'],'timestamp':dt.datetime.fromtimestamp(int(g['timestamp'],16),dt.timezone.utc).isoformat(),'allocated_accounts':len(g['alloc'])}
(OUT/'source_extracts.json').write_text(json.dumps(results,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in results.items() if k.startswith('arc_rpc') or k=='genesis'},indent=2))
for name in ['arc_whitepaper_library','q1_2026_release','q2_2026_release','q3_2026_release']:
    if name in results:print(name,'LINKS',json.dumps(results[name]['links'])[:4500])
