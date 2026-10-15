#!/usr/bin/env python3
"""Live full-DU save/restart/quit isolation for the unshipped ED test loop."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from qualify_ed_lifecycle import build_testloop,ROOT
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--diskdefs',type=Path,required=True);args=p.parse_args()
    parent=ROOT/'build/ed-development/du';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));binary=build_testloop(work)
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    body=b'Original in user seven\r\n'
    for case in ('same-drive','split','head','quit'):
        here=work/case;here.mkdir();disks=here/'disks';disks.mkdir();shutil.copy2(args.diskdefs,here/'diskdefs')
        for drive in ('a','b'):shutil.copy2(template,disks/f'drive{drive}.dsk')
        def tool(*cmd):return subprocess.run(cmd,cwd=here,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
        def put(data,drive,user,name):
            path=here/'staging.bin';path.write_bytes(data)
            tool('cpmcp','-T','raw','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),str(path),f'{user}:'+name)
        def get(drive,user,name):
            path=here/'extracted.bin'
            path.unlink(missing_ok=True)
            result=subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(disks/f'drive{drive}.dsk'),f'{user}:'+name,str(path)],cwd=here,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            return None if result.returncode or not path.exists() else path.read_bytes().rstrip(b'\x1a')
        put(binary.read_bytes(),'a',0,'EDTEST.COM')
        put(body+b'\x1a','a',7,'CASE.TXT')
        put(b'Caller sentinel\x1a','a',0,'CASE.TXT');put(b'Other drive sentinel\x1a','b',0,'CASE.TXT')
        outdrive='a' if case=='same-drive' else 'b'
        commands=[(f'EDTEST A7:CASE.TXT {outdrive.upper()}19:\r'.encode(),b'*',10),
                  (b'iNEW\x1a\r',b'*',10)]
        if case=='quit':
            commands.extend([(b'Q\r',b'(Y/N)?',10),(b'Y',b'A0>_ ',10)])
        else:
            if case=='head':commands.extend([(b'H\r',b'*',10),(b'iAGAIN\x1a\r',b'*',10)])
            exitdu=b'A7' if case=='head' else outdrive.upper().encode()+b'19'
            commands.extend([(b'E\r',exitdu+b'>_ ',10),(b'A0:\r',b'A0>_ ',10)])
        commands.append((b'BYE\r',b'System halted',10))
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        assert b'LIFECYCLE FAILED' not in trace and b'DISK OR DIRECTORY FULL' not in trace
        assert get('a',0,'CASE.TXT')==b'Caller sentinel'
        assert get('b',0,'CASE.TXT')==b'Other drive sentinel'
        if case=='quit':
            assert get('a',7,'CASE.TXT')==body and get('b',19,'CASE.$$$') is None
        elif case=='head':
            assert get('a',7,'CASE.TXT')==b'AGAINNEW'+body
            assert get('b',19,'CASE.BAK')==b'NEW'+body
        else:
            assert get(outdrive,19,'CASE.TXT')==b'NEW'+body
            assert get('a',7,'CASE.BAK')==body and get('a',7,'CASE.TXT') is None
    print(f'PASS: A7/A19/B19 save, split H, caller-DU Q, exit prompts and user-zero sentinels; {work}')


if __name__=='__main__':main()
