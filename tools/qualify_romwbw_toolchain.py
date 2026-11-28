#!/usr/bin/env python3
"""Run pinned native ZSM4 macro/include and multi-module LINK probes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from qualify_cromemco_compatibility import REVISION
from qualify_utilities_toolchain import probe_sources
from romwbw_media import image
from test_romwbw_system import Terminal


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('suite','image-dir','simulator','rom','output'): p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    files=list(probe_sources().items());tools={}
    for name in ('ZSM4.COM','LINK.COM'):
        data=subprocess.check_output(['git','-C',str(a.suite.resolve()),'show',REVISION+':suite/build-tools/'+name])
        files.append((name,data));tools[name]=hashlib.sha256(data).hexdigest()
    source=a.image_dir.resolve()/'system.img';shutil.copy2(source,out/'system.img')
    shutil.copy2(a.image_dir.resolve()/'diskdefs',out/'diskdefs')
    (out/'work.img').write_bytes(image(bytes(20480),b'\0',files))
    cmd=[str(a.simulator.resolve()),'--romwbw='+str(a.rom.resolve()),
         '--disk0='+str(out/'system.img'),'--disk1='+str(out/'work.img'),
         '--boot=2','--no-config','--strict-io','--max-instructions=4000000000']
    t=Terminal(a.simulator.resolve(),out,command=cmd)
    try:
        t.prompt();t.send('CONFIG /LOGICAL=B /UNIT=3','B: binding updated.')
        t.send('B:',drive='B')
        for name in ('MAIN','PART'): t.send('ZSM4 '+name+'='+name,'Errors: 0',drive='B')
        t.send('LINK CHECK=MAIN,PART[A]',drive='B')
        t.send('CHECK','TOOLCHAIN OK',drive='B')
        assert b'MODULE OK' in t.data and b'TOOLCHAIN FAILED' not in t.data
    finally: t.close()
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-romwbw',str(out/'work.img'),
                    '0:CHECK.COM',str(out/'CHECK.COM')],cwd=out,check=True)
    result={'status':'PASS','suite_revision':REVISION,'tool_sha256':tools,
            'system_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'checks':['native indexed Z80 assembly','macro and include expansion',
                      'multi-module relocation/link','linked guest program execution'],
            'output_sha256':hashlib.sha256((out/'CHECK.COM').read_bytes()).hexdigest()}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print('PASS:',out/'result.json')


if __name__=='__main__': main()
