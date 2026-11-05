from pathlib import Path
from datetime import datetime,timezone,timedelta
import hashlib,json,subprocess,xml.etree.ElementTree as ET,shutil
import os
os.chdir(Path(__file__).resolve().parents[1])
ci=json.loads(Path('evidence/audit/hosted-ci.json').read_text())
assert ci['conclusion']=='success' and ci['status']=='completed'
assert ci['url'].startswith('https://github.com/6631503097/notevault-team-outsiders/actions/runs/')
job=next(j for j in ci['jobs'] if j['name']=='security');assert job['conclusion']=='success'
journal=json.loads(Path('evidence/audit/execution-journal.json').read_text());latest={r['check']:r for r in journal['records']}
required={'baseline','backend','frontend-tests','frontend-build','signature','tamper-rejection','runtime-executables'}
assert required<=latest.keys() and all(latest[k]['passed'] for k in required)
for record in journal['records']:
 for name,digest in record['outputs'].items():assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest,name
base=json.loads(Path('evidence/audit/baseline.json').read_text());team=json.loads(Path('team.json').read_text())
assert base['team']==team['id']=='Team Outsiders' and base['marker']=='3d821afbe8a0'
assert base['baseline_sha256']==hashlib.sha256(Path('lab/original/app.py').read_bytes()).hexdigest()
assert len([r for r in base['results'] if 'request' in r])==10
xml=ET.parse('evidence/audit/regression.xml').getroot();suites=list(xml.iter('testsuite'));assert sum(int(x.get('tests','0')) for x in suites)==25;assert sum(int(x.get('failures','0'))+int(x.get('errors','0')) for x in suites)==0
assert '3 passed' in Path('evidence/audit/frontend-tests-attempt2.log').read_text()
release=json.loads(Path('release/provenance.json').read_text());mismatch=[name for name,digest in release['files'].items() if hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest];assert not mismatch,mismatch
blobmap={}
for line in subprocess.check_output(['git','ls-tree','-r',ci['headSha']],text=True).splitlines():
 meta,path=line.split('\t',1);blobmap[path]=meta.split()[2]
critical=[p for p in blobmap if p.startswith(('backend/','frontend/src/','tests/')) or p in {'Dockerfile','compose.yaml','requirements.txt','frontend/package.json','frontend/package-lock.json','frontend/vite.config.ts','team.json'}]
for name in critical:
 data=Path(name).read_bytes();assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==blobmap[name],name
inputs=[]
for path in sorted(Path('evidence/audit').rglob('*')):
 if not path.is_file() or path.name=='provenance.json':continue
 scope='own-repository-ci-generated-output' if '/ci/' in str(path) else ('own-repository-ci-observation' if path.name=='hosted-ci.json' else 'independent-local-audit-record')
 inputs.append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scope':scope})
for name in critical+['lab/original/app.py','scripts/reproduce_baseline.py','scripts/record_audit_checks.py','scripts/build_report.py','release/team-outsiders-notevault.tar.gz','release/cosign.pub','release/release.sigstore.json','release/provenance.json','release/SHA256SUMS']:
 inputs.append({'path':name,'sha256':hashlib.sha256(Path(name).read_bytes()).hexdigest(),'scope':'source inspected; implementation inherited unless audit tooling'})
student=[str(p) for p in Path('evidence').glob('*.png')]+['evidence/baseline.json']
summary={'hosted_ci':'Passed security job at '+ci['url']+' on '+ci['headSha']+'; tag-only signing skipped'}
ledger={'checked_at':datetime.now(timezone(timedelta(hours=7))).isoformat(),'restored_bundle_head':'eee868167d3bb1b9aefb6fba73aede7103308452','ci_source_head':ci['headSha'],'runtime_and_test_source_files_matching_ci':critical,'all_required_checks_passed':True,'meaning_of_pass':'Latest required check passes; the failed initial local frontend attempt is retained and disclosed. This is not a claim that every attempt passed.','local_failed_attempts':[r for r in journal['records'] if not r['passed']],'summary':summary,'report_inputs':inputs,'retained_student_material':student,'release':{'source_head':release['revision'],'sha256':hashlib.sha256(Path('release/team-outsiders-notevault.tar.gz').read_bytes()).hexdigest(),'runtime_build_input_hashes_match_current_workspace':True},'inherited_claims_excluded':['earlier Debian-image rejection','specific dependency-upgrade history','external deployment ownership/Nginx/remote persistence/salt configuration','private Classroom access date','uncited legacy evidence files'],'limits':'An analyst-created hash ledger is not independent attestation. Student statements/screenshots are their own submissions; inherited code is not new work in this conversation.'}
Path('evidence/audit/provenance.json').write_text(json.dumps(ledger,indent=2)+'\n')
print('Ledger accepted:',len(inputs),'hashed inputs;',len(critical),'runtime/test files match observed own-repository CI head; initial failed attempt retained')
