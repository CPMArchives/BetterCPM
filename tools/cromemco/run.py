#!/usr/bin/env python3
"""Start writable Cromemco release media; build the pinned emulator when needed."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emulator',type=Path,help='existing compatible cromemcosim executable')
    p.add_argument('--session',type=Path,default=root/'Session',help='persistent writable session folder')
    p.add_argument('--c',choices=('Utilities-1','Utilities-2','Utilities-3'),default='Utilities-1')
    p.add_argument('--d',choices=('Utilities-1','Utilities-2','Utilities-3'),default='Utilities-2')
    a=p.parse_args();work=a.session.resolve()
    import platform
    prebuilt=root/'Host/prebuilt/macos-arm64/cromemcosim'
    native=platform.system()=='Darwin' and platform.machine()=='arm64' and prebuilt.is_file()
    sim=a.emulator.resolve() if a.emulator else prebuilt if native else root/'Host/build/cromemco/cromemcosim/cromemcosim'
    if not sim.is_file():
        if a.emulator:p.error('emulator executable does not exist')
        subprocess.run([sys.executable,str(root/'Host/tools/prepare_cromemco_emulator.py'),
                        '--output',str(root/'Host/build/cromemco')],check=True)
    (work/'disks').mkdir(parents=True,exist_ok=True)
    # Preserve A/B across launches. C/D are explicit selected utility mounts.
    for letter,volume in [('a','System'),('b','Work'),('c',a.c),('d',a.d)]:
        dest=work/f'disks/drive{letter}.dsk'
        if letter in 'cd' or not dest.exists():
            shutil.copy2(root/'Media'/f'BetterCPM-1.3-Cromemco-{volume}.dsk',dest)
    (work/'disks/disk.map').write_text(''.join(f'drive{d}.dsk\n' for d in 'abcd'))
    for name in ('system.conf','diskdefs'):shutil.copy2(root/'Media'/name,work/name)
    print('Writable session:',work,flush=True)
    os.chdir(work)
    os.execv(str(sim),[str(sim),'-z','-R','-M1','-f0','-r',str(root/'Host/roms' if native and not a.emulator else sim.parent/'roms'),'-c',str(work/'system.conf'),'-d',str(work/'disks')])


if __name__=='__main__':main()
