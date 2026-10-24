#!/usr/bin/env python3
"""Direct COPY/CHECK and refusal preserve the same real-media safeguards."""
from pathlib import Path
import argparse, shutil, subprocess, tempfile
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='dup-cli-media-') as t:
        w=Path(t);shutil.copytree(a.image_dir/'disks',w/'disks');shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
        source=w/'disks/drivea.dsk';target=w/'disks/driveb.dsk'
        subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(source),'0:DUP.COM'],cwd=w,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(source),str(ROOT/'build/utilities/DUP.COM'),'0:DUP.COM'],cwd=w,check=True)
        before=source.read_bytes();target.write_bytes(b'\xa5'*len(target.read_bytes()));old=target.read_bytes()
        session(a.simulator,w/'disks',[(b'DUP /FORMAT B:\r',b'[Y/N]',30),(b'N',b'A0>_ ',30),(b'DUP /COPY A: B:\r',b'[Y/N]',30),(b'N',b'A0>_ ',30)])
        assert target.read_bytes()==old and source.read_bytes()==before
        report=ROOT/'build/test-results/dup-command-line';report.mkdir(parents=True,exist_ok=True)
        transcript=session(a.simulator,w/'disks',[
            (b'DUP /FORMAT A:\r',b'A0>_ ',30),
            (b'DUP /COPY A: B:\r',b'[Y/N]',30),
            (b'Y',b'A0>_ ',120),
            (b'DUP /CHECK B:\r',b'A0>_ ',120),
            (b'BYE /Y\r',b'System halted',30)],report/'cpmsim.txt')
        assert b'Copy complete; destination verified.' in transcript
        assert b'Unreadable sectors: 00000' in transcript
        assert b'protected system disk' in transcript
        assert source.read_bytes()==before
        assert target.read_bytes()==before,'copied sector payloads differ'
    print('PASS: direct COPY refusal, protected FORMAT, payload equality and read-only CHECK')
if __name__=='__main__':main()
