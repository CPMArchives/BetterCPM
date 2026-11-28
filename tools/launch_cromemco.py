#!/usr/bin/env python3
"""Run a built Cromemco engineering image in the current terminal."""
import argparse
import os
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image-dir',type=Path,required=True)
    p.add_argument('--simulator',type=Path,required=True)
    a = p.parse_args()
    image, simulator = a.image_dir.resolve(), a.simulator.resolve()
    for path in (simulator,image/'candidate.json',image/'system.conf',
                 *(image/f'disks/drive{x}.dsk' for x in 'abcd')):
        if not path.is_file():
            p.error('missing build artifact: '+str(path))
    os.chdir(image)
    os.execv(str(simulator),[str(simulator),'-z','-R','-M1','-f0',
                            '-r',str(simulator.parent/'roms'),'-c',str(image/'system.conf'),'-d',str(image/'disks')])


if __name__ == '__main__':
    main()
