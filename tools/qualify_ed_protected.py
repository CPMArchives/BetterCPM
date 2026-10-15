#!/usr/bin/env python3
"""Protected-source entry/quit behavior against DRI ED and the development loop."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from qualify_ed_lifecycle import build_testloop,ROOT
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--save-readonly',action='store_true')
    p.add_argument('--split',action='store_true')
    p.add_argument('--readonly-system',action='store_true')
    p.add_argument('--users',action='store_true',help='BetterCP/M source A7 and output user 19')
    p.add_argument('--oracle',action='store_true');p.add_argument('--better',action='store_true');p.add_argument('--diskdefs',type=Path)
    args=p.parse_args();assert not (args.oracle and args.better)
    assert not args.users or args.better
    assert not args.readonly_system or args.save_readonly
    su,du=(7,19) if args.users else (0,0)
    template=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(template.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    fmt='ibm-3740';prompt=b'A>'
    if args.better:
        assert args.diskdefs
        template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk';fmt='bettercpm-default';prompt=b'A0>_ '
    parent=ROOT/'build/ed-development/protected';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));binary=build_testloop(work)
    if args.oracle:
        binary=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
        assert hashlib.sha256(binary.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    for attr in (('rs' if args.readonly_system else 'r',) if args.save_readonly else ('r','s','rs')):
        here=work/attr;here.mkdir();disks=here/'disks';disks.mkdir();image=disks/'drivea.dsk';shutil.copy2(template,image)
        outimage=disks/'driveb.dsk' if args.split else image
        if args.split:shutil.copy2(template,outimage)
        if args.better:shutil.copy2(args.diskdefs,here/'diskdefs')
        def tool(*cmd):return subprocess.run(cmd,cwd=here,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
        def put(host,name,user=0):tool('cpmcp','-T','raw','-f',fmt,str(image),str(host),str(user)+':'+name)
        put(binary,'EDTEST.COM')
        original=here/'source.txt';original.write_bytes(b'Protected original\r\n\x1a');put(original,'CASE.TXT',su)
        backup=here/'backup.txt';backup.write_bytes(b'Older backup\r\n\x1a');put(backup,'CASE.BAK',su)
        tool('cpmchattr','-T','raw','-f',fmt,str(image),attr,str(su)+':CASE.TXT')
        operand=(f'A{su}:CASE.TXT' if args.users else 'CASE.TXT')
        if args.split or args.users:operand+=' '+('B' if args.split else 'A')+(str(du) if args.users else '')+':'
        commands=[(b'EDTEST '+operand.encode()+b'\r',prompt if attr=='s' else b'*',10)]
        if args.save_readonly:
            commands.extend([(b'iCHANGE\x1a\r',b'*',10),(b'E\r',b'File R/O',10),(b'\r',prompt,10)])
        elif attr!='s':commands.extend([(b'iCHANGE\x1a\r',b'*',10),(b'Q\r',b'(Y/N)?',10),(b'Y',prompt,10)])
        commands.append((b'BYE\r',b'System halted',10))
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin',initial_prompt=prompt)
        if attr=='s':assert b'"SYSTEM" FILE NOT ACCESSIBLE' in trace and b'READ/ONLY' not in trace
        else:assert b'** FILE IS READ/ONLY **' in trace and b'NOT ACCESSIBLE' not in trace
        exported=here/'result.txt';tool('cpmcp','-T','raw','-f',fmt,str(image),str(su)+':CASE.TXT',str(exported))
        assert exported.read_bytes().rstrip(b'\x1a')==original.read_bytes().rstrip(b'\x1a')
        names=tool('cpmls','-T','raw','-f',fmt,str(image)).upper()
        outnames=tool('cpmls','-T','raw','-f',fmt,str(outimage)).upper()
        assert (b'CASE.$$$' in outnames)==args.save_readonly
        assert (b'CASE.BAK' in names)==(attr=='s')
        if args.save_readonly:
            recovery=here/'recovery.txt';tool('cpmcp','-T','raw','-f',fmt,str(outimage),str(du)+':CASE.$$$',str(recovery))
            assert recovery.read_bytes().rstrip(b'\x1a')==b'CHANGE'+original.read_bytes().rstrip(b'\x1a')
    platform='DRI oracle' if args.oracle else ('BetterCP/M' if args.better else 'new code / stock CP/M')
    scope='RO save diagnostic/acknowledgment and original/recovery preservation' if args.save_readonly else 'RO/SYS entry precedence, notices, quit preservation and backup/temp states'
    print(f'PASS: {scope} on {platform}; {work}')


if __name__=='__main__':main()
