"""Prepare manifest-selected Altair System and Utilities volumes, with readback."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from altair_media import image,DISKDEFS

def sha(data):return hashlib.sha256(data).hexdigest()


def build_collection(root,out,payload,assembler):
    from build_utilities import BUILDERS
    env=dict(os.environ,BETTERCPM_IDENTITY_TARGET='altair',BETTERCPM_IDENTITY_STATE='assigned')
    existing={'disk_utilities','path','ndr','batch','rsx_utilities'}
    for name in [n for n in BUILDERS if n not in existing]+['ed','sq','usq','uncr','cr','lzh','unlzh','search','fdf_rsx','p2dos_rsx','adm3a','vt52','ansi']:
        command=[sys.executable,'-B',str(root/'tools'/f'build_{name}.py')]
        if name!='fdb':command+=['--assembler',str(assembler)]
        if name in ('ddt','dasm','dsym','dlink','sq','usq','uncr','cr','lzh','unlzh','stat','time','path'):command+=['--target','altair']
        subprocess.run(command,cwd=root,env=env,check=True)
    from build_ted import build as ted
    ted(assembler,root/'build/utilities',target='altair',identity_state='assigned')
    from build_release_tcap import release_modules
    release_modules('altair',assembler)
    from fdf_v1 import compile_file
    (out/'DISK.FDB').write_bytes(compile_file(root/'src/platform/altair/ALTRB77.FDF'))
    # The shared z80pack shutdown port is the same. Keep the standard parser,
    # confirmation and help while selecting an accurate emulator label.
    from build_z80pack_bye import build as bye
    bye(assembler,out,identity_state='assigned',emulator='Altair')
    from build_distribution import selected_files
    manifest=json.loads((root/'metadata/distribution.json').read_text())
    selected,omitted=selected_files(manifest,'altair',root)
    files={r['name']:data for r,data in selected}
    from build_utilities_disk import COMPONENTS
    from noah_distribution import COMPONENTS as NOAH
    for name,path in {**COMPONENTS,**NOAH, 'MOVE.COM':'build/utilities/MOVE.COM',
                      'WARM.COM':'build/utilities/WARM.COM'}.items():
        files[name]=(root/path).read_bytes()
    # Keep every loadable overlay with its command. A search PATH only crosses
    # disks mounted by the caller; no hidden swapping or altered OS semantics.
    critical=('README.TXT','STARTUP.SUB','RCP.CPX','R3PACK.RSX','R3CACHE.RSX','SYSTEM.SYS',
              'CONFIG.COM','PDSCONF.OVL','STAT.COM','RSX.COM','CPX.COM','PATH.COM',
              'NDR.COM','NDR.RSX','SUBMIT.COM','P2DOS.RSX','SYSGEN.COM','DUP.COM','BYE.COM','DISK.FDB','VER.COM','DIR.COM','ERA.COM','TYPE.COM','REN.COM','TIME.COM','PIP.COM','ED.COM')
    volumes=[('System',[(n,files.pop(n)) for n in critical])]
    groups=[]
    for family in [('HELP.COM','HELP.LBR'),('FDB.COM','FDBVIEW.OVL'),('NOAH.COM','NOAH.OVL','NOAH.TXT')]:
        groups.append([(n,files.pop(n)) for n in family])
    groups += [[(n,data)] for n,data in sorted(files.items())]
    current=[]; number=1
    for group in groups:
        try:image(bytes(20480),current+group)
        except ValueError:
            if not current:raise
            volumes.append((f'Utilities-{number}',current));number+=1;current=[]
            image(bytes(20480),group)
        current+=group
    if current:volumes.append((f'Utilities-{number}',current))
    release=out/'release';release.mkdir()
    (release/'diskdefs').write_text(DISKDEFS)
    reports=[]
    for label,items in volumes:
        name=f'BetterCPM-1.3-Altair-{label}.dsk'
        raw=image(payload if label=='System' else bytes(20480),items)
        target=release/name;target.write_bytes(raw)
        subprocess.run(['fsck.cpm','-T','raw','-f','bettercpm-altair','-n',str(target)],cwd=release,check=True)
        included=[]
        for filename,data in items:
            extraction=release/'readback.bin'
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-altair',str(target),'0:'+filename,str(extraction)],cwd=release,check=True)
            actual=extraction.read_bytes()
            if actual!=data.ljust((len(data)+127)//128*128,b'\x1a'):
                raise ValueError('independent readback differs: '+filename)
            included.append({'name':filename,'bytes':len(data),'sha256':sha(data),'cpm_sha256':sha(actual)})
            extraction.unlink()
        reports.append({'volume':label,'image':name,'sha256':sha(raw),'included':included})
    shutil.copy2(out/'system.conf',release/'system.conf')
    report={'status':'CANDIDATE; runtime qualification pending','target':'altair','version':'1.3',
            'manifest_sha256':sha((root/'metadata/distribution.json').read_bytes()),
            'volumes':reports,'omitted':omitted,'development_fixtures':False}
    (release/'collection.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Prepared',len(reports),'Altair release volumes',flush=True)
