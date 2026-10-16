#!/usr/bin/env python3
"""Qualify portable VT52 with the ANSI-host backend on private cpmsim media.

Captured bytes are checked; this does not qualify a physical terminal display.
"""
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
    parent=ROOT/'build/vt52-development/live'
    parent.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix='cpmsim-',dir=parent))
    disks=work/'disks'
    simulator=args.simulator
    rom_image=None
    if args.rom_build:
        args.rom_build=args.rom_build.resolve()
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
    files=[('R3PACK.RSX',ROOT/'build/system/R3PACK.RSX'),
           ('ANSISCRN.RSX',ROOT/'build/screen-backends/ANSISCRN.RSX'),
           ('VT52.RSX',ROOT/'build/vt52-development/VT52.RSX'),
           ('VT52TST.COM',ROOT/'build/vt52-development/VT52TST.COM'),
           ('HELLO.RSX',ROOT/'build/rsx/HELLO.RSX')]
    if rom_image:
        # ROM overlays carry relocated resident references; never replace them
        # with the ordinary RAM-profile container during qualification.
        files[0]=('R3PACK.RSX',args.rom_build/'rom/rsx-overlays/R3PACK.RSX')
    for name,path in files:
        existing=subprocess.check_output(['cpmls','-T','raw','-f','bettercpm-default',str(image)],cwd=work,text=True).upper().split()
        if name in existing:
            subprocess.run(['cpmrm','-T','raw','-f','bettercpm-default',str(image),'0:'+name],cwd=work,check=True)
        subprocess.run(['cpmcp','-T','raw','-f','bettercpm-default',str(image),str(path),'0:'+name],cwd=work,check=True)
    prompt=b'A0>_ '
    trace=session(simulator,disks,[
        (b'VT52TST /VER\r',b'BetterCP/M VT52TST 1.0 (Build 002)',10),
        (b'',prompt,10),
        (b'RSX LOAD HELLO\r',prompt,30),
        (b'RSX LOAD ANSISCRN\r',prompt,30),
        (b'RSX LOAD VT52\r',prompt,30),
        (b'RSX UNLOAD HELLO\r',prompt,30),
        (b'VT52TST\r',b'Press a key to continue.',30),
        (b' ',b'Press a key to continue.',10),
        (b' ',b'Press a key to continue.',10),
        (b' ',b'VT52 monitor exercise complete.',10),
        (b'',prompt,10),
        (b'RSX UNLOAD VT52\r',prompt,30),
        (b'RSX UNLOAD ANSISCRN\r',prompt,30),
        (b'RSX LIST\r',b'TPA available: 53K',10),
        (b'BYE\r',b'System halted',10)],work/'transcript.bin',rom_image=rom_image,rom_start='DF00' if rom_image else None)
    if rom_image:
        assert b'ROM QUALIFICATION ACTIVE START=DF00' in trace
        assert b'ROM WRITE VIOLATION' not in trace
    assert b'identification reply ESC / K passed.' in trace
    rendered = trace[trace.index(b'\x1b[1;1H'):trace.index(b'VT52 monitor exercise complete.')]
    assert b'\x1b[6;11H' in rendered and b'\x1b[11;80H' in rendered
    assert b'\x1b[0K' in rendered and b'\x1b[0J' in rendered
    assert b'\x1bY' not in rendered, 'unparsed VT52 address reached host'
    assert b'No RSXs loaded' in trace
    assert b'identification reply failed' not in trace
    print(f'PASS: live cpmsim portable VT52 through ANSI-host backend, load/movement, identification, three utility phases, unload/53K and BYE; {work}')


if __name__=='__main__':main()
