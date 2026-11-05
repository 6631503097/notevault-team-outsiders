"""Create a review draft handoff from tracked source and public release evidence."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output' / 'handoff'
OUT.mkdir(parents=True, exist_ok=True)
revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
if subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True).strip():
    raise SystemExit('Commit reviewed tracked changes before packaging the handoff.')
bundle = OUT / 'Team_Outsiders_Repository.bundle'
subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], cwd=ROOT, check=True)
files = [ROOT / p for p in subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()]
files += [ROOT / 'output/pdf/team-outsiders-report-final-draft.pdf', bundle]
files += [p for p in (ROOT / 'release').glob('*') if p.is_file()]
final_ci = json.loads((OUT / 'final-ci.json').read_text())
if final_ci.get('headSha') != revision or final_ci.get('conclusion') != 'success' or final_ci.get('status') != 'completed':
    raise SystemExit('Require a successful hosted CI run on the exact packaged head.')
files.append(OUT / 'final-ci.json')
qa = ROOT / 'output/pdf/qa/verification.json'
files.append(qa)
blocked_parts = {'.keys', '.git', '.venv', '.lab-venv', '.tooling', 'node_modules', 'instance', '__pycache__'}
for path in files:
    relative = path.relative_to(ROOT)
    if any(part in blocked_parts for part in relative.parts) or path.name.startswith('.env') or path.suffix in {'.key', '.db', '.sqlite', '.sqlite3'} or '.db-' in path.name:
        raise SystemExit('Forbidden package input: ' + str(relative))
    if not path.is_file():
        raise SystemExit('Missing package input: ' + str(relative))
manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
archive = OUT / 'Team_Outsiders_Review_Draft.zip'
with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as z:
    for path in sorted(set(files)):
        z.write(path, 'Team_Outsiders/' + str(path.relative_to(ROOT)))
    z.writestr('Team_Outsiders/HANDOFF-MANIFEST.json', json.dumps({'revision': revision, 'status': 'Review draft; human reviews, demo and submission pending', 'final_ci': final_ci['url'], 'files': manifest}, indent=2) + '\n')
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
pdf = ROOT / 'output/pdf/team-outsiders-report-final-draft.pdf'
pdf_checksum = hashlib.sha256(pdf.read_bytes()).hexdigest()
(OUT / 'SHA256SUMS').write_text(checksum + '  ' + archive.name + '\n' + pdf_checksum + '  ../pdf/' + pdf.name + '\n')
(OUT / 'ARTIFACTS.json').write_text(json.dumps({'revision': revision, 'ci': final_ci['url'], 'pdf': {'path': str(pdf), 'sha256': pdf_checksum}, 'zip': {'path': str(archive), 'sha256': checksum}}, indent=2) + '\n')
print(json.dumps({'path': str(archive), 'sha256': checksum, 'revision': revision, 'files': len(files)}, indent=2))
