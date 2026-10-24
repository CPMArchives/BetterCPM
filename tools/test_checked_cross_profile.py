#!/usr/bin/env python3
"""Cross-profile live rejection and public-service portability on private media."""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
from test_z80pack_sysgen_install import session
from system_layout import LAYOUT as L


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--foreign',type=Path,required=True)
    p.add_argument('--image',type=Path,required=True)
    p.add_argument('--foreign-image',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    a=p.parse_args();root=Path(__file__).resolve().parents[1];out=a.output.resolve();out.mkdir(parents=True)
    results={}
    def case(name):
        w=out/name;(w/'disks').mkdir(parents=True)
        shutil.copy2(root/'build/z80pack/diskdefs',w/'diskdefs')
        for d in 'abcd':shutil.copy2(a.image,w/'disks'/f'drive{d}.dsk')
        return w
    def put(w,name,data,drive='a'):
        path=w/name;path.write_bytes(data);disk=w/'disks'/f'drive{drive}.dsk'
        subprocess.run(['cpmrm','-f','bettercpm-default',str(disk),'0:'+name],cwd=w,capture_output=True)
        subprocess.run(['cpmcp','-f','bettercpm-default',str(disk),str(path),'0:'+name],cwd=w,check=True,capture_output=True)
    def run(w,commands):
        steps=[(c.encode()+b'\r',b'A0>_ ',30) if isinstance(c,str) else c for c in commands]
        return session(a.simulator,w/'disks',steps,w/'transcript.bin').decode(errors='replace')
    w=case('utilities')
    for name in ('CONFIG','SYSGEN','STAT','RSX','CPX','CLS'):
        put(w,'F'+name+'.COM',(a.foreign/f'build/utilities/{name}.COM').read_bytes())
    put(w,'HELLO.CPX',(root/'build/cpx/HELLO.CPX').read_bytes())
    t=run(w,['FCONFIG /SHOW','FSYSGEN A: B:','FSTAT MEM','FSTAT VAL:',
             'FRSX LIST','FCPX LIST','FRSX LOAD ZPRTC','TIME','FRSX UNLOAD ZPRTC',
             'FCPX LOAD HELLO','HELLO','FCPX UNLOAD HELLO','FCLS','STAT MEM'])
    assert t.count('Private utility build mismatch.')==2 and t.count('Requires matching BetterCP/M private build.')==1
    assert 'Hello from HELLO.CPX' in t and 'RSX module or profile error' not in t
    assert f'Maximum loadable COM: {(L["TPA"]-256)//128*128}' in t
    results['utilities']={'private_refusals':3,'public_STAT_RSX_CPX_CLS':True}
    for kind in ('package','disk','rcp','pack'):
        w=case(kind);target=w/'disks/driveb.dsk'
        if kind=='package':
            put(w,'FOREIGN.SYS',(a.foreign/'build/z80pack/system-package/SYSTEM.SYS').read_bytes())
            steps=['SYSGEN FOREIGN.SYS B:'];message='system package is invalid'
        else:
            if kind=='disk':shutil.copy2(a.foreign_image,w/'disks/drivec.dsk')
            if kind in ('rcp','pack'):
                name,path=('RCP.CPX','build/cpx/RCP.CPX') if kind=='rcp' else ('R3PACK.RSX','build/system/R3PACK.RSX')
                put(w,name,(a.foreign/path).read_bytes(),'b')
            steps=[((b'SYSGEN C: B:\r' if kind=='disk' else b'SYSGEN A: B:\r'),b'Proceed (Y/N)?',60),(b'Y',b'A0>_ ',90)]
            message='system package is invalid' if kind=='disk' else 'Matching RCP.CPX and R3PACK.RSX required'
        before=target.read_bytes();t=run(w,steps)
        assert message in t and target.read_bytes()==before,kind
        results[kind]={'foreign_rejected':True,'target_unchanged':True}
    (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print('PASS five cross-profile campaigns')


if __name__=='__main__':main()
