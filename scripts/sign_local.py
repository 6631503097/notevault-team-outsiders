"""Create a separate local signing key per team and verify a release, offline.
A local signature demonstrates integrity; it does not establish public identity or SLSA.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import tempfile
ROOT=Path(__file__).resolve().parents[1]
team=json.loads((ROOT/'team.json').read_text())
keys=ROOT/'.keys';keys.mkdir(mode=0o700,exist_ok=True)
secret=keys/'passphrase'
if not secret.exists():
    fd=os.open(secret,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as output:output.write(secrets.token_urlsafe(40))
env={**os.environ,'COSIGN_PASSWORD':secret.read_text()}
prefix=keys/'cosign'
if not prefix.with_suffix('.key').exists():
    subprocess.run(['cosign','generate-key-pair','--output-key-prefix',str(prefix)],env=env,check=True)
artifact=ROOT/'release'/(team['slug']+'-notevault.tar.gz')
bundle=ROOT/'release'/'release.sigstore.json'
subprocess.run(['cosign','sign-blob','--yes','--key',str(prefix.with_suffix('.key')),'--use-signing-config=false','--tlog-upload=false','--bundle',str(bundle),str(artifact)],env=env,check=True)
shutil.copy2(prefix.with_suffix('.pub'),ROOT/'release/cosign.pub')
result=subprocess.run(['cosign','verify-blob','--key',str(ROOT/'release/cosign.pub'),'--bundle',str(bundle),'--insecure-ignore-tlog',str(artifact)],capture_output=True,text=True)
(ROOT/'evidence/cosign-verification.txt').write_text('Local key signature; transparency log intentionally not used.\n'+result.stdout+result.stderr)
result.check_returncode()
print(result.stdout+result.stderr)

with tempfile.TemporaryDirectory(prefix='notevault-tamper-') as directory:
    changed=Path(directory)/'tampered.tar.gz'
    changed.write_bytes(artifact.read_bytes()+b'local integrity probe')
    bad=subprocess.run(['cosign','verify-blob','--key',str(ROOT/'release/cosign.pub'),'--bundle',str(bundle),'--insecure-ignore-tlog',str(changed)],capture_output=True,text=True)
    (ROOT/'evidence/cosign-tamper-rejection.txt').write_text('Changed artifact verification exit code: '+str(bad.returncode)+'\n'+bad.stdout+bad.stderr)
    if bad.returncode==0:raise RuntimeError('Tampered artifact was incorrectly accepted')
    print('Tampered artifact correctly rejected.')
