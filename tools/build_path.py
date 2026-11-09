#!/usr/bin/env python3
"""Build the numeric command-search PATH utility for the selected layout."""
import argparse
from pathlib import Path

from build_ccp import assemble
from component_build import recorded_build

ROOT = Path(__file__).resolve().parents[1]

@recorded_build('utility:PATH')
def build(assembler, output):
    source = (ROOT / 'src/utilities/path.mac').read_text(encoding='ascii')
    source = source.replace('; @path-tcap@',
        (ROOT / 'src/utilities/common/tcap2.inc').read_text(encoding='ascii'))
    return assemble(assembler, source, output / 'PATH.COM', output / 'path.lst', 0x100)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home() / 'bin/z80asm')
    parser.add_argument('--target', default='z80pack')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/utilities')
    args = parser.parse_args()
    build(args.assembler, args.output, target=args.target)
