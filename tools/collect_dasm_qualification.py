#!/usr/bin/env python3
"""Collect complete exact-artifact DASM emulator qualification receipts and evidence."""
import argparse,gzip,hashlib,io,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()

def retained_dependencies(current_members,prior_members):
 names=('DASM.COM','DSYM.COM','ZSM4.COM','LINK.COM')
 if not all(current_members[n]==prior_members[n] for n in names):
  raise ValueError('retained campaign dependency changed')
 return {n:current_members[n] for n in names}


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--campaign-root',type=Path,default=Path('/private/tmp'));p.add_argument('--prefix',default='dasm-v3');p.add_argument('--final-prefix');p.add_argument('--retained-inventory',type=Path);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 gates={'runtime_profile':'runtime','real_utility':'utility2-{platform}','integration':'integration-{platform}','checked_link':'link-{platform}','analysis':'analysis-{platform}','corpus':'corpus-{platform}','capacity':'capacity-{platform}','filesystem':'failures2-{platform}','console':'console-{platform}','session_rejection':'session-rejection','insufficient_tpa':'low-tpa'}
 inventory=json.loads(a.inventory.read_text());assert inventory['status']=='PASS'
 retained=json.loads(a.retained_inventory.read_text()) if a.retained_inventory else inventory
 assert retained['status']=='PASS'
 binaries={n:{'sha256':sha((ROOT/'build/utilities'/n).read_bytes()),'bytes':(ROOT/'build/utilities'/n).stat().st_size} for n in ('DASM.COM','DSYM.COM','DLINK.COM')}
 receipt={'schema':1,'dasm_acceptance':'PASS','scope':'Model 4/trs80gp and z80pack/cpmsim emulators; no physical hardware or whole Utilities release claim','binaries':binaries,'external_tools':{n:{'version':v,'sha256':sha((ROOT/path).read_bytes())} for n,v,path in [('ZSM4.COM','4.7','third_party/zsm4/ZSM4.COM'),('LINK.COM','1.3','third_party/dri-link/LINK.COM')]},'host_full_core_cases':{'DASM':161,'DSYM':73,'DLINK':40,'USQ_regression':71},'platforms':{}}
 host=(a.campaign_root/((a.final_prefix or a.prefix)+'-host.txt')).read_bytes()
 for token in (b'161 DASM',b'73 DSYM',b'40 DLINK',b'71 standalone USQ',b'44 of 512 bytes'):
  assert token in host,('missing host verdict',token)
 receipt['stack_observed_high_water_bytes']=44
 evidence={'inventory.json':a.inventory.read_bytes(),'host-tests.txt':host};roots=set();disk_evidence=set()
 if a.retained_inventory:evidence['retained-inventory.json']=a.retained_inventory.read_bytes()
 for platform in ('z80pack','trs80gp'):
  proof={'status':'PASS','gates':{},'utilities_sha256':inventory['platforms'][platform]['image_sha256']}
  current_members=inventory['platforms'][platform]['files_sha256']
  retained_members=retained['platforms'][platform]['files_sha256']
  proof['retained_dependencies']=retained_dependencies(current_members,retained_members)
  for gate,template in gates.items():
   final_gate=gate in ('integration','checked_link','filesystem','console','runtime_profile')
   selected_prefix=(a.final_prefix or a.prefix) if final_gate else a.prefix
   folder=a.campaign_root/(selected_prefix+'-'+template.format(platform=platform));roots.add(folder)
   data=json.loads((folder/'report.json').read_text());result=data['platforms'][platform];assert result['status']=='PASS',(gate,platform,result)
   if gate=='runtime_profile':
    proof['normal_active_ceiling']=result['active_ceiling'];proof['normal_input_capacity']=result['input_capacity'];proof['resident_profile']=result['resident_profile']
   executions=list((folder/platform).rglob('execution.json'));assert executions,(gate,platform)
   if gate in ('filesystem','console'):
    preserved=list((folder/platform).rglob('after-KEEP.ASM' if gate=='filesystem' else 'after-ABORT.ASM'))
    assert len(preserved)==(4 if gate=='filesystem' else 1)
    for saved in preserved:
     original=saved.read_bytes();assert original[:13]==b'KEEP ORIGINAL' and 13<=len(original)<=128 and set(original[13:])<={0,26},saved
   for path in executions:
    execution=json.loads(path.read_text());assert execution['original_media_unchanged']
    if gate in ('filesystem','session_rejection'):
     disk=path.parent/'system.raw';disk_evidence.add(disk)
     definition='dasm-system' if platform=='trs80gp' else 'bettercpm-default'
     listing=subprocess.run(['cpmls','-T','raw','-f',definition,'system.raw'],cwd=path.parent,check=True,capture_output=True).stdout
     if gate=='filesystem':assert b'OUT.ASM' not in listing.upper()
     (path.parent/'filesystem-after.txt').write_bytes(listing)
     audit=subprocess.run(['fsck.cpm','-T','raw','-f',definition,'-n','system.raw'],cwd=path.parent,check=True,capture_output=True)
     (path.parent/'filesystem-check.txt').write_bytes(audit.stdout+audit.stderr)

    if 'system_sha256' in proof:assert proof['system_sha256']==execution['system_sha256'],(gate,platform,'system changed')
    proof['system_sha256']=execution['system_sha256']
    expected_media=inventory if final_gate else retained
    assert execution['utilities_sha256']==expected_media['platforms'][platform]['image_sha256'],(gate,'unexpected media')
    for name,value in execution.get('utilities_members',{}).items():
     if name in binaries:assert binaries[name]['sha256']==value,(gate,name)
   proof['gates'][gate]={'status':'PASS','report':folder.name+'/report.json','report_sha256':sha((folder/'report.json').read_bytes()),'tested_utilities_sha256':expected_media['platforms'][platform]['image_sha256'],'final_media_execution':final_gate}
  assert proof['utilities_sha256']==inventory['platforms'][platform]['image_sha256']
  for name,row in binaries.items():assert inventory['platforms'][platform]['files_sha256'][name]==row['sha256']
  receipt['platforms'][platform]=proof
 for folder in sorted(roots):
  for f in sorted(folder.rglob('*')):
   if f.is_file() and (f.suffix not in ('.dmk','.dsk','.raw') or f in disk_evidence) and 'disks' not in f.relative_to(folder).parts:
    evidence[folder.name+'/'+str(f.relative_to(folder))]=f.read_bytes()
 for name in ('DASM','DSYM','DLINK'):
  evidence['build/'+name+'-build-report.json']=(ROOT/'build/utilities'/(name+'-build-report.json')).read_bytes()
  for ext in ('mac','lst','bin'):evidence['build/'+name.lower()+'.'+ext]=(ROOT/'build/utilities'/(name.lower()+'.'+ext)).read_bytes()
 manifest={n:sha(b) for n,b in sorted(evidence.items())};evidence['EVIDENCE-MANIFEST.json']=(json.dumps(manifest,indent=2)+'\n').encode()
 raw=io.BytesIO()
 with tarfile.open(fileobj=raw,mode='w') as archive:
  for name,data in sorted(evidence.items()):
   info=tarfile.TarInfo(name);info.size=len(data);info.mode=0o644;archive.addfile(info,io.BytesIO(data))
 packed=gzip.compress(raw.getvalue(),mtime=0);name='DASM-Qualification-Evidence.tar.gz';(a.output/name).write_bytes(packed)
 receipt['evidence_archive']={'name':name,'bytes':len(packed),'sha256':sha(packed),'manifest_entries':len(manifest)}
 receipt['repository_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 receipt['evidence_policy']='Integration, corrected launcher, filesystem, console and runtime-profile gates execute final media. Retained DASM gates are accepted only with identical DASM/DSYM/ZSM4/LINK bytes, the same System image, and independently audited inventories; each tested media hash is explicit.'
 receipt['limits']=['8 KiB input; fixed bounded metadata arenas','BDOS active ceiling at least B200H; normal Model 4 M4SCRN+ADM3A and z80pack ZPRTC profiles','Fault-model injections cover individual BDOS failures and publication transitions; native media witnesses cover directory/data full, read-only file/media and cancellation','Single-byte LINK workaround adds explicit 1Ah outside the declared logical interval; physical padding checked separately','Owned binaries retain 1.0 (001-dev); external ZSM4/LINK retain upstream identities']
 (a.output/'DASM-Qualification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS both-platform exact-artifact qualification; evidence',sha(packed))
if __name__=='__main__':main()
