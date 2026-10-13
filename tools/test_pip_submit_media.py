#!/usr/bin/env python3
"""Qualify PIP error cancellation of the real A0 SUBMIT stream in cpmsim."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--image-dir',type=Path,default=ROOT/'build/z80pack')
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    args=parser.parse_args()
    report=ROOT/'build/test-results/pip-submit'
    report.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='pip-submit-',dir='/private/tmp') as tmp:
        work=Path(tmp)
        shutil.copytree(args.image_dir/'disks',work/'disks')
        shutil.copy2(args.image_dir/'diskdefs',work/'diskdefs')
        disk=work/'disks/drivea.dsk'
        def install(path,target):
            subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),str(path),target],cwd=work,check=True)
        existing=subprocess.run(['cpmls','-T','raw','-f','bettercpm-default',str(disk)],cwd=work,check=True,capture_output=True,text=True).stdout
        if 'submit.com' in existing.lower():
            subprocess.run(['cpmrm','-f','bettercpm-default',str(disk),'0:SUBMIT.COM'],cwd=work,check=True)
        install(ROOT/'build/pip-development/PIP.COM','0:PIPDEV.COM')
        install(ROOT/'build/utilities/SUBMIT.COM','0:SUBMIT.COM')
        keep=work/'KEEP.SUB';keep.write_bytes(b'UNRELATED USER QUEUE\r\n')
        install(keep,'7:$$$.SUB')
        source=work/'SOURCE.DAT';source.write_bytes(b'AFTER ERROR MUST NOT RUN\r\n')
        install(source,'7:SOURCE.DAT')
        batch=work/'PFAIL.SUB'
        batch.write_bytes(b'A7:\r\n:PIPDEV BAD\r\n:PIPDEV A7:AFTER.DAT=A7:SOURCE.DAT\r\n')
        install(batch,'0:PFAIL.SUB')
        transcript=session(args.simulator,work/'disks',[
            (b':SUBMIT PFAIL\r',b'INVALID FORMAT',60),
            (b'',b'A7>_ ',30),
        ],report/'transcript.txt')
        listing=subprocess.run(['cpmls','-T','raw','-f','bettercpm-default',str(disk)],cwd=work,check=True,capture_output=True,text=True).stdout
        assert 'after.dat' not in listing.lower(),listing
        recovered=work/'RECOVERED.SUB'
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disk),'7:$$$.SUB',str(recovered)],cwd=work,check=True)
        assert recovered.read_bytes()==keep.read_bytes()
        assert b'CANNOT CANCEL SUBMIT QUEUE' not in transcript
        assert listing.lower().count('$$$.sub')==1,listing
        (report/'listing.txt').write_text(listing)
    print('PASS: real PIP error cancels A0 SUBMIT, preserves A7 same-name file and suppresses next batch command')

if __name__=='__main__':
    main()
