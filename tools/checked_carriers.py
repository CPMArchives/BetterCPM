"""Emit checked carrier bindings only in a verified prepared-profile workspace."""
from pathlib import Path
import binascii
import struct

from build_profiles import selected_context
from checked_build_contract import load_contract

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_RSX = frozenset(('HELLO', 'ECHO'))
PRIVATE_RSX = frozenset(('STATEFUL', 'TEST', 'ANSISCRN', 'ADM3A', 'VT52',
                         'ANSI', 'BATCHIO', 'FDF', 'P2DOS', 'ZPRTC',
                         'T104Z8', 'T104C3'))


def selected_contract(assembler=None):
    if not selected_context(ROOT/'src/system/layout.inc'):
        return None
    return load_contract(ROOT, assembler or Path.home()/'bin/z80asm')


def binding(name, contract, kind):
    name = name.upper()
    public = PUBLIC_RSX if kind == 'rsx' else frozenset(('HELLO',))
    private = PRIVATE_RSX if kind == 'rsx' else frozenset(('RCP',))
    if kind == 'ccp':
        public, private = frozenset(), frozenset(('CCP',))
    if name not in public | private:
        raise ValueError(f'unreviewed or unsupported checked {kind} module: {name}')
    return bytes((1, int(name not in public))) + (
        bytes(16) if name in public else bytes.fromhex(contract['compatibility_id']))


def rsx_metadata(name, metadata, contract):
    """Prepend the mandatory binding while constructing BMET2 metadata."""
    record = bytes((4, 18)) + binding(name, contract, 'rsx')
    header = bytearray(metadata[:12])
    header[4] = 2
    header[7] += 1
    struct.pack_into('<H', header, 8, len(metadata) + len(record))
    if len(metadata) + len(record) >= 512:
        raise ValueError('checked RSX metadata exceeds one record area')
    return bytes(header) + record + metadata[12:]


def command_carrier(data, name, kind, contract):
    """Emit schema-2 whole-carrier CRC and public/private identity trailer."""
    bind = binding(name, contract, kind)
    result = bytearray(data)
    if kind == 'cpx':
        if result[:5] != b'BCPX\x01':
            raise ValueError('expected an unbound BCPX1 carrier')
        result[4] = 2
    elif kind == 'ccp':
        if result[:6] != b'BCM1\x01\x02':
            raise ValueError('expected an unbound BCM1 CCP carrier')
        result[:5] = b'BCM2\x02'
    else:
        raise ValueError('unknown checked command carrier kind')
    result += b'BP' + bytes((2,)) + bind[1:]
    result += struct.pack('<H', binascii.crc_hqx(result, 0xFFFF))
    return bytes(result)
