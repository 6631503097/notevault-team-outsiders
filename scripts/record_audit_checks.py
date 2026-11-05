"""Record independently executed report checks without replacing student baseline evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--python',default=str(ROOT/'.venv/bin/python'))
p.add_argument('--lab-python',default=str(ROOT/'.lab-venv/bin/python'))
p.add_argument('--frontend-root',default='frontend')
p.add_argument('--resume',action='store_true')
a=p.parse_args()
OUT=ROOT/'evidence/audit';OUT.mkdir(parents=True,exist_ok=True)
records=json.loads((OUT/'execution-journal.json').read_text())['records'] if a.resume and (OUT/'execution-journal.json').exists() else []
source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()

def run(label,command,outputs=(),expected=0):
    if a.resume and any(r['check']==label and r['passed'] for r in records):
        return
    started=datetime.now(timezone.utc).isoformat()
    r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    attempt=1+sum(v['check']==label for v in records)
    log=OUT/(label+('' if attempt==1 else '-attempt'+str(attempt))+'.log');log.write_text(r.stdout+r.stderr)
    ok=(r.returncode==expected) if expected is not None else (r.returncode!=0 and 'signature' in (r.stdout+r.stderr).lower())
    files=[log]+[ROOT/name for name in outputs]
    row={'check':label,'command':command,'source_head':source,'started_at':started,'finished_at':datetime.now(timezone.utc).isoformat(),'exit_code':r.returncode,'expected_exit':expected if expected is not None else 'nonzero signature rejection','passed':ok,'outputs':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files if f.is_file()}}
    records.append(row)
    (OUT/'execution-journal.json').write_text(json.dumps({'executor':'Codex assistant; not student contribution evidence','records':records},indent=2)+'\n')
    print(label+': '+('PASS' if ok else 'FAIL'),flush=True)
    if not ok:raise SystemExit('Check failed; see '+str(log))

run('baseline',[a.lab_python,'scripts/reproduce_baseline.py','--output','evidence/audit/baseline.json'],['evidence/audit/baseline.json'])
run('backend',[a.python,'-m','pytest','-q','tests','--junitxml=evidence/audit/regression.xml'],['evidence/audit/regression.xml'])
run('frontend-tests',['npm','--prefix',a.frontend_root,'test','--','--run'])
run('frontend-build',['npm','--prefix',a.frontend_root,'run','build'])
artifact=ROOT/'release/team-outsiders-notevault.tar.gz'
command=['cosign','verify-blob','--key',str(ROOT/'release/cosign.pub'),'--bundle',str(ROOT/'release/release.sigstore.json'),'--insecure-ignore-tlog']
run('signature',command+[str(artifact)])
with tempfile.TemporaryDirectory(prefix='outsiders-audit-tamper-') as temp:
    changed=Path(temp)/'tampered.tar.gz';changed.write_bytes(artifact.read_bytes()+b'audit tamper probe')
    run('tamper-rejection',command+[str(changed)],expected=None)
print('Audit checks completed; signed artifact SHA-256: '+hashlib.sha256(artifact.read_bytes()).hexdigest())
