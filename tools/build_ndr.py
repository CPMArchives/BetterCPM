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

def default_template(carrier, table_offset):
    """Pin editing to this provider layout, for public BRSX 2 and 3."""
    from checked_carriers import rsx_metadata
    configuration = json.loads((ROOT/'metadata/component-inputs.json').read_text())['components']['utility:NDR']['configuration']
    if carrier[40:42] != bytes(configuration['default_provider_version']):
        raise ValueError('review /DEFAULT compatibility before changing the provider version')
    code_size = int.from_bytes(carrier[12:14], 'little')
    metadata_offset = int.from_bytes(carrier[30:32], 'little')
    header = bytearray(carrier[:512]); header[4] = 2
    metadata = carrier[metadata_offset:]
    if carrier[4] == 3:
        assert metadata[12:16] == bytes((4, 18, 1, 0))
        metadata = bytearray(metadata[:12] + metadata[32:])
        metadata[4] = 1; metadata[7] -= 1
        metadata[8:10] = len(metadata).to_bytes(2, 'little')
        metadata = bytes(metadata)
    checked = rsx_metadata('NDR', metadata, {})  # public binding has no target ID
    assert table_offset + 320 == code_size
    values = dict(NF_TABLE_OFFSET=512+table_offset, NF_META_OFFSET=metadata_offset,
                  NF_PAYLOAD_SIZE=code_size, NF_SIZE2=metadata_offset+len(metadata),
                  NF_SIZE3=metadata_offset+len(checked))
    assert max(values['NF_SIZE2'], values['NF_SIZE3']) <= 1152
    values['NF_RECS2'] = (values['NF_SIZE2']+127)//128
    values['NF_RECS3'] = (values['NF_SIZE3']+127)//128
    result = '\n'.join(f'{name} EQU {value}' for name,value in values.items())+'\n'
    for label, data in [('NF_REFERENCE',bytes(header)+carrier[512:512+table_offset]),
                        ('NF_META2',metadata),('NF_META3',checked)]:
        result += label+':\n'
        result += '\n'.join('        DB '+','.join(f'0{v:02X}H' for v in data[i:i+16])
                            for i in range(0,len(data),16))+'\n'
    return result

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
    template = default_template(carrier, symbols(output/'ndr.lst')['NR_TABLE']-0x8000)
    @recorded_build('utility:NDR')
    def build_manager(assembler, destination):
        source = (ROOT/'src/utilities/ndr.mac').read_text()
        source = source.replace('; @ndr-default@',
            (ROOT/'src/utilities/common/ndr-default.inc').read_text())
        source = source.replace('; @ndr-default-template@', template)
        return assemble(assembler, source, destination/'NDR.COM', destination/'ndr.lst', 0x100)
    build_manager(assembler, dest, target=CONTEXT[0]['target'] if CONTEXT else 'z80pack')
    return carrier

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    build(parser.parse_args().assembler)
