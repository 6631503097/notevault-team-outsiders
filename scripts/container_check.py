"""Verify the running Compose application and its effective container protections."""
from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
team=json.loads((ROOT/'team.json').read_text())
base='http://127.0.0.1:'+str(team['port'])
assert json.load(urllib.request.urlopen(base+'/api/health'))['status']=='ok'
config=json.load(urllib.request.urlopen(base+'/api/config'))
assert config['team']==team['id']
container=subprocess.check_output(['docker','compose','ps','-q','app'],cwd=ROOT,text=True).strip()
info=json.loads(subprocess.check_output(['docker','inspect',container],text=True))[0]
assert info['Config']['User']=='10001:10001'
assert info['HostConfig']['ReadonlyRootfs']
assert 'ALL' in info['HostConfig']['CapDrop']
assert 'no-new-privileges:true' in info['HostConfig']['SecurityOpt']
assert all(binding['HostIp']=='127.0.0.1' for bindings in info['HostConfig']['PortBindings'].values() for binding in bindings)
output={'team':team['id'],'marker':config['marker'],'captured_at':datetime.now(timezone.utc).isoformat(),'image_id':info['Image'],'user':info['Config']['User'],'read_only_rootfs':True,'cap_drop':info['HostConfig']['CapDrop'],'security_options':info['HostConfig']['SecurityOpt'],'ports':info['HostConfig']['PortBindings'],'health':info['State']['Health']['Status']}
(ROOT/'evidence/container-check.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output,indent=2))
