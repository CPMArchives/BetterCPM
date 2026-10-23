#!/usr/bin/env python3
"""Audit source closure, profile separation, filesystem selection and repeats."""
from pathlib import Path
import argparse,hashlib,json,subprocess
p=argparse.ArgumentParser(description=__doc__);p.add_argument('full',type=Path);p.add_argument('legacy',type=Path);p.add_argument('repeat',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
profiles=[json.loads((r/'assessment-profile.json').read_text()) for r in (a.full,a.legacy,a.repeat)]
assert profiles[0]['compatibility_id']==profiles[2]['compatibility_id']!=profiles[1]['compatibility_id']
assert profiles[0]['contract']['private_inputs']==profiles[1]['contract']['private_inputs']
for p in profiles:
 c=p['contract'];assert c['carrier_epoch']==c['private_epoch']==c['package_epoch']==2
 ident=hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:32];assert ident==p['compatibility_id']
 for name,expected in c['private_inputs'].items():assert sha(repo/name)==expected,name
 changed=json.loads(json.dumps(c));changed['private_inputs']['tools/checked_system_package.py']='0'*64
 assert hashlib.sha256(json.dumps(changed,sort_keys=True,separators=(',',':')).encode()).hexdigest()[:32]!=ident
result={'profiles':{},'repeat_artifacts':[],'source_closure_files':len(profiles[0]['contract']['private_inputs']),'metadata_and_transitive_tools_included':True,'changed_input_changes_contract':True}
for r,profile in zip((a.full,a.legacy),profiles):
 m=json.loads((r/'assessment-media/manifest.json').read_text());ident=profile['compatibility_id'];expected=bytes.fromhex(ident)
 assert m['compatibility_id']==ident
 names=set(m['files']);assert not {'HELLO.RSX','HELLO.CPX','STATEFUL.RSX'} & names
 directory=subprocess.check_output(['cpmls','-f','bettercpm-default',str(r/'assessment-media/system.raw')],cwd=r/'assessment-media').decode().upper()
 for n in ('HELLO.RSX','HELLO.CPX','STATEFUL.RSX'):assert n not in directory
 for n,v in m['files'].items():assert sha(r/v['artifact'])==v['sha256'],n
 for rel,offset in [('build/z80pack/command-loader/stage1.carrier',1000),('build/z80pack/command-loader/stage2.carrier',2024),('build/system/R3PACK.RSX',8)]:assert (r/rel).read_bytes()[offset:offset+16]==expected,rel
 for rel in ('build/ccp/ccp.rlm','build/cpx/RCP.CPX'):assert (r/rel).read_bytes()[-18:-2]==expected,rel
 sysgen_size=(r/'build/utilities/SYSGEN.COM').stat().st_size;assert sysgen_size+256<0x3000
 result['profiles'][profile['contract']['profile']]={'compatibility_id':ident,'files':len(names),'test_modules_excluded':True,'sysgen_bytes':sysgen_size,'stage2_bytes':(r/'build/z80pack/command-loader/stage2.bin').stat().st_size}
manifest=json.loads((a.full/'assessment-media/manifest.json').read_text())
paths=['assessment-media/system.raw','assessment-media/SYSTEM.SYS','build/z80pack/command-loader/stage1.carrier','build/z80pack/command-loader/stage2.carrier','build/ccp/ccp.rlm']+[v['artifact'] for v in manifest['files'].values()]
for rel in paths:
 assert (a.full/rel).read_bytes()==(a.repeat/rel).read_bytes(),rel
 result['repeat_artifacts'].append({'path':rel,'sha256':sha(a.full/rel)})
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result['profiles']));print('PASS closure, profile binding, selected files and '+str(len(paths))+' repeated artifacts')
