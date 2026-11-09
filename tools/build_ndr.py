#!/usr/bin/env python3
"""Build NDR's STATEFUL provider and transient manager; enforce its budget."""
import argparse
import json
from pathlib import Path
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_stateful_test_rsx import symbols
from component_registry import module_version
from component_build import recorded_build
from system_layout import CONTEXT

ROOT = Path(__file__).resolve().parents[1]

@recorded_build('utility:NDR')
def build_manager(assembler, destination):
    return assemble(assembler, (ROOT/'src/utilities/ndr.mac').read_text(),
                    destination/'NDR.COM', destination/'ndr.lst', 0x100)

def build(assembler, output=None):
    output = output or ROOT / 'build/rsx'
    output.mkdir(parents=True, exist_ok=True)
    source = (ROOT / 'src/rsx/ndr.mac').read_text()
    text = source.replace('        CSEG\n        .PHASE  ', '        ASEG\n        ORG     ').replace('        .DEPHASE\n', '')
    code = assemble(assembler, text, output/'ndr.bin', output/'ndr.lst', 0x8000)
    alt = assemble(assembler, text.replace('08000H', '08101H'), output/'ndr-alt.bin', output/'ndr-alt.lst', 0x8101)
    offsets = relocation_offsets(code, alt, 0x101)
    entry = symbols(output/'ndr.lst')['NR_SERVICE'] - 0x8000
    carrier = make_module(name='NDR', version=module_version('NDR'), services=[], linked_base=0x8000,
        code=code, relocations=offsets, reconstruction_class='STATEFUL',
        callable_services=[(b'NDR ', 1, 0, entry, 0)], cache_footer_inline=True)
    allocated = int.from_bytes(carrier[14:16], 'little')
    if allocated > 768:
        raise ValueError(f'NDR provider exceeds its 768-byte protected allocation ceiling: {allocated}')
    (output/'NDR.RSX').write_bytes(carrier)
    report = dict(payload_bytes=len(code), table_bytes=320, allocation_bytes=allocated,
                  descriptors_bytes=10, inline_cache_bytes=10, reconstruction='STATEFUL')
    (output/'ndr-memory.json').write_text(json.dumps(report, indent=2)+'\n')
    print(report)
    dest = ROOT/'build/utilities'
    dest.mkdir(parents=True, exist_ok=True)
    build_manager(assembler, dest, target=CONTEXT[0]['target'] if CONTEXT else 'z80pack')
    return carrier

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    build(parser.parse_args().assembler)
