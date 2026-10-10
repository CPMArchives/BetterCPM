#!/usr/bin/env python3
"""Build BYE.COM for cpmsim's hardware-control interface."""
from pathlib import Path
from build_ccp import assemble
ROOT = Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    output = ROOT / 'build/z80pack-tools/BYE.COM'
    output.parent.mkdir(parents=True, exist_ok=True)
    data = assemble(Path.home()/'bin/z80asm',
                    (ROOT/'src/platform/z80pack/bye.mac').read_text(),
                    output, output.with_suffix('.lst'), 0x100)
    if data != bytes.fromhex('3eaad3a03e80d3a0f376c9'):
        raise ValueError('unexpected cpmsim exit sequence')
    print(f'{output}: {len(data)} bytes')
