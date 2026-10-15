#!/usr/bin/env python3
"""Exercise real full media through ED's unmodified entry on private images."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
FMT='bettercpm-default'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--diskdefs',type=Path,required=True);args=p.parse_args()
    parent=ROOT/'build/ed-development/capacity';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));results=[]
    template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
    for case in ('directory-full','disk-full','partial-output'):
        here=work/case;here.mkdir();disks=here/'disks';disks.mkdir()
        shutil.copy2(args.diskdefs,here/'diskdefs')
        adisk=disks/'drivea.dsk';bdisk=disks/'driveb.dsk';shutil.copy2(template,adisk)
        def tool(*cmd,check=True):return subprocess.run(cmd,cwd=here,check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        bdisk.write_bytes(bytes(template.stat().st_size))
        tool('mkfs.cpm','-f',FMT,str(bdisk))
        def put(host,name,user=7,check=True):return tool('cpmcp','-T','raw','-f',FMT,str(bdisk),str(host),f'{user}:'+name,check=check)
        tool('cpmcp','-T','raw','-f',FMT,str(adisk),str(ROOT/'build/ed-development/EDDEV.COM'),'0:EDDEV.COM')
        source=b'OLD\r\n' if case!='partial-output' else b'x'*6000+b'\r\n'
        seed=here/'seed.txt';seed.write_bytes(source+b'\x1a');put(seed,'CASE.TXT')
        empty=here/'empty.bin';empty.write_bytes(b'')
        if case=='directory-full':
            for i in range(63):put(empty,f'F{i:03}.DAT',user=0)
            assert len([n for n in tool('cpmls','-T','raw','-f',FMT,str(bdisk)).stdout.split() if b'.' in n])==64
            probe=put(empty,'PROBE.DAT',check=False);assert probe.returncode!=0
        else:
            if case=='partial-output':
                reserve=here/'reserve.bin';reserve.write_bytes(b'r'*2048);put(reserve,'RESERVE.DAT')
            filler=here/'filler.bin';filler.write_bytes(b'f'*(512*1024))
            filled=put(filler,'FILLER.DAT',user=0,check=False)
            assert filled.returncode!=0 and b'full' in filled.stderr.lower(),filled
            probe=here/'probe.bin';probe.write_bytes(b'p')
            blocked=put(probe,'PROBE.DAT',check=False)
            assert blocked.returncode!=0 and b'full' in blocked.stderr.lower(),blocked
            # A failed host write may leave its empty directory entry.
            tool('cpmrm','-T','raw','-f',FMT,str(bdisk),'7:PROBE.DAT',check=False)
            assert len([n for n in tool('cpmls','-T','raw','-f',FMT,str(bdisk)).stdout.split() if b'.' in n])<64
            if case=='partial-output':tool('cpmrm','-T','raw','-f',FMT,str(bdisk),'7:RESERVE.DAT')
        original=here/'original-records.bin'
        tool('cpmcp','-T','raw','-f',FMT,str(bdisk),'7:CASE.TXT',str(original))
        before=hashlib.sha256(bdisk.read_bytes()).hexdigest()
        commands=[(b'EDDEV B7:CASE.TXT\r',b'A0>_ ' if case=='directory-full' else b'*',15)]
        if case!='directory-full':commands.extend([(b'iNEW\x1a\r',b'*',10),(b'E\r',b'A0>_ ',15)])
        commands.append((b'BYE\r',b'System halted',10))
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin')
        assert trace.count(b'DISK OR DIRECTORY FULL')==1 and b'BREAK' not in trace
        def extract(name):
            target=here/name.replace('$','D');target.unlink(missing_ok=True)
            tool('cpmcp','-T','raw','-f',FMT,str(bdisk),'7:'+name,str(target));assert target.exists()
            return target.read_bytes()
        assert extract('CASE.TXT')==original.read_bytes()
        listing=tool('cpmls','-T','raw','-f',FMT,str(bdisk)).stdout.lower().split()
        assert b'case.bak' not in listing
        if case=='directory-full':
            assert b'case.$$$' not in listing
            assert hashlib.sha256(bdisk.read_bytes()).hexdigest()==before
            retained=0
        else:
            data=extract('CASE.$$$');retained=len(data)
            expected=(b'NEW'+source)[:2048] if case=='partial-output' else b''
            assert data==expected,(case,len(data),len(expected))
        results.append({'case':case,'retained_work_bytes':retained,'result':'PASS'})
    (work/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    print(f'PASS: actual directory-full, disk-full and partial-output recovery via real ED entry; {work}')


if __name__=='__main__':main()
