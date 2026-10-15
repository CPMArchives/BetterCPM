#!/usr/bin/env python3
"""Run real ANSI load/movement, screen utility and unload on private cpmsim media."""
import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path
from test_z80pack_sysgen_install import session
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image',type=Path,default=ROOT/'build/z80pack/disks/library/BetterCPM-Distribution-z80pack-332K.dsk')
    parser.add_argument('--diskdefs',type=Path,required=True)
    parser.add_argument('--simulator',type=Path,default=Path.home()/'projects/git/z80pack/cpmsim/cpmsim')
    parser.add_argument('--rom-build',type=Path,help='Qualify protected ROM from this platform build instead of --image')
    parser.add_argument('--z80pack-source',type=Path,default=Path.home()/'projects/git/z80pack')
    args=parser.parse_args()
    parent=ROOT/'build/ansi-development/live'
    parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='cpmsim-',dir=parent))
    disks=work/'disks'
    simulator=args.simulator
    rom_image=None
    if args.rom_build:
        from test_cpmsim_rom_guard import build_guarded_simulator,prove_guard_primitives
        simulator=build_guarded_simulator(args.z80pack_source,work)
        probes=work/'guard-probes';probes.mkdir()
        prove_guard_primitives(simulator,probes)
        shutil.copytree(args.rom_build/'rom-disks',disks,symlinks=False)
        rom_image=args.rom_build/'rom/rom-boot.hex'
    else:
        disks.mkdir()
        shutil.copy2(args.image,disks/'drivea.dsk')
    image=disks/'drivea.dsk'
    shutil.copy2(args.diskdefs,work/'diskdefs')
    if rom_image:
        # Only disposable qualification media: free development-test directory slots.
        for name in ('RSX2TST.COM','RSXTEST.COM','STATTST.COM','SVCTEST.COM','HELLO.RSX'):
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
    for name,path in [('ANSI.RSX','build/ansi-development/ANSI.RSX'),
                      ('ANSITST.COM','build/ansi-development/ANSITST.COM'),
                      ('HELLO.RSX','build/rsx/HELLO.RSX')]:
        existing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        if name in existing:
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(ROOT/path),'0:'+name],cwd=work,check=True)
    prompt=b'A0>_ '
    trace=session(simulator,disks,[
        (b'ANSITST /VER\r',b'BetterCP/M ANSITST 1.0 (Build 001)',10),
        (b'',prompt,10),
        (b'RSX LOAD HELLO\r',prompt,30),
        (b'RSX LOAD ANSI\r',prompt,30),
        (b'RSX UNLOAD HELLO\r',prompt,30),
        (b'ANSITST\r',b'Press a key to continue.',30),
        (b' ',b'Press a key to continue.',10),
        (b' ',b'ANSI monitor exercise complete.',10),
        (b'',prompt,10),
        (b'RSX UNLOAD ANSI\r',prompt,30),
        (b'RSX LIST\r',b'TPA available: 53K',10),
        (b'BYE\r',b'System halted',10)],work/'transcript.bin',rom_image=rom_image,rom_start='DF00' if rom_image else None)
    if rom_image:
        assert b'ROM QUALIFICATION ACTIVE START=DF00' in trace
        assert b'ROM WRITE VIOLATION' not in trace
    import pyte
    screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
    stream.feed(trace.split(b'Press a key to continue.',1)[0].decode('ascii',errors='replace'))
    assert screen.display[5][10:35]=='Marker: row 5, column 10.'
    assert screen.display[7].startswith('Normal Reverse Normal')
    assert screen.buffer[7][7].reverse and not screen.buffer[7][0].reverse
    assert screen.display[9].rstrip()=='Erase KEEP'
    assert b'ANSI monitor foundation test' in trace
    assert b'Parser reset: readable text' in trace
    assert b'No RSXs loaded' in trace
    assert b'No MCON provider loaded' not in trace
    print(f'PASS: live cpmsim ANSI load/movement, two utility phases, unload/53K and BYE; {work}')


if __name__=='__main__':main()
