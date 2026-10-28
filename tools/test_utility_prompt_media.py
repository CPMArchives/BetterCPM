#!/usr/bin/env python3
"""Exercise inline help from exact paired candidate volumes under BetterCP/M."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
from test_z80pack_sysgen_install import session
from test_lbr import archive,entry,with_crcs

ROOT=Path(__file__).resolve().parents[1]
sha=lambda b:hashlib.sha256(b).hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--utilities',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args();w=a.report.resolve();w.mkdir(parents=True,exist_ok=False)
    shutil.copytree(a.image_dir/'disks',w/'disks')
    shutil.copy2(a.image_dir/'diskdefs',w/'diskdefs')
    volumes={letter:(a.utilities/name).read_bytes() for letter,name in (
        ('b','BetterCPM-Utilities-z80pack-332K.dsk'),('c','BetterCPM-NOAH-z80pack-332K.dsk'))}
    for letter,data in volumes.items():(w/f'disks/drive{letter}.dsk').write_bytes(data)
    def cpm(*args):
        return subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(w/'disks/drivea.dsk'),*map(str,args)],cwd=w,check=True,capture_output=True)
    fixture=b'123456789'+b'\x1a'*119
    files=[('FIX.DAT',fixture,'31:FIX.DAT'),('CRC.LST',b'old CRC list','31:CRC.LST'),
           ('MD5SUM.LST',b'old MD5 list','31:MD5SUM.LST'),
           ('MEMBER.LBR',with_crcs(archive([entry(b'FIX     DAT')],fixture)),'3:MEMBER.LBR')]
    for name,data,destination in files:
        (w/name).write_bytes(data);cpm(w/name,destination)
    commands=[]
    for name,listname in [('CRCKSUM','CRC.LST'),('MD5SUM','MD5SUM.LST')]:
        commands.append((f'B:{name} A31:FIX.DAT /LOCAL={listname}\r'.encode(),b'Overwrite? (Y/n/a/?) ',30))
        for _ in range(2):commands.append((b'?',b'Y Yes, N No, A All, ? Help',10));commands.append((b'',b'Overwrite? (Y/n/a/?) ',10))
        commands.append((b'N',b'A0>_ ',30))
    commands.append((b'C:\r',b'C0>_ ',30))
    commands.append((b'NOAH /X A3:MEMBER.LBR A31:\r',b'Replace? Y/N/A/C/? [N]: ',30))
    for _ in range(2):
        commands.append((b'?',b'Y Yes, N No, A All, C Cancel, ? Help',10))
        commands.append((b'',b'A31:FIX.DAT exists. Replace? Y/N/A/C/? [N]: ',10))
    commands.append((b'N',b'C0>_ ',30))
    text=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',w/'disks',commands,w/'transcript.txt').decode('ascii',errors='replace')
    assert text.count('Y Yes, N No, A All, ? Help')==4,text
    assert text.count('Y Yes, N No, A All, C Cancel, ? Help')==2,text
    for name,data,destination in files:
        out=w/('READ-'+name);cpm(destination,out)
        assert out.read_bytes()[:len(data)]==data,(name,'changed')
    for letter,before in volumes.items():assert (w/f'disks/drive{letter}.dsk').read_bytes()==before
    record={'status':'PASS','scope':'Repeated inline help then No; exact packaged primary and NOAH companion; unchanged target files and B/C images',
            'volumes':{letter:sha(data) for letter,data in volumes.items()},
            'binaries':{name:sha((ROOT/'build/utilities'/name).read_bytes()) for name in ('CRCKSUM.COM','MD5SUM.COM','NOAH.COM','NOAH.OVL')}}
    (w/'evidence.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Packaged CRCKSUM/MD5SUM/NOAH prompt-help cpmsim campaign: PASS')


if __name__=='__main__':main()
