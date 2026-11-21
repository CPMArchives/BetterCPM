"""Build the private transient PDS worker; no resident allocation."""
from pathlib import Path
from build_ccp import assemble

ROOT = Path(__file__).resolve().parents[1]


def build(assembler=None):
    assembler = assembler or Path.home()/'bin/z80asm'
    out = ROOT/'build/pds'
    out.mkdir(parents=True, exist_ok=True)
    binary = assemble(assembler, (ROOT/'src/system/pds-worker.mac').read_text(),
                      out/'worker.bin', out/'worker.lst', 0x1700)
    if not 0 < len(binary) <= 1021:
        raise ValueError(f'PDS worker exceeds its transient slot: {len(binary)}')
    return binary


if __name__ == '__main__':
    print('PDS worker bytes:', len(build()))
