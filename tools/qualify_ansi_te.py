#!/usr/bin/env python3
"""Qualify the unchanged upstream TE VT100 editor on private cpmsim media."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reference',type=Path,required=True,help='Local MiguelVis/te checkout; never modified')
    p.add_argument('--image',type=Path,default=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk')
    p.add_argument('--diskdefs',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=p.parse_args()
    parent=ROOT/'build/ansi-development/te';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    disks=work/'disks';disks.mkdir();image=disks/'drivea.dsk'
    shutil.copy2(args.image,image);shutil.copy2(args.diskdefs,work/'diskdefs')
    document=work/'ANSITEST.TXT';document.write_bytes(b'ORIGINAL ANSI DOCUMENT\r\n\x1a')
    files=[('ANSI.RSX',ROOT/'build/ansi-development/ANSI.RSX'),('TE.COM',args.reference/'TE_WS100.COM'),('TE.CF',args.reference/'TE_WS100.CF'),('ANSITEST.TXT',document)]
    for name,path in files:
        names=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        if name in names:subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+name],cwd=work,check=True)
    prompt=b'A0>_ '
    trace=session(args.simulator,disks,[
        (b'RSX LOAD ANSI\r',prompt,30),
        (b'CLS\r',prompt,10),
        (b'TE ANSITEST.TXT\r',b' = menu',30),
        (b'ANSI EDIT CHECK\x1b',b' = back): ',20),
        (b'S',b' = back): ',20),
        (b'X',prompt,20),
        (b'RSX UNLOAD ANSI\r',prompt,30),
        (b'RSX LIST\r',b'TPA available: 53K',10),
        (b'BYE\r',b'System halted',10)],work/'transcript.bin')
    import pyte
    for columns,rows in ((80,25),(100,40)):
        screen=pyte.Screen(columns,rows);stream=pyte.Stream(screen)
        stream.feed(trace.split(b' = menu',1)[0].decode('ascii',errors='replace'))
        assert screen.display[0].startswith('te: ANSITEST.TXT')
        assert screen.display[2].startswith('  1|ORIGINAL ANSI DOCUMENT')
        (work/f'screen-{columns}x{rows}.txt').write_text('\n'.join(screen.display)+'\n')
    saved=work/'saved.txt' 
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),'0:ansitest.txt',str(saved)],cwd=work,check=True)
    assert b'ANSI EDIT CHECK' in saved.read_bytes()
    assert b'No RSXs loaded' in trace
    commit=subprocess.check_output(['git','-C',str(args.reference),'rev-parse','HEAD'],text=True).strip()
    (work/'reference.txt').write_text('https://github.com/MiguelVis/te\ncommit '+commit+'\n'+'\n'.join(f'{path.name}: {hashlib.sha256(path.read_bytes()).hexdigest()}' for _,path in files if path.parent==args.reference)+'\n')
    print(f'PASS: unchanged TE VT100 editor opens, edits, saves, exits; ANSI unload restores 53K; {work}')


if __name__=='__main__':main()
