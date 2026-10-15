#!/usr/bin/env python3
"""Live setup/save fixture, using an unshipped test-only ED command loop."""
import argparse
import hashlib
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_ed import expanded_source
from build_ccp import assemble
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def build_testloop(work,fault=None,real_entry=False):
    source=expanded_source();start=source.index('ED_START:');end=source.index('ED_BAD:')
    production=source
    source=source[:start]+'''ED_START:
        LD SP,ED_STACK
        CALL EI_PARSE
        JP C,LT_BAD
        LD HL,6000H
        LD DE,0C000H
        CALL EB_INIT
        CALL EC_INIT
        CALL FD_BEGIN
        JP C,LT_READY
LT_LOOP:
        CALL EU_READ
        JP C,LT_READY
        OR A
        JP Z,LT_LOOP
        CALL FD_ACT
        JP C,LT_READY
        OR A
        JP Z,LT_LOOP
LT_READY:
        JP 0
LT_BAD:
        LD A,(FP_STEP)
        ADD A,48
        LD E,A
        LD C,2
        CALL 5
        LD DE,LT_ERROR
        LD C,9
        CALL 5
        JP 0
LT_ERROR: DB 'LIFECYCLE FAILED',13,10,'$'
'''+source[end:]
    if real_entry:
        assert fault is None
        source=production
    if fault:
        assert fault in (16,20,21)
        source=source.replace('LT_LOOP:\n', '        CALL FZ_INSTALL\nLT_LOOP:\n',1)
        source=source.replace('LT_READY:\n        JP 0','LT_READY:\n        LD HL,(FZ_JUMP+1)\n        LD (6),HL\n        JP 0',1)
        shim='''
FZ_INSTALL:
        LD HL,(6)
        LD (FZ_JUMP+1),HL
        LD HL,FZ_GATE
        LD (6),HL
        RET
FZ_GATE:
        LD A,C
        CP FAULT_FUNCTION
        JP NZ,FZ_JUMP
        LD A,(FZ_COUNT)
        OR A
        JP Z,FZ_FAIL
        DEC A
        LD (FZ_COUNT),A
FZ_JUMP:
        JP 0
FZ_FAIL:
        LD A,2
        RET
FZ_COUNT: DB ALLOW_RECORDS
'''
        if fault==16:
            shim=shim.replace('FZ_FAIL:\n        LD A,2\n        RET','''FZ_FAIL:
        LD A,(FZ_ONCE)
        OR A
        JP Z,FZ_JUMP
        XOR A
        LD (FZ_ONCE),A
        LD A,255
        RET
FZ_ONCE: DB 1''')
        shim=shim.replace('FAULT_FUNCTION',str(fault)).replace('ALLOW_RECORDS',str(int(fault==21)))
        source=source.replace('; ED invocation only:',shim+'\n; ED invocation only:',1)
    source=source.replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
    binary=work/'EDTEST.COM';assemble(Path.home()/'bin/z80asm',source,binary,work/'test.lst',256)
    return binary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--better',action='store_true')
    parser.add_argument('--real-entry',action='store_true',help='Use the actual editor startup and TPA allocation')
    parser.add_argument('--oracle',action='store_true',help='Run the same stock-CP/M expectations against pinned DRI ED')
    parser.add_argument('--diskdefs',type=Path)
    args=parser.parse_args()
    template=Path.home()/'projects/git/z80pack/cpmsim/disks/library/cpm22-1.dsk'
    assert hashlib.sha256(template.read_bytes()).hexdigest()=='86ac7cb1bdd6bac05fe6299b50f94cb26a047022ce00135fbecf7bbc5d3303d2'
    fmt='ibm-3740'
    if args.better:
        assert args.diskdefs, '--diskdefs is required with --better'
        template=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk'
        fmt='bettercpm-default'
    parent=ROOT/'build/ed-development/lifecycle';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='run-',dir=parent))
    binary=build_testloop(work,real_entry=args.real_entry)
    if args.oracle:
        assert not args.better, '--oracle uses stock CP/M to avoid the known S1 baseline difference'
        binary=ROOT/'third_party/dri-ed/ED-CPM22-reference.COM'
        assert hashlib.sha256(binary.read_bytes()).hexdigest()=='adeeb92c897bd6a07579f06d163bd6ded549842203a5459c88a93d26c65fe85f'
    body=b'Old Mixed\r\nsecond line\r\n'
    for case in ('new','existing','split','quit','new-quit','original','head','split-head'):
        here=work/case;here.mkdir();disks=here/'disks';disks.mkdir()
        if args.better:shutil.copy2(args.diskdefs,here/'diskdefs')
        for drive in ('a','b'):shutil.copy2(template,disks/f'drive{drive}.dsk')
        def copy(host,drive,name):subprocess.run(['cpmcp','-T','raw','-f',fmt,str(disks/f'drive{drive}.dsk'),str(host),'0:'+name],cwd=here,check=True)
        copy(binary,'a','EDTEST.COM')
        if case not in ('new','new-quit'):
            seed=here/'seed.txt';seed.write_bytes(body+b'\x1a');copy(seed,'a','CASE.TXT')
        operand=b'CASE.TXT'+(b' B:' if case.startswith('split') else b'')
        commands=[(b'EDTEST '+operand+b'\r',b'*',10),(b'iNEW\x1a\r',b'*',10)]
        if case in ('quit','new-quit'):
            commands.extend([(b'Q\r',b'(Y/N)?',10),(b'Y',b'A0>_ ' if args.better else b'A>',10)])
        else:
            if case in ('original','head','split-head'):commands.append((b'U-V\r',b'*',10))
            if case=='original':commands.extend([(b'O\r',b'(Y/N)?',10),(b'Y',b'*',10),(b'iagain\x1a\r',b'*',10)])
            if case in ('head','split-head'):commands.extend([(b'H\r',b'*',10),(b'iagain\x1a\r',b'*',10)])
            prompt=(b'B0>_ ' if case=='split' else b'A0>_ ') if args.better else (b'B>' if case=='split' else b'A>')
            commands.append((b'E\r',prompt,10))
        commands.append((b'A:BYE\r',b'System halted',10))
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,commands,here/'transcript.bin',initial_prompt=b'A0>_ ' if args.better else b'A>')
        assert b'LIFECYCLE FAILED' not in (here/'transcript.bin').read_bytes()
        def extract(drive,name):
            target=here/(drive+'-'+name)
            subprocess.run(['cpmcp','-T','raw','-f',fmt,str(disks/f'drive{drive}.dsk'),'0:'+name,str(target)],cwd=here,check=True)
            return target.read_bytes()
        result=extract('b' if case=='split' else 'a','case.txt')
        if case in ('quit','new-quit'):
            expected=body if case=='quit' else b''
            assert result.rstrip(b'\x1a')==expected,(case,result)
            listing=subprocess.run(['cpmls','-T','raw','-f',fmt,str(disks/'drivea.dsk')],cwd=here,check=True,stdout=subprocess.PIPE).stdout.upper()
            assert b'CASE.$$$' not in listing and b'CASE.BAK' not in listing
            continue
        expected=b'NEW'+(body if case!='new' else b'')
        if case=='original':expected=b'AGAIN'+body
        if case in ('head','split-head'):expected=b'AGAINNEW'+body
        assert result==expected+b'\x1a'*((-len(expected))%128),(case,result)
        backup=extract('b' if case=='split-head' else 'a','case.bak')
        expected_backup=(b'NEW'+body) if case in ('head','split-head') else (body if case!='new' else b'')
        assert backup.rstrip(b'\x1a')==expected_backup,(case,backup)
    platform='BetterCP/M' if args.better else ('stock CP/M / DRI oracle' if args.oracle else 'stock CP/M')
    print(f'PASS: live setup/save, Q, O, H and split-DU H on {platform}; {work}')


if __name__=='__main__':main()
