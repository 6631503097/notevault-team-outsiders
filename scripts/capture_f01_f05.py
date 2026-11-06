"""Harmless F-01/F-05 probes using isolated Flask clients, never a listener.
Operator labels are self-reported, not an identity attestation. No tokens are retained.
"""
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('--mode',choices=['baseline','patched'],required=True)
p.add_argument('--operator-label',default='Not attested; automated test-client execution')
p.add_argument('--summary',action='store_true',help='Print compact results for a readable terminal capture; JSON is still retained')
a=p.parse_args()
team=json.loads((ROOT/'team.json').read_text())
assert team['id']=='Team Outsiders'
rows=[]
def record(fid,operation,response,**observed):
    rows.append({'finding':fid,'operation':operation,'status':response.status_code,**observed})

with tempfile.TemporaryDirectory(prefix='outsiders-f01-f05-') as directory:
    if a.mode=='baseline':
        os.environ['TEAM_ID']=team['id']
        spec=importlib.util.spec_from_file_location('original_review',ROOT/'lab/original/app.py')
        original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
        original.DB=str(Path(directory)/'baseline.db');original.seed();original.app.config['TESTING']=True
        c=original.app.test_client()
        r=c.post('/login',data={'username':"admin' --",'password':'wrong'})
        assert r.status_code==302 and 'session=' in r.headers.get('Set-Cookie','')
        record('F-01','Injected username with an incorrect fixture password',r,session_cookie_issued=True,limit='Cookie issuance is not proof of a normal administrator subject; no cookie value retained')
        c=original.app.test_client();assert c.post('/login',data={'username':'alice','password':'alicepw'}).status_code==302
        r=c.get('/search',query_string={'q':"' OR 1=1 -- "})
        marker=original.team_marker();assert marker in r.get_data(as_text=True)
        record('F-01','Injected search as Alice',r,other_owner_team_marker_present=True,marker=marker)
        r=c.get('/export',query_string={'fmt':'txt; printf NV_SAFE_PROBE'})
        assert 'NV_SAFE_PROBE' in r.get_data(as_text=True)
        record('F-05','Export format appends only harmless printf NV_SAFE_PROBE',r,harmless_shell_probe_present=True)
    else:
        from backend.app import create_app
        app=create_app({'TESTING':True,'DATABASE':str(Path(directory)/'patched.db'),'DEMO_MODE':True})
        c=app.test_client();h={'X-NoteVault-Client':'web'}
        r=c.post('/api/login',json={'username':"admin' --",'password':'wrong'},headers=h)
        assert r.status_code==401
        record('F-01','Same injected username with incorrect fixture password',r,rejected=True)
        login=c.post('/api/login',json={'username':'alice','password':'alicepw'},headers=h);assert login.status_code==200
        write_h={**h,'X-CSRF-Token':login.json['csrf']}
        r=c.get('/api/notes',query_string={'q':"' OR 1=1 -- "})
        assert r.status_code==200 and r.json['notes']==[]
        record('F-01','Same injected search as Alice',r,note_count=0,treated_as_literal_data=True)
        r=c.post('/api/notes',json={'title':'Wanna guided review fixture','body':'Harmless review note','collection':team['collections'][0]},headers=write_h);assert r.status_code==201
        r=c.get('/api/notes',query_string={'q':'guided review fixture'});assert r.status_code==200 and len(r.json['notes'])==1
        record('F-01','Legitimate literal search for a newly created own note',r,note_count=1)
        for fmt in ['txt; printf NV_SAFE_PROBE','$(id)','../../../etc/passwd','html']:
            r=c.get('/api/export',query_string={'fmt':fmt});assert r.status_code==400
            record('F-05','Reject unrecognized format: '+fmt,r,rejected=True,harmless_shell_probe_present='NV_SAFE_PROBE' in r.get_data(as_text=True))
        for fmt in ['json','csv','txt']:
            r=c.get('/api/export',query_string={'fmt':fmt});assert r.status_code==200 and b'Harmless review note' in r.data and 'attachment' in r.headers.get('Content-Disposition','')
            record('F-05','Legitimate owned-note '+fmt+' export',r,attachment=True,own_fixture_present=True)
        marker=c.get('/api/config').json['marker']

out=ROOT/'evidence/review-wanna-f01-f05';out.mkdir(parents=True,exist_ok=True)
result={'team':team['id'],'marker':marker,'prepared_for':'Wanna San - 6631503097','operator_label':a.operator_label,'identity_limit':'Operator label is supplied text, not proof of student execution or understanding','captured_at':datetime.now(timezone(timedelta(hours=7))).isoformat(),'mode':a.mode,'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'source_sha256':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['lab/original/app.py','backend/app.py','scripts/capture_f01_f05.py']},'method':'Isolated temporary database and Flask test client; no public listener; no session or CSRF token values retained','results':rows}
path=out/(a.mode+'.json');path.write_text(json.dumps(result,indent=2)+'\n')
if a.summary:
    print(result['captured_at']+' | '+result['prepared_for'])
    print(result['team']+' | marker='+marker+' | mode='+a.mode)
    print('Operator label (self-reported): '+a.operator_label)
    print('Temporary DB / Flask client only; no listener or retained token values')
    for row in rows:
        details={k:v for k,v in row.items() if k not in {'finding','operation','status','limit'}}
        print(row['finding']+' | HTTP '+str(row['status'])+' | '+row['operation']+' | '+json.dumps(details,sort_keys=True))
    print('Evidence: '+str(path.relative_to(ROOT)))
else:
    print(json.dumps(result,indent=2))
