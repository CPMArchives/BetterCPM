#!/usr/bin/env python3
"""Build the portable BetterCP/M STAT.COM utility."""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import tempfile
from pathlib import Path

from system_layout import expand_layout
from component_build import recorded_build

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/utilities/stat.mac"
BUILD = ROOT / "build/utilities"


@recorded_build('utility:STAT')
def build(assembler, destination):
    text = expand_layout(SOURCE.read_text(encoding="ascii"))
    text = text.replace("        INCLUDE common/duselect.inc",
                        (SOURCE.parent / "common/duselect.inc").read_text(encoding="ascii"))
    text = text.replace("        CSEG\n", "        ASEG\n")
    text = text.replace("        .PHASE  0103H\n", "        ORG     0103H\n")
    text = text.replace("        .DEPHASE\n", "")
    from checked_carriers import selected_contract
    from checked_build_contract import assembly_constants
    contract = selected_contract(assembler)
    if contract:text = assembly_constants(contract) + text
    with tempfile.TemporaryDirectory(prefix="bettercpm-stat-") as temporary:
        staged = Path(temporary) / "stat.mac"
        staged.write_text(text, encoding="ascii")
        raw = Path(temporary) / "stat.bin"
        listing = destination / "stat.lst"
        subprocess.run([str(assembler), "-fb", f"-o{raw}",
                        f"-l{listing}", staged.name], cwd=staged.parent,
                       check=True)
        data = raw.read_bytes()
    if len(data) > 0x0103 and data[:0x0103] == bytes(0x0103):
        data = data[0x0103:]
    data = bytes((0xC3, 0x03, 0x01)) + data
    if len(data) <= 3:
        raise SystemExit("empty STAT output")
    output = destination / "STAT.COM"
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
    print(f'STAT: {len(data)} bytes')


if __name__ == '__main__':
    main()
