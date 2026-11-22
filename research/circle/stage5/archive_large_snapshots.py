"""Losslessly compress generated large RPC snapshots after collection is finished."""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent;MAN=ROOT/'source_manifest.json'
records=json.loads(MAN.read_text());archived=[]
def sha(p,gz=False):
    h=hashlib.sha256()
    with (gzip.open(p,'rb') if gz else p.open('rb')) as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
paths=[p for p in (ROOT/'raw').glob('*.json') if p.stat().st_size>2_000_000 and p.name.startswith(('usdc_flow_','cctp_'))]
paths += [ROOT/'results'/n for n in ['usdc_q3_2026_mint_burn_logs.json','ethereum_cctp_q3_fee_logs.json','ethereum_cctp_q3_routes.json'] if (ROOT/'results'/n).exists()]
for p in paths:
    p=p.resolve();assert p.is_relative_to(ROOT.resolve()) and p.is_file()
    original_sha=sha(p);size=p.stat().st_size;z=Path(str(p)+'.gz')
    with p.open('rb') as source,gzip.open(z,'wb',compresslevel=3) as target:shutil.copyfileobj(source,target,1024*1024)
    assert sha(z,True)==original_sha,'Lossless compression verification failed'
    for rec in records:
        if rec.get('file')==str(p.relative_to(ROOT)):
            assert rec['sha256']==original_sha,'Original source manifest hash differs'
            rec.update(file=str(z.relative_to(ROOT)),compression='gzip',stored_bytes=z.stat().st_size)
    archived.append({'file':str(z.relative_to(ROOT)),'original_bytes':size,'stored_bytes':z.stat().st_size,'uncompressed_sha256':original_sha})
    p.unlink() # Only the verified generated file inside this stage is replaced.
MAN.write_text(json.dumps(records,indent=2),encoding='utf8')
(ROOT/'results/archive_manifest.json').write_text(json.dumps({'format':'gzip; original response SHA-256 retained in source manifest','files':archived},indent=2),encoding='utf8')
print(json.dumps({'files_compressed':len(archived),'before_mb':sum(x['original_bytes'] for x in archived)/1e6,'after_mb':sum(x['stored_bytes'] for x in archived)/1e6}))
