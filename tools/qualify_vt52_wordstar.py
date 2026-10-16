#!/usr/bin/env python3
"""Exercise native VT52 WordStar edit/save on disposable media.

This checks application behavior and captured wire output, not physical display.
"""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference',type=Path,default=Path.home()/'CPM/z80pack/mosteksim/disks/CPM/WordStar_VT52.dsk')
    parser.add_argument('--image',type=Path,default=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk')
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    parent=ROOT/'build/vt52-development/wordstar';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    disks=work/'disks';disks.mkdir()
    image=disks/'drivea.dsk';shutil.copy2(args.image,image)
    shutil.copy2(args.diskdefs,work/'diskdefs')
    files=[('VT52.RSX',ROOT/'build/vt52-development/VT52.RSX')]
    for name in ['WS.COM','WSMSGS.OVR','WSOVLY1.OVR']:
        path=work/name
        subprocess.run(['cpmcp','-f','ibm-3740',str(args.reference),'0:'+name.lower(),str(path)],check=True)
        files.append((name,path))
    document=work/'VT52TEST.TXT';document.write_bytes(b'ORIGINAL VT52 DOCUMENT\r\n\x1a')
    files.append(('VT52TEST.TXT',document))
    for name,path in files:
        existing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        if name in existing:
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+name],cwd=work,check=True)
    prompt=b'A0>_ '
    trace=session(args.simulator,disks,[
        (b'RSX LOAD VT52\r',prompt,30),
        (b'CLS\r',prompt,10),
        (b'WS VT52TEST.TXT\r',b'WordStar',30),
        (b'VT52 EDIT CHECK\x0b\x18',prompt,30),
        (b'RSX UNLOAD VT52\r',prompt,30),
        (b'BYE\r',b'System halted',10)],work/'transcript.bin')
    native=trace[trace.index(b'\x1bH\x1bJ'):trace.index(b'RSX UNLOAD VT52')]
    assert b'\x1bY' in native and b'\x1b[' not in native
    saved=work/'saved.txt'
    subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),'0:vt52test.txt',str(saved)],cwd=work,check=True)
    assert b'VT52 EDIT CHECK' in saved.read_bytes(),saved.read_bytes()
    report=work/'reference.txt'
    report.write_text('\n'.join(f'{name}: {hashlib.sha256(path.read_bytes()).hexdigest()}' for name,path in files if name in ['WS.COM','WSMSGS.OVR','WSOVLY1.OVR'])+'\n')
    print(f'PASS: original VT52 WordStar opens, edits, saves and returns; provider unloads; {work}')


if __name__=='__main__':main()
