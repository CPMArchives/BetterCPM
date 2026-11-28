#!/usr/bin/env python3
"""Start writable Altair release media; build the pinned emulator when needed."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    root=Path(__file__).resolve().parent
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--emulator',type=Path,help='existing compatible altairsim executable')
    p.add_argument('--session',type=Path,default=root/'Session',help='persistent writable session folder')
    p.add_argument('--c',choices=('Utilities-1','Utilities-2','Utilities-3'),default='Utilities-1')
    p.add_argument('--d',choices=('Utilities-1','Utilities-2','Utilities-3'),default='Utilities-2')
    a=p.parse_args();work=a.session.resolve();sim=a.emulator.resolve() if a.emulator else root/'Host/build/altair/altairsim/altairsim'
    if not sim.is_file():
        if a.emulator:p.error('emulator executable does not exist')
        subprocess.run([sys.executable,str(root/'Host/tools/prepare_altair_emulator.py'),
                        '--output',str(root/'Host/build/altair')],check=True)
    (work/'disks').mkdir(parents=True,exist_ok=True)
    # Preserve A/B across launches. C/D are explicit selected utility mounts.
    for letter,volume in [('a','System'),('b','Work'),('c',a.c),('d',a.d)]:
        dest=work/f'disks/drive{letter}.dsk'
        if letter in 'cd' or not dest.exists():
            shutil.copy2(root/'Media'/f'BetterCPM-1.3-Altair-{volume}.dsk',dest)
    for name in ('system.conf','diskdefs'):shutil.copy2(root/'Media'/name,work/name)
    print('Writable session:',work,flush=True)
    os.chdir(work)
    os.execv(str(sim),[str(sim),'-z','-R','-M1','-f0','-c',str(work/'system.conf'),'-d',str(work/'disks')])


if __name__=='__main__':main()
