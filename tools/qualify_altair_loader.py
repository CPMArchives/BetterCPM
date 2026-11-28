#!/usr/bin/env python3
"""Qualify the final Altair boot/load boundary using disposable B-drive probes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from altair_media import image
from test_altair_system import Terminal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    root=a.build_root.resolve();src=root/'build/altair';out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    collection=json.loads((src/'release/collection.json').read_text());master=(src/'release'/collection['volumes'][0]['image']).read_bytes()
    def work(name,system=master):
        w=out/name;w.mkdir();(w/'disks').mkdir()
        for letter in 'abcd':(w/f'disks/drive{letter}.dsk').write_bytes(system if letter=='a' else image(bytes(20480),[]))
        for n in ('diskdefs','system.conf'):shutil.copy2(src/n,w/n)
        return w
    w=work('load-boundary')
    files=[(n.upper()+'.COM',(src/(n+'.bin')).read_bytes()) for n in ('atpa','afile','aapi','aecho')]
    files += [('ECHO.RSX',(root/'build/rsx/ECHO.RSX').read_bytes())]
    (w/'disks/driveb.dsk').write_bytes(image(bytes(20480),files))
    t=Terminal(a.simulator.resolve(),w)
    try:
        t.prompt();t.send('STAT MEM','Maximum loadable COM: 57344 bytes')
        t.send('B:AAPI','ALTAIR GEOMETRY API PASS')
        t.send('B:AFILE','ALTAIR BDOS FILE IO PASS')
        t.send('B:ATPA','ALTAIR 56K TPA OVERWRITE PASS')
        t.send('VER','BetterCP/M 1.3');t.send('RSX LOAD B:ECHO')
        t.send('RSX LIST','ECHO : BDOS 199');t.send('B:AECHO','Hello from ECHO.RSX')
        t.send('RSX UNLOAD ECHO');t.send('STAT MEM','Maximum loadable COM: 57344 bytes')
        t.send('B:',drive='B');t.send('\x03',drive='B')
    finally:t.close()
    expected=bytes(record^column for record in range(140) for column in range(128,0,-1))
    for letter in 'bcd':
        target=w/(letter+'-ALTAIR.DAT')
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-altair',str(w/f'disks/drive{letter}.dsk'),'0:ALTAIR.DAT',str(target)],cwd=w,check=True)
        assert target.read_bytes()==expected,letter+' multi-extent extraction differs'
    guards=[]
    for name,offset in [('stage1-corruption',60*128+200),('stage2-corruption',84*128+200),('foreign-stage1-identity',60*128+1000)]:
        damaged=bytearray(master);damaged[offset]^=1;w=work(name,damaged)
        t=Terminal(a.simulator.resolve(),w)
        try:t.expect('!');t.process.wait(timeout=5)
        finally:t.close()
        assert b'A0>' not in t.data and (w/'disks/drivea.dsk').read_bytes()==damaged
        guards.append({'case':name,'status':'PASS','transcript_sha256':hashlib.sha256(t.data).hexdigest()})
    result={'status':'PASS','system_sha256':hashlib.sha256(master).hexdigest(),'guards':guards,
            'checks':['56K destructive TPA overwrite and warm reconstruction','B-D multi-extent data and independent extraction','geometry API','ECHO load/call/unload and full memory recovery','B warm-boot preservation'],
            'fixture_scope':'diagnostics installed only on disposable B; final release System bytes used unchanged'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: final Altair loader, TPA and carrier guards')


if __name__=='__main__':main()
