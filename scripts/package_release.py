"""Package only hardened runtime/build source and generated frontend. Never package lab or keys."""
from datetime import datetime,timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
ROOT=Path(__file__).resolve().parents[1]
team=json.loads((ROOT/'team.json').read_text())
release=ROOT/'release';release.mkdir(exist_ok=True)
revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
files=[]
for entry in ['backend','frontend/src','frontend/public','frontend/dist','requirements.txt','team.json','Dockerfile','compose.yaml','frontend/package.json','frontend/package-lock.json','frontend/tsconfig.json','frontend/vite.config.ts','frontend/index.html']:
    path=ROOT/entry
    files.extend([p for p in path.rglob('*') if p.is_file() and '__pycache__' not in p.parts] if path.is_dir() else [path])
for path in sorted((ROOT/'evidence').glob('sbom-*.json')):files.append(path)
missing=[str(p) for p in files if not p.exists()]
if missing:raise RuntimeError('Missing release inputs: '+str(missing))
manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
provenance={'team':team['id'],'revision':revision,'created_at':datetime.now(timezone.utc).isoformat(),'builder':'local AI-assisted build; no SLSA level claimed','files':manifest}
(release/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
artifact=release/(team['slug']+'-notevault.tar.gz')
with tarfile.open(artifact,'w:gz') as archive:
    for path in sorted(files):archive.add(path,arcname=str(path.relative_to(ROOT)),recursive=False)
    archive.add(release/'provenance.json',arcname='provenance.json')
(release/'SHA256SUMS').write_text(hashlib.sha256(artifact.read_bytes()).hexdigest()+'  '+artifact.name+'\n')
print(artifact)
