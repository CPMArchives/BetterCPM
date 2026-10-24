#!/usr/bin/env python3
"""Assemble maintained streaming command stages from verified profile inputs."""
from pathlib import Path
import argparse
import binascii
import hashlib
import json

from build_ccp import assemble
from build_profiles import CONTEXT_RELATIVE, selected_context
from checked_build_contract import load_contract

ROOT = Path(__file__).resolve().parents[1]


def build_stages(output: Path, identity: bytes, assembler: Path) -> dict:
    """Emit stages for a caller's contract; fixtures may supply a reference ID.

    The command-line entry obtains the ID only from load_contract(). No resident
    or command-carrier inputs are modified here. Historical P9/CR9/CR10 labels
    remain stable for the existing stack-observer and symbol-based fixtures.
    """
    if len(identity) != 16:
        raise ValueError('private build ID must contain 16 bytes')
    if not selected_context(ROOT/'src/system/layout.inc'):
        raise ValueError('checked command stages require a prepared profile context')
    output.mkdir(parents=True, exist_ok=False)
    source = (ROOT/'src/system/command-stage2.mac').read_text(encoding='ascii')
    (output/'stage2.mac').write_text(source, encoding='ascii')
    stage2 = assemble(assembler, source, output/'stage2.bin', output/'stage2.lst', 0x500)
    if not stage2 or len(stage2) > 2024:
        raise ValueError(f'stage 2 payload exceeds 2024 bytes: {len(stage2)}')
    carrier2 = stage2.ljust(2024, b'\0') + identity + bytes(8)
    (output/'stage2.carrier').write_bytes(carrier2)
    checksum = binascii.crc_hqx(carrier2, 0xFFFF)
    constants = f'COMMAND_STAGE2_CRC EQU 0{checksum:04X}H\n'
    (output/'command-bindings.inc').write_text(constants, encoding='ascii')
    bootstrap = constants + (ROOT/'src/system/command-stage1.mac').read_text(encoding='ascii')
    (output/'stage1.mac').write_text(bootstrap, encoding='ascii')
    stage1 = assemble(assembler, bootstrap, output/'stage1.bin', output/'stage1.lst', 0x100)
    if not stage1 or len(stage1) > 932:
        raise ValueError(f'stage 1 payload exceeds 932 bytes: {len(stage1)}')
    carrier1 = stage1.ljust(1000, b'\0') + identity + bytes(8)
    (output/'stage1.carrier').write_bytes(carrier1)
    result = {
        'compatibility_id': identity.hex(), 'stage1_bytes': len(stage1),
        'stage2_bytes': len(stage2), 'stage1_origin': 0x100, 'stage2_origin': 0x500,
        'stage1_carrier_bytes': len(carrier1), 'stage2_carrier_bytes': len(carrier2),
        'stage2_crc16': checksum, 'stage2_raw_records': [84, 99],
        'stack_reserved_low': 0xD00, 'stack_top': 0x1000,
        'header_origin': 0x1000, 'header_capacity': 1536,
        'record_buffer': 0x1600, 'record_buffer_bytes': 128, 'temporary_limit': 0x1680,
        'artifacts': {name:hashlib.sha256((output/name).read_bytes()).hexdigest()
                      for name in ('stage1.bin', 'stage2.bin', 'stage1.carrier', 'stage2.carrier')},
        'status': 'checked command stages assembled; not installed in a distribution',
    }
    (output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/z80pack/command-loader')
    parser.add_argument('--assembler', type=Path, default=Path.home()/'bin/z80asm')
    args = parser.parse_args()
    if not selected_context(ROOT/'src/system/layout.inc'):
        parser.error('select a prepared checked profile with BETTERCPM_BUILD_CONTEXT')
    assembler = args.assembler.expanduser().resolve()
    contract = load_contract(ROOT, assembler)
    result = build_stages(args.output.resolve(), bytes.fromhex(contract['compatibility_id']), assembler)
    if load_contract(ROOT, assembler) != contract:
        raise ValueError('private build inputs changed while assembling command stages')
    (args.output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
