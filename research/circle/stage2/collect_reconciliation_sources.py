"""Download original reserve checkpoints and Q4 release, preserving stage one."""
import concurrent.futures
import hashlib
import json
import lxml.html
from collect_stage2 import ROOT,RAW,fetch

if __name__=='__main__':
 doc=lxml.html.fromstring((ROOT.parent/'feasibility/raw/circle_transparency.html').read_bytes())
 jobs=[]
 for year,month in [('2025','March'),('2025','June'),('2025','September'),('2025','December'),('2026','March')]:
  links=[e.get('href') for e in doc.xpath('//a[@href]') if '/USDCAttestationReports/' in e.get('href','') and year in e.get('href','') and month in e.get('href','')]
  if len(links)!=1: raise ValueError((year,month,links))
  jobs.append((f'attestation_{year}_{month}',links[0]))
 jobs.append(('q4_2025_release','https://www.circle.com/pressroom/circle-reports-fourth-quarter-and-full-fiscal-year-2025-financial-results'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: records=list(pool.map(lambda j:fetch(*j),jobs))
 # The shared downloader preserves PDF bytes even though its generic suffix is txt.
 for r in records:
  if r.get('file') and (ROOT/r['file']).read_bytes().startswith(b'%PDF'):
   old=ROOT/r['file']; new=old.with_suffix('.pdf'); old.rename(new); r['file']=str(new.relative_to(ROOT))
 (ROOT/'reconciliation_sources_manifest.json').write_text(json.dumps(records,indent=2),encoding='utf8')
