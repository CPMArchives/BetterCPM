#!/usr/bin/env python3
"""Record/compare DRI transfer lifetime across O/H on isolated CP/M disks."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from qualify_ed_lifecycle import build_testloop,ROOT
from test_z80pack_sysgen_install import session


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--oracle',action='store_true');p.add_argument('--better',action='store_true');p.add_argument('--diskdefs',type=Path);p.add_argument('--compare',type=Path);p.add_argument('--same-du-only',action='store_true');args=p.parse_args()
    assert not (args.oracle and args.better)
    template=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(template.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    fmt='ibm-3740';aprompt=b'A>';bprompt=b'B>'
    if args.better:
        assert args.diskdefs
        template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk';fmt='bettercpm-default';aprompt=b'A0>_ ';bprompt=b'B0>_ '
    parent=ROOT/'build/ed-development/transfer-lifetime';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent));binary=build_testloop(work)
    if args.oracle:
        binary=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
        assert hashlib.sha256(binary.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    results={};body=b'line one\r\nrest\r\n'
    cases=('same-O','same-H') if args.same_du_only else ('same-O','same-H','split-O','split-H')
    for case in cases:
        here=work/case;here.mkdir();disks=here/'disks';disks.mkdir()
        if args.better:shutil.copy2(args.diskdefs,here/'diskdefs')
        for letter in ('a','b'):shutil.copy2(template,disks/f'drive{letter}.dsk')
        def tool(*cmd):return subprocess.run(cmd,cwd=here,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
        a=disks/'drivea.dsk';seed=here/'seed.txt';seed.write_bytes(body+b'\x1a')
        for host,name in [(binary,'EDTEST.COM'),(seed,'CASE.TXT')]:tool('cpmcp','-T','raw','-f',fmt,str(a),str(host),'0:'+name)
        tail=b' B:' if case.startswith('split') else b''
        commands=[(b'EDTEST CASE.TXT'+tail+b'\r',b'*',10),(b'#a\r',b'*',10),(b'Bx\r',b'*',10)]
        if case.endswith('O'):commands.extend([(b'O\r',b'(Y/N)?',10),(b'Y',b'*',10)])
        else:commands.append((b'H\r',b'*',10))
        prompt=bprompt if case=='split-O' else aprompt
        commands.extend([(b'r\r',b'*',10),(b'E\r',prompt,10),(b'A:BYE\r',b'System halted',10)])
        trace=session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin',initial_prompt=aprompt)
        assert b'LIFECYCLE FAILED' not in trace and b'DISK OR DIRECTORY FULL' not in trace
        snapshot={'missing_R':b'BREAK "O"' in trace,'files':{}}
        for letter in ('a','b'):
            image=disks/f'drive{letter}.dsk'
            names=tool('cpmls','-T','raw','-f',fmt,str(image)).upper().split()
            for name in ('CASE.TXT','CASE.BAK','CASE.$$$','X$$$$$$$.LIB'):
                key=letter+':'+name
                if name.encode() not in names:snapshot['files'][key]=None;continue
                target=here/'extracted.bin';target.unlink(missing_ok=True)
                tool('cpmcp','-T','raw','-f',fmt,str(image),'0:'+name,str(target))
                snapshot['files'][key]=target.read_bytes().rstrip(b'\x1a').hex()
        results[case]=snapshot
    report=work/'results.json';report.write_text(json.dumps(results,indent=2)+'\n')
    baseline=args.compare
    if baseline is None:
        baseline=ROOT/('tools/fixtures/ed-transfer-lifetime-dri.json' if args.oracle else 'tools/fixtures/ed-transfer-lifetime-safe.json')
    if baseline:
        expected=json.loads(baseline.read_text())
        assert results=={case:expected[case] for case in cases},report
    verdict='PASS' if baseline else 'RECORDED'
    print(f'{verdict}: transfer O/H lifecycle campaign; {report}')


if __name__=='__main__':main()
