"""Run the release-code gate. Any tool error or finding fails closed."""
import json
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
commands=[
    [sys.executable,'-m','bandit','-r','backend','-lll','-ii','-f','json','-o','evidence/sast.json'],
    [sys.executable,'-m','pip_audit','-r','requirements.txt','--require-hashes','--disable-pip','-f','json','-o','evidence/sca-python.json'],
    ['npm','audit','--prefix','frontend','--audit-level=high','--json'],
    ['gitleaks','dir','.','--no-banner','--redact','--report-format','json','--report-path','evidence/secrets.json'],
]
results=[]
for command in commands:
    r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    if command[0]=='npm':(OUT/'sca-npm.json').write_text(r.stdout)
    results.append({'command':command,'exit_code':r.returncode,'stdout':r.stdout[-2500:],'stderr':r.stderr[-2500:]})
(OUT/'security-gate.json').write_text(json.dumps(results,indent=2))
for result in results:print('PASS' if result['exit_code']==0 else 'FAIL',' '.join(result['command']))
sys.exit(int(any(r['exit_code']!=0 for r in results)))
