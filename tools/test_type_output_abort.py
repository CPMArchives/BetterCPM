#!/usr/bin/env python3
"""Verify ordinary TYPE output uses standard BDOS Ctrl-S/Ctrl-C warm boot."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--image-dir',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    work=a.report.resolve();work.mkdir(parents=True,exist_ok=False)
    shutil.copytree(a.image_dir/'disks',work/'disks');shutil.copy2(a.image_dir/'diskdefs',work/'diskdefs')
    disk=work/'disks/drivea.dsk'
    def cpm(tool,*values):
        subprocess.run([tool,'-T','raw','-f','bettercpm-default',str(disk),*map(str,values)],cwd=work,check=True,stdout=subprocess.DEVNULL)
    cpm('cpmrm','0:*.*');cpm('cpmcp',ROOT/'build/utilities/TYPE.COM','0:TYPE.COM');cpm('cpmcp',ROOT/'build/cpx/RCP.CPX','0:RCP.CPX')
    data=b'CANCEL TEST\r\n'*10000+b'\x1a';(work/'LONG.TXT').write_bytes(data);cpm('cpmcp',work/'LONG.TXT','3:LONG.TXT')
    original=disk.read_bytes();sim=Path.home()/'projects/git/z80pack/cpmsim/cpmsim'
    for i,command in enumerate((':TYPE A3:LONG.TXT','TYPE A3:LONG.TXT')):
        text=session(sim,work/'disks',[(b'A0:\r',b'A0>_ ',60),(command.encode()+b'\r',b'CANCEL TEST',60),(b'\x13\x03',b'A3>_ ',60)],work/f'case-{i}.txt')
        assert text.count(b'CANCEL TEST')<10000,'Ctrl-C did not abort ordinary output'
        assert disk.read_bytes()==original,'output abort changed source disk'
    (work/'evidence.json').write_text(json.dumps({'result':'PASS','type_sha256':hashlib.sha256((ROOT/'build/utilities/TYPE.COM').read_bytes()).hexdigest(),'ordinary_abort':'BDOS WBOOT retains active A3 DU','whole_disk_unchanged':True},indent=2)+'\n')
    print('PASS: resident/transient TYPE ordinary-output Ctrl-C warm boot, active DU and unchanged source')
if __name__=='__main__':main()
