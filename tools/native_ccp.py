"""Validated ordinary outer-carrier metadata for native RLMBUILD."""
import struct


def metadata(raw: bytes) -> str:
    if len(raw) < 16:
        raise ValueError('truncated CCP carrier')
    magic, version, headers, base, size, allocation, entry, count = struct.unpack_from('<4sBBHHHHH', raw)
    if (magic != b'BCM1' or version != 1 or headers not in (1, 2)
            or base != 0xBB00 or entry != 0 or not 1 <= size <= 6144
            or allocation < size or allocation % 256 or 0xBD37+allocation > 65536
            or count > (headers*512-16)//2
            or len(raw) != headers*512+size or len(raw) > 6656):
        raise ValueError('unsupported native CCP carrier layout')
    offsets = [struct.unpack_from('<H',raw,16+2*i)[0] for i in range(count)]
    if any(x+2 > size for x in offsets) or any(b-a < 2 for a,b in zip(offsets,offsets[1:])):
        raise ValueError('invalid native CCP relocation directory')
    return ''.join(f'CCP_{key} EQU {value}\n' for key, value in (
        ('SIZE', size), ('ALLOC', allocation), ('RECORDS', (size+127)//128),
        ('RELOCS', count), ('HEADERS', headers)))
