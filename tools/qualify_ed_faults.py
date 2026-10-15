#!/usr/bin/env python3
"""Inject BDOS status failures into a live test-only ED loop on copied media."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from qualify_ed_lifecycle import build_testloop,ROOT
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--diskdefs',type=Path,required=True);args=p.parse_args()
    parent=ROOT/'build/ed-development/faults';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    original=b'x'*400+b'\r\n\x1a'
    for function in (20,21):
        here=work/str(function);here.mkdir();disks=here/'disks';disks.mkdir()
        shutil.copy2(args.diskdefs,here/'diskdefs');image=disks/'drivea.dsk';shutil.copy2(template,image)
        binary=build_testloop(here,fault=function)
        seed=here/'seed.txt';seed.write_bytes(original)
        def tool(*cmd):return subprocess.run(cmd,cwd=here,check=True,stdout=subprocess.PIPE).stdout
        for host,name in [(binary,'EDTEST.COM'),(seed,'CASE.TXT')]:tool('cpmcp','-T','raw','-f','bettercpm-default',str(image),str(host),'0:'+name)
        commands=[(b'EDTEST CASE.TXT\r',b'*',10)]
        if function==20:commands.append((b'a\r',b'A0>_ ',10))
        else:commands.extend([(b'#a\r',b'*',10),(b'#w\r',b'A0>_ ',10)])
        commands.append((b'BYE\r',b'System halted',10))
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        assert b'DISK OR DIRECTORY FULL' in trace and b'BREAK' not in trace
        def extract(name):
            path=here/name.replace('$','D')
            tool('cpmcp','-T','raw','-f','bettercpm-default',str(image),'0:'+name,str(path));return path.read_bytes()
        assert extract('CASE.TXT').rstrip(b'\x1a')==original.rstrip(b'\x1a')
        recovery=extract('CASE.$$$')
        assert recovery==(b'x'*128 if function==21 else b''),(function,recovery)
        assert b'CASE.BAK' not in tool('cpmls','-T','raw','-f','bettercpm-default',str(image)).upper()
    print(f'PASS: live injected A read failure and W second-record failure preserve original and recovery output; {work}')


if __name__=='__main__':main()
