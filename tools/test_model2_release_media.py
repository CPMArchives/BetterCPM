#!/usr/bin/env python3
"""Independently decode the IMDs, check the protected package and exercise cpmtools."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from checked_system_package import validate
from model2_media import image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'docs/engineering/evidence/2026-11-06-model2'))
from inspect_images import decode, raw_image, repack

DISKDEFS = """diskdef bcm2ss
  seclen 512
  tracks 77
  sectrk 16
  blocksize 2048
  maxdir 128
  skew 1
  boottrk 4
  os 2.2
end
"""


def require(ok, message):
    if not ok:
        raise ValueError(message)


def decoded(blob):
    comment, tracks, problems = decode(blob)
    require(not problems and len(tracks)==77,'invalid track inventory')
    for cyl,track in enumerate(tracks):
        ids = tuple(range(1,27)) if not cyl else tuple(i*11%16+1 for i in range(16))
        require((track['cylinder'],track['head'],track['mode'],track['size'],tuple(track['ids'])) ==
                (cyl,0,3 if cyl else 0,512 if cyl else 128,ids),'wrong physical surface')
    raw = raw_image(tracks)
    require(len(raw)==625920,'wrong image size')
    return comment,tracks,raw


def check(out, binary_dir):
    payload=(out/'system-tracks.bin').read_bytes()
    package=(out/'SYSTEM.SYS').read_bytes()
    binding=json.loads((out/'checked-package.json').read_text())
    require(validate(package,binding) and package[128:]==payload,'wrong checked package')
    altered=bytearray(package);altered[-1]^=1
    try: validate(altered,binding)
    except ValueError: pass
    else: raise ValueError('modified package admitted')
    result={}
    with tempfile.TemporaryDirectory() as td:
        work=Path(td)
        (work/'diskdefs').write_text(DISKDEFS)
        env=dict(os.environ,DISKDEFS=str(work/'diskdefs'))
        rawfile=work/'disk.raw'
        def cpm(tool,*args):
            exe=str(binary_dir/tool) if binary_dir else shutil.which(tool)
            if not exe:raise ValueError(f'{tool} is required')
            p=subprocess.run([exe,'-f','bcm2ss',*map(str,args)],cwd=work,env=env,
                             text=True,capture_output=True)
            require(p.returncode==0,f'{tool}: {p.stdout} {p.stderr}')
            return p.stdout
        def prepare(raw):
            # Only the flat host fixture needs padding between track zero and one.
            rawfile.write_bytes(raw[:3328]+bytes(4864)+raw[3328:])
        def extract(name,expected):
            dest=work/'out.bin'
            cpm('cpmcp',rawfile,'0:'+name,dest)
            require(dest.read_bytes()==expected.ljust((len(expected)+127)//128*128,b'\x1a'),name)
        for role in ('System','Utilities'):
            blob=(out/f'Model-II-{role}-candidate.imd').read_bytes()
            _,_,raw=decoded(blob)
            prepare(raw)
            cpm('fsck.cpm','-n',rawfile)
            if role=='System':
                require(raw[512:516]==b'BOOT' and raw[1536:1543]==b'DIAG\xc3\x04\x10','ROM entry')
                protected=(raw[:384]+raw[1536:1664]+raw[512:1024]+raw[3328:3328+152*128])
                require(protected==payload,'physical package differs from checked SYSTEM.SYS')
                extract('system.sys',package)
                extract('path.com',(out.parent/'utilities/PATH.COM').read_bytes())
                for module in ('M2SCRN','ADM3A','VT52','ANSI'):
                    name=module+'.RSX'
                    extract(name,(out.parent/'rsx'/name).read_bytes())
            for name in ('CONFIG','DUP','SYSGEN','RSX','CPX','TIME','STAT'):
                extract(name+'.com',(out.parent/'utilities'/(name+'.COM')).read_bytes())
            result[role]=hashlib.sha256(blob).hexdigest()
        n=290*2048
        pattern=(bytes(range(251))*(n//251+1))[:n]
        blob=image(bytes(20480),[('FINAL.BIN',pattern)],bootable=False)
        comment,tracks,raw=decoded(blob)
        require(raw[-512:]==pattern[-512:],'last physical sector missing')
        prepare(raw)
        extract('final.bin',pattern)
        cpm('cpmrm',rawfile,'0:final.bin')
        (work/'write.bin').write_bytes(pattern[::-1])
        cpm('cpmcp',rawfile,work/'write.bin','0:other.bin')
        extract('other.bin',pattern[::-1]);cpm('fsck.cpm','-n',rawfile)
        changed=rawfile.read_bytes()
        rebuilt=repack(comment,tracks,changed[:3328]+changed[8192:])
        require(decoded(rebuilt)[2][-512:]==pattern[::-1][-512:],'independent final-sector write lost')
        for files in ([('FULL.BIN',pattern+b'x')],[(f'F{i}.DAT',b'') for i in range(129)]):
            try: image(bytes(20480),files,bootable=False)
            except ValueError: pass
            else: raise ValueError('overfull fixture accepted')
    return {'status':'PASS','checks':'physical surfaces, protected record map/CRC, independent cpmtools read/write and fsck, final block, disk and directory limits','sha256':result}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('artifacts',type=Path)
    p.add_argument('--cpmtools',type=Path)
    a=p.parse_args()
    print(json.dumps(check(a.artifacts.resolve(),a.cpmtools.resolve() if a.cpmtools else None),indent=2))
