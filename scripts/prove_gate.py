"""Prove SAST rejects an actual high severity fixture without executing it."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='notevault-gate-') as directory:
    fixture=Path(directory)/'high_severity_fixture.py'
    fixture.write_text('import subprocess\n\ndef export(fmt):\n    return subprocess.run("echo " + fmt, shell=True)\n')
    r=subprocess.run([sys.executable,'-m','bandit','-r',str(fixture),'-lll','-ii','-f','json'],capture_output=True,text=True)
    report=json.loads(r.stdout)
    assert r.returncode!=0 and any(x['issue_severity']=='HIGH' for x in report['results'])
    output={'captured_at':datetime.now(timezone.utc).isoformat(),'fixture':'Nonexecuted shell injection sample in a temporary directory','exit_code':r.returncode,'scanner_report':report,'scope':'Local execution of the CI SAST command; not a hosted GitHub Actions run.'}
    (ROOT/'evidence/gate-rejection.json').write_text(json.dumps(output,indent=2))
    print('Verified: high-severity SAST fixture rejects with exit code',r.returncode)
