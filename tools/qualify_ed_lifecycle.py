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


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--better',action='store_true')
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
    source=expanded_source();start=source.index('ED_START:');end=source.index('ED_BAD:')
    source=source[:start]+'''ED_START:
        LD SP,ED_STACK
        CALL EI_PARSE
        JP C,LT_BAD
        LD HL,6000H
        LD DE,0C000H
        CALL EB_INIT
        CALL EC_INIT
        CALL FS_SETUP
        JP C,LT_BAD
LT_LOOP:
        CALL EU_READ
        CP 'E'
        JP NZ,LT_LOOP
        CALL EF_DRAIN
        JP C,LT_BAD
        CALL FP_COMMIT
        JP C,LT_BAD
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
    source=source.replace('        CSEG\n        .PHASE  ','        ASEG\n        ORG     ').replace('        .DEPHASE\n','')
    binary=work/'EDTEST.COM';assemble(Path.home()/'bin/z80asm',source,binary,work/'test.lst',256)
    body=b'Old Mixed\r\nsecond line\r\n'
    for case in ('new','existing','split'):
        here=work/case;here.mkdir();disks=here/'disks';disks.mkdir()
        if args.better:shutil.copy2(args.diskdefs,here/'diskdefs')
        for drive in ('a','b'):shutil.copy2(template,disks/f'drive{drive}.dsk')
        def copy(host,drive,name):subprocess.run(['cpmcp','-T','raw','-f',fmt,str(disks/f'drive{drive}.dsk'),str(host),'0:'+name],cwd=here,check=True)
        copy(binary,'a','EDTEST.COM')
        if case!='new':
            seed=here/'seed.txt';seed.write_bytes(body+b'\x1a');copy(seed,'a','CASE.TXT')
        operand=b'CASE.TXT'+(b' B:' if case=='split' else b'')
        session(Path.home()/'projects/git/z80pack/cpmsim/cpmsim',disks,[
            (b'EDTEST '+operand+b'\r',b'*',10),
            (b'iNEW\x1a\r',b'*',10),(b'E\r',(b'B0>_ ' if case=='split' else b'A0>_ ') if args.better else b'A>',10),
            (b'A:BYE\r',b'System halted',10)],here/'transcript.bin',initial_prompt=b'A0>_ ' if args.better else b'A>')
        assert b'LIFECYCLE FAILED' not in (here/'transcript.bin').read_bytes()
        def extract(drive,name):
            target=here/(drive+'-'+name)
            subprocess.run(['cpmcp','-T','raw','-f',fmt,str(disks/f'drive{drive}.dsk'),'0:'+name,str(target)],cwd=here,check=True)
            return target.read_bytes()
        result=extract('b' if case=='split' else 'a','case.txt')
        expected=b'NEW'+(body if case!='new' else b'')
        assert result==expected+b'\x1a'*((-len(expected))%128),(case,result)
        backup=extract('a','case.bak')
        assert backup.rstrip(b'\x1a')==(body if case!='new' else b''),(case,backup)
    platform='BetterCP/M' if args.better else 'stock CP/M'
    print(f'PASS: live new/existing/split setup, completion and backup publication on {platform}; {work}')


if __name__=='__main__':main()
