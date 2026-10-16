#!/usr/bin/env python3
"""Exercise SCX rendition through public service lookup on private cpmsim media."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
import pyte
from build_ccp import assemble
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]
SOURCE='''        ASEG
        ORG 0100H
        LD DE,START
        LD C,9
        CALL 5
        LD DE,REQUEST
        LD C,182
        CALL 5
        OR A
        JP NZ,FAILED
        LD HL,(REQUEST+12)
        LD (ENTRY),HL
        LD A,16
        CALL GO
        OR A
        JP NZ,FAILED
        LD DE,8
        ADD HL,DE
        LD A,(HL)
        AND 24
        CP 24
        JP NZ,FAILED
        LD HL,STYLE
        LD A,20
        CALL GO
        LD HL,6
        LD DE,11
        LD A,18
        CALL GO
        LD HL,MARK
        CALL TEXT
        LD B,7
        LD C,0
        LD A,6
        CALL GO
        LD C,'L'
        LD A,7
        CALL GO
        LD C,'N'
        LD A,21
        CALL GO
        LD HL,NORMAL
        LD A,20
        CALL GO
        LD HL,10
        LD DE,1
        LD A,18
        CALL GO
        LD HL,PASSED
        CALL TEXT
        LD DE,ENDING
        LD C,9
        CALL 5
        JP 0
TEXT:
        LD C,(HL)
        LD A,C
        OR A
        RET Z
        INC HL
        PUSH HL
        LD A,21
        CALL GO
        POP HL
        JR TEXT
GO:
        PUSH HL
        LD HL,(ENTRY)
        LD (TARGET+1),HL
        POP HL
TARGET:
        JP 0
FAILED:
        LD DE,ERROR
        LD C,9
        CALL 5
        JP 0
ENTRY: DW 0
REQUEST: DB 1,20,0,0,'SCRN',1,0
        DB 0,0,0,0,0,0,0,0,0,0
STYLE: DB 33,2,10,128,250,1,200,0,0
NORMAL: DB 0,0,0,0,0,0,0,0,0
START: DB 'SCXSTART',13,10,'$'
MARK: DB 'MARK',0
PASSED: DB 'SCX CHECK PASSED',0
ENDING: DB 13,10,'SCXEND',13,10,'$'
ERROR: DB 'SCX CHECK FAILED',13,10,'$'
        END
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--image',type=Path,default=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk')
    parser.add_argument('--rom-build',type=Path,help='use a matching protected-ROM build and its relocated overlays')
    args=parser.parse_args()
    parent=ROOT/'build/screen-rendition-live';parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='cpmsim-',dir=parent));disks=work/'disks'
    simulator=Path.home()/'projects/git/z80pack/cpmsim/cpmsim';rom_image=None
    container=ROOT/'build/system/R3PACK.RSX'
    if args.rom_build:
        args.rom_build=args.rom_build.resolve()
        from test_cpmsim_rom_guard import build_guarded_simulator,prove_guard_primitives
        simulator=build_guarded_simulator(Path.home()/'projects/git/z80pack',work)
        probes=work/'guard-probes';probes.mkdir();prove_guard_primitives(simulator,probes)
        shutil.copytree(args.rom_build/'rom-disks',disks,symlinks=False)
        rom_image=args.rom_build/'rom/rom-boot.hex'
        container=args.rom_build/'rom/rsx-overlays/R3PACK.RSX'
    else:
        disks.mkdir();shutil.copy2(args.image,disks/'drivea.dsk')
    image=disks/'drivea.dsk';shutil.copy2(args.diskdefs,work/'diskdefs')
    if rom_image:
        # Free test-only directory entries on the disposable ROM fixture.
        names=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        for name in ('RSX2TST.COM','RSXTEST.COM'):
            if name in names:subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
    (work/'test.mac').write_text(SOURCE)
    assemble(Path.home()/'bin/z80asm',SOURCE,work/'SCXTEST.COM',work/'test.lst',0x100)
    for name,path in [('R3PACK.RSX',container),('ANSISCRN.RSX',ROOT/'build/screen-backends/ANSISCRN.RSX'),('SCXTEST.COM',work/'SCXTEST.COM')]:
        existing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        if name in existing:subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+name],cwd=work,check=True)
    prompt=b'A0>_ '
    trace=session(simulator,disks,[
        (b'RSX LOAD ANSISCRN\r',prompt,30),(b'SCXTEST\r',b'SCXEND',30),
        (b'',prompt,30),(b'RSX UNLOAD ANSISCRN\r',prompt,30),
        (b'RSX LIST\r',b'TPA available: 53K',30),(b'BYE\r',b'System halted',30)],work/'transcript.bin',rom_image=rom_image,rom_start='DF00' if rom_image else None)
    if rom_image:
        assert b'ROM QUALIFICATION ACTIVE START=DF00' in trace and b'ROM WRITE VIOLATION' not in trace
    assert b'SCX CHECK FAILED' not in trace and b'No RSXs loaded' in trace
    fragment=trace.split(b'SCXSTART\r\n',1)[1].split(b'SCXEND',1)[0]
    screen=pyte.Screen(80,24);pyte.Stream(screen).feed(fragment.decode('ascii'))
    assert screen.display[5][10:14]=='MARK'
    mark=screen.buffer[5][10];assert mark.reverse and mark.bold and mark.fg=='0a80fa'
    assert screen.buffer[7][0].data=='L' and not screen.buffer[7][0].reverse
    assert screen.buffer[7][1].data=='N' and screen.buffer[7][1].reverse
    assert screen.buffer[7][1].fg=='0a80fa'
    assert screen.display[9].startswith('SCX CHECK PASSED')
    print(f'PASS live public SCRN lookup, capability discovery, RGB/reverse rendering, legacy/styled switching, unload/53K: {work}')


if __name__=='__main__':main()
