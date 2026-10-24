#!/usr/bin/env python3
"""Build the hardware-independent BetterCP/M TIME.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

from system_layout import expand_layout
from component_build import recorded_build

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/time.mac"
BUILD = ROOT / "build/utilities"


@recorded_build('utility:TIME')
def build(assembler, destination):
    text = expand_layout(SOURCE.read_text(encoding="ascii")).replace(
        "        CSEG\n", "        ASEG\n").replace(
        "        .PHASE  0103H\n", "        ORG     0103H\n").replace(
        "        .DEPHASE\n", "")
    with tempfile.TemporaryDirectory(prefix="bettercpm-time-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "time.bin"
        subprocess.run([str(assembler), "-fb", f"-o{raw}",
                        f"-l{destination / 'time.lst'}", staged.name],
                       check=True, cwd=staged.parent)
        data = bytes((0xC3, 0x03, 0x01)) + raw.read_bytes()
    output = destination / "TIME.COM"
    output.write_bytes(data)

    return data


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--assembler',type=Path,default=Path.home()/'bin/z80asm')
    parser.add_argument('--output-dir',type=Path,default=BUILD)
    parser.add_argument('--target',choices=('z80pack','trs80gp'),default='z80pack')
    parser.add_argument('--identity-state',choices=('auto','assigned','development'),default='auto')
    args=parser.parse_args()
    data=build(args.assembler,args.output_dir,target=args.target,identity_state=args.identity_state)
    print(f'TIME: {len(data)} bytes')


if __name__ == '__main__':
    main()
