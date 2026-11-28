#!/usr/bin/env python3
"""Smoke shipped Cromemco utilities, overlay PATH, HELP and native toolchain."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from cromemco_media import image
from test_cromemco_system import Terminal
from qualify_utilities_toolchain import probe_sources


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();src=a.image_dir.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    collection=json.loads((src/'release/collection.json').read_text())
    volumes={v['volume']:v for v in collection['volumes']}
    def mount(label):return (src/'release'/volumes[label]['image']).read_bytes()
    def work(name,c,d=None,files=()):
        w=out/name;w.mkdir();(w/'disks').mkdir();(w/'disks/disk.map').write_text(''.join(f'drive{d}.dsk\n' for d in 'abcd'))
        for letter,data in [('a',mount('System')),('b',image(bytes(20480),files)),('c',mount(c)),('d',mount(d) if d else image(bytes(20480),[]))]:
            (w/f'disks/drive{letter}.dsk').write_bytes(data)
        shutil.copy2(src/'system.conf',w/'system.conf');shutil.copy2(src/'release/diskdefs',w/'diskdefs')
        return w
    def start(w):
        t=Terminal(a.simulator.resolve(),w);t.prompt();return t
    registry={parts[0]:(parts[1],int(parts[2])) for line in (Path(__file__).resolve().parents[1]/'metadata/utility-versions.tsv').read_text().splitlines()[1:] if (parts:=line.split('\t'))}
    queried=[]
    for volume in volumes:
        w=work('versions-'+volume,volume);t=start(w)
        try:
            for row in volumes[volume]['included']:
                name=row['name']
                if not name.endswith('.COM') or name[:-4] not in registry:continue
                before=len(t.data);t.send('C:'+name[:-4]+' /VER')
                output=t.data[before:]
                assert b'Bad command' not in output and b'Unknown option' not in output,(name,output)
                version,revision=registry[name[:-4]]
                expected=f'{name[:-4]} {version} ({revision:03d})'.encode()
                assert expected in output,(name,expected,output)
                queried.append({'name':name,'sha256':row['sha256']})
        finally:t.close()
    w=work('overlays','Utilities-1','Utilities-3',files=[('INPUT.BIN',bytes(range(256)))])
    t=start(w)
    try:
        t.send('RSX LOAD C:ANSI')
        assert b'RSX module or profile error' not in t.data,'ANSI load failed'
        t.cursor=len(t.data);t.type_command('HELP PIP');t.expect('Q Exit')
        os.write(t.master,b'Q');t.prompt()
        t.send('NOAH /ADD B:SMOKE.ARK B:INPUT.BIN')
        t.send('NOAH /TEST B:SMOKE.ARK','INPUT.BIN: CRC OK')
        t.send('ERA B:INPUT.BIN')
        t.send('NOAH /X /Y B:SMOKE.ARK B:','extracted and verified.')
        t.send('RSX UNLOAD ANSI')
        for personality,drive in [('ADM3A','C'),('VT52','D')]:
            begin=len(t.data);t.send('RSX LOAD '+drive+':'+personality)
            assert b'RSX module or profile error' not in t.data[begin:],personality+' load failed'
            t.cursor=len(t.data);t.type_command('HELP PIP');t.expect('Q Exit')
            os.write(t.master,b'Q');t.prompt()
            t.send('RSX UNLOAD '+personality)
        t.send('STAT MEM','Maximum loadable COM: 57344 bytes')
    finally:t.close()
    extracted=w/'extracted.bin'
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-cromemco',str(w/'disks/driveb.dsk'),'0:INPUT.BIN',str(extracted)],cwd=w,check=True)
    assert extracted.read_bytes()==bytes(range(256))
    w=work('toolchain','Utilities-2','Utilities-3',list(probe_sources().items()));t=start(w)
    try:
        t.send('B:',drive='B')
        t.send('ZSM4 MAIN=MAIN','Errors: 0',drive='B')
        t.send('ZSM4 PART=PART','Errors: 0',drive='B')
        t.send('LINK CHECK=MAIN,PART[A]',drive='B')
        t.send('CHECK','TOOLCHAIN OK',drive='B')
        assert b'MODULE OK' in t.data and b'TOOLCHAIN FAILED' not in t.data
    finally:t.close()
    result={'status':'PASS','system_sha256':volumes['System']['sha256'],'utility_versions':queried,
            'checks':['all registry-versioned shipped COM queries','HELP PIP through PATH and all three integrated screen personalities','NOAH overlay PATH add/test/extract','native ZSM4 macro/include and multi-module LINK execution','56K restored after ANSI unload']}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS: Cromemco shipped utility smoke')


if __name__=='__main__':main()
