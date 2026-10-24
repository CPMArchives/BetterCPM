"""Checked internal reconstruction slots and their bounded pack directory."""
import binascii
import struct
from rsx_container import NAMES


def bind_slot(data: bytes, identity: bytes) -> bytes:
    if len(identity) != 16 or len(data) != 1024 or any(data[1000:1016]):
        raise ValueError('private binding overlaps executable bytes or has an invalid size')
    return data[:1000]+identity+data[1016:]


def pack_slots(images: dict, identity: bytes) -> bytes:
    if len(identity) != 16 or len(NAMES) != 15:
        raise ValueError('unsupported reconstruction pack contract')
    header = bytearray(512)
    header[:6] = b'BCPH\1\1'
    struct.pack_into('<H', header, 6, 512)
    header[8:24] = identity
    for offset, value in ((24, 15), (26, 1024), (28, 124)):
        struct.pack_into('<H', header, offset, value)
    payload = bytearray()
    for slot, name in enumerate(NAMES):
        data = images[name+'.RSX']
        if len(data) != 1024:
            raise ValueError(f'{name}: reconstruction slot must contain 1024 bytes')
        kind = 0 if slot < 5 or slot == 12 else 1
        struct.pack_into('<BBHHH', header, 34+8*slot, slot, kind, 4+8*slot,
                         1024, binascii.crc_hqx(data, 0xFFFF))
        payload += data
    struct.pack_into('<H', header, 32, binascii.crc_hqx(header, 0xFFFF))
    return bytes(header+payload)
