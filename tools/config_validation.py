"""Build CONFIG's small CRC-32/ISO-HDLC compatibility records.

This detects accidental corruption/build mismatch, not hostile modification.
Only the established editable physical and logical fields are normalized to zero.
"""
import struct
import zlib
from sysgen_image import sysgen_image


def normalized(carrier, base, physical, logical):
    data=bytearray(carrier)
    ranges=[(physical-base,24)]+[(logical-base+i*80+16,64) for i in range(4)]
    for start,size in ranges:
        if not 0<=start<=len(data)-size:
            raise ValueError('CONFIG editable range outside carrier')
        data[start:start+size]=bytes(size)
    return bytes(data)


def validation_record(resident,base,records,first,spt):
    reference=sysgen_image(resident,base,records,first,spt)
    header=reference[:16]
    physical,logical=struct.unpack_from('<HH',header,10)
    checksum=zlib.crc32(normalized(reference[128:],base,physical,logical))
    return header+struct.pack('<I',checksum)


def assembly(records):
    records=list(dict.fromkeys(records))
    if not records or any(len(r)!=20 for r in records):
        raise ValueError('CONFIG needs 20-byte validation records')
    keys=[r[10:16] for r in records]
    if len(keys)!=len(set(keys)):
        raise ValueError('ambiguous CONFIG layout/geometry validation records')
    return ('SGVALID:\n'+''.join('        DB '+','.join(str(v) for v in r)+'\n' for r in records)+'SGVEND:\n')
