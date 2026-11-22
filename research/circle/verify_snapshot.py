"""Run the published offline checks. No source download, Git push or scheduler activation."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--extended',action='store_true',help='Also run exploratory revenue, transaction, on-chain and RLDC checks')
parser.add_argument('--skip-manifest',action='store_true',help='Use only when rerunning in a clone whose generated receipts have already changed')
args=parser.parse_args()
node=shutil.which('node')
if not node:raise SystemExit('Node.js must be available on PATH for the dashboard checks')
if not args.skip_manifest:
    manifest=json.loads((ROOT/'FILE_MANIFEST.json').read_text())
    bad=[row['path'] for row in manifest['files'] if not (ROOT/row['path']).is_file() or hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()!=row['sha256']]
    if bad:raise SystemExit('Snapshot bytes differ from FILE_MANIFEST.json: '+', '.join(bad[:12]))
jobs=[
 ('report',[sys.executable,'reserve_report/verify.py'],ROOT),
 ('historical_javascript',[node,'reserve_report/verify_model.mjs'],ROOT),
 ('monitor_python',[sys.executable,'verify.py'],ROOT/'monitor'),
 ('monitor_javascript',[node,'verify_monitor.mjs'],ROOT/'monitor'),
 ('stage3_independent',[sys.executable,'stage3/verify_stage3.py'],ROOT),
]
if args.extended:
    jobs += [
      ('other_revenue',[sys.executable,'stage4/verify_stage4.py'],ROOT),
      ('transaction_revenue',[sys.executable,'stage4/transactions/verify.py'],ROOT),
      ('onchain_extensions',[sys.executable,'stage5/verify.py'],ROOT),
      ('rldc',[sys.executable,'stage5/rldc/verify.py'],ROOT),
    ]
results=[]
for name,command,cwd in jobs:
    started=time.monotonic()
    p=subprocess.run(command,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace')
    row={'name':name,'passed':p.returncode==0,'exit_code':p.returncode,'seconds':round(time.monotonic()-started,3),'stdout':p.stdout[-8000:],'stderr':p.stderr[-8000:]}
    results.append(row)
    print(json.dumps({'check':name,'passed':row['passed'],'seconds':row['seconds']}),flush=True)
record={'tested_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'passed':all(x['passed'] for x in results),'offline':True,'extended':args.extended,'checks':results,
        'interpretation':'These checks verify archived source integrity, arithmetic, parsers and system behavior. They are not prospective forecast-performance results.'}
(ROOT/'verification').mkdir(exist_ok=True)
(ROOT/'verification/public_run.json').write_text(json.dumps(record,indent=2)+'\n')
sys.exit(0 if record['passed'] else 1)
