import json
import sqlite3
import time

import pytest
from backend.app import create_app

H = {"X-NoteVault-Client": "web"}

@pytest.fixture()
def app(tmp_path):
    return create_app({"TESTING":True,"DATABASE":str(tmp_path/'vault.db'),"DEMO_MODE":True})

@pytest.fixture()
def client(app):
    return app.test_client()

def login(client, name='alice', password='alicepw'):
    result = client.post('/api/login',json={"username":name,"password":password},headers=H)
    assert result.status_code == 200, result.json
    return {**H,"X-CSRF-Token":result.json['csrf']}

def note_data(app, **changes):
    return {"title":"A real note","body":"Hello world","collection":app.config['TEAM']['collections'][0],**changes}

def test_legitimate_note_lifecycle_and_exports(app,client):
    h=login(client)
    result=client.post('/api/notes',json=note_data(app),headers=h)
    assert result.status_code==201
    n=result.json['note']
    assert client.get(f"/api/notes/{n['id']}").json['note']['body']=='Hello world'
    for change in ({'title':'Revised'}, {'pinned':True}, {'archived':True}, {'deleted':True}, {'deleted':False,'archived':False}):
        data={**n,**change,'pinned':bool(change.get('pinned',n['pinned'])),'archived':bool(change.get('archived',n['archived'])),'deleted':bool(change.get('deleted',n['deleted']))}
        r=client.put(f"/api/notes/{n['id']}",json=data,headers=h)
        assert r.status_code==200,r.json
        n=r.json['note']
    for fmt in ['json','csv','txt']:
        r=client.get('/api/export?fmt='+fmt)
        assert r.status_code==200 and 'attachment' in r.headers['Content-Disposition']
        assert b'Revised' in r.data and b'build-tag' not in r.data
    assert client.get('/api/activity').json['events']

@pytest.mark.parametrize('path',['/api/notes','/api/notes/1','/api/export','/api/activity','/api/team','/api/admin/users'])
def test_anonymous_cannot_read(client,path):
    assert client.get(path).status_code==401

def test_f01_sql_injection_login_and_search(app,client):
    assert client.post('/api/login',json={'username':"admin' --",'password':'wrong'},headers=H).status_code==401
    login(client)
    for q in ["' OR 1=1 --", "%' UNION SELECT 1,2,3 --", '%','_']:
        assert client.get('/api/notes',query_string={'q':q}).json['notes']==[]

def test_f02_owner_isolation_and_mass_assignment(app,client):
    h=login(client)
    admin=app.test_client();ah=login(admin,'admin','admin123')
    secret=admin.post('/api/notes',json=note_data(app,title='admin secret'),headers=ah).json['note']
    assert client.get(f"/api/notes/{secret['id']}").status_code==404
    assert client.put(f"/api/notes/{secret['id']}",json=note_data(app,version=1),headers=h).status_code==404
    created=client.post('/api/notes',json=note_data(app,owner_id=secret['owner_id']),headers=h).json['note']
    assert created['owner_id']!=secret['owner_id']
    assert all(n['owner_id']==created['owner_id'] for n in client.get('/api/notes').json['notes'])

def test_f03_registration_never_accepts_admin_role(app,client):
    r=client.post('/api/register',json={'username':'mallory','password':'strong-local-test-pass','role':'admin'},headers=H)
    assert r.status_code==201 and r.json['user']['role']=='user'
    assert client.get('/api/admin/users').status_code==403

def test_f04_html_and_template_payloads_remain_data(app,client):
    h=login(client)
    raw='<img src=x onerror=alert(1)>{{7*7}}'
    n=client.post('/api/notes',json=note_data(app,title=raw,body=raw),headers=h).json['note']
    r=client.get(f"/api/notes/{n['id']}")
    assert r.json['note']['body']==raw
    assert r.mimetype=='application/json'
    assert "script-src 'self'" in r.headers['Content-Security-Policy']
    assert r.headers['X-Content-Type-Options']=='nosniff'

@pytest.mark.parametrize('fmt',['txt; echo NV_PROBE','$(id)','../../../etc/passwd','html'])
def test_f05_export_rejects_command_input(client,fmt):
    login(client)
    assert client.get('/api/export',query_string={'fmt':fmt}).status_code==400

def test_f06_password_hashes_and_admin_redaction(app,client):
    login(client,'admin','admin123')
    r=client.get('/api/admin/users')
    assert r.status_code==200
    assert 'password' not in r.get_data(as_text=True)
    with sqlite3.connect(app.config['DATABASE']) as con:
        hashes=con.execute('SELECT password_hash FROM users').fetchall()
    assert all(h[0].startswith('scrypt:') for h in hashes)

def test_f07_session_revocation_expiry_and_forgery(app,client):
    h=login(client)
    name=app.config['COOKIE_NAME']
    token=client.get_cookie(name).value
    assert len(token)>=40
    assert client.post('/api/logout',json={},headers=h).status_code==200
    client.set_cookie(name,token)
    assert client.get('/api/notes').status_code==401
    login(client)
    with sqlite3.connect(app.config['DATABASE']) as con:
        con.execute('UPDATE sessions SET expires_at=?',(int(time.time())-1,))
    assert client.get('/api/notes').status_code==401
    client.set_cookie(name,'forged.jwt.token')
    assert client.get('/api/notes').status_code==401

def test_f08_csrf_origin_and_cookie_flags(app,client):
    response=client.post('/api/login',json={'username':'alice','password':'alicepw'},headers=H)
    cookie=response.headers['Set-Cookie']
    assert 'HttpOnly' in cookie and 'SameSite=Strict' in cookie
    h={**H,'X-CSRF-Token':response.json['csrf']}
    assert client.post('/api/notes',json=note_data(app)).status_code==403
    assert client.post('/api/notes',json=note_data(app),headers=H).status_code==403
    assert client.post('/api/notes',json=note_data(app),headers={**h,'Origin':'https://attacker.invalid'}).status_code==403
    assert client.get('/api/logout').status_code in (404,405)
    assert client.get('/api/notes',headers={'Host':'attacker.invalid'}).status_code==400

def test_concurrent_edit_protection(app,client):
    h=login(client);n=client.post('/api/notes',json=note_data(app),headers=h).json['note']
    data=note_data(app,version=n['version'],title='Edit one')
    assert client.put(f"/api/notes/{n['id']}",json=data,headers=h).status_code==200
    assert client.put(f"/api/notes/{n['id']}",json=data,headers=h).status_code==409
    assert client.get(f"/api/notes/{n['id']}").json['note']['title']=='Edit one'

def test_persistence_and_team_guard(app,client):
    h=login(client);n=client.post('/api/notes',json=note_data(app,title='Survives restart'),headers=h).json['note']
    restarted=create_app({'TESTING':True,'DATABASE':app.config['DATABASE'],'DEMO_MODE':True})
    c=restarted.test_client();login(c)
    assert c.get(f"/api/notes/{n['id']}").json['note']['title']=='Survives restart'
    with pytest.raises(RuntimeError,match='different TEAM_ID'):
        create_app({'DATABASE':app.config['DATABASE'],'TEAM_ID':'another team'})

def test_separate_databases_reject_replayed_session(app,client,tmp_path):
    login(client)
    other=create_app({'TESTING':True,'DATABASE':str(tmp_path/'other.db'),'TEAM_ID':'other','DEMO_MODE':True})
    c=other.test_client();c.set_cookie(other.config['COOKIE_NAME'],client.get_cookie(app.config['COOKIE_NAME']).value)
    assert c.get('/api/notes').status_code==401

def test_rate_limiting_and_malformed_inputs(app,client):
    assert client.post('/api/register',json=[],headers=H).status_code==400
    assert client.post('/api/register',data='bad',headers=H).status_code==415
    assert client.post('/api/register',json={'username':'joe','password':'short'},headers=H).status_code==400
    with sqlite3.connect(app.config['DATABASE']) as con:
        import hashlib
        bucket=hashlib.sha256(b'127.0.0.1').hexdigest()
        con.executemany('INSERT INTO attempts VALUES (?,?)',[(bucket,int(time.time()))]*20)
    assert client.post('/api/login',json={'username':'alice','password':'alicepw'},headers=H).status_code==429

def test_csv_formula_protection(app,client):
    h=login(client)
    client.post('/api/notes',json=note_data(app,title='=1+1',body='@SUM(1)'),headers=h)
    export=client.get('/api/export?fmt=csv').get_data(as_text=True)
    assert "'=1+1" in export and "'@SUM(1)" in export

def test_no_demo_accounts_without_explicit_opt_in(tmp_path):
    clean=create_app({'TESTING':True,'DATABASE':str(tmp_path/'clean.db'),'DEMO_MODE':False})
    c=clean.test_client()
    assert not c.get('/api/config').json['demo']
    assert c.post('/api/login',json={'username':'alice','password':'alicepw'},headers=H).status_code==401

def test_https_cookie_configuration(tmp_path):
    secure=create_app({'TESTING':True,'DATABASE':str(tmp_path/'secure.db'),'DEMO_MODE':True,'COOKIE_SECURE':True})
    c=secure.test_client()
    r=c.post('/api/login',base_url='https://localhost',json={'username':'alice','password':'alicepw'},headers=H)
    assert 'Secure;' in r.headers['Set-Cookie']
    assert r.headers['Strict-Transport-Security'].startswith('max-age=')
