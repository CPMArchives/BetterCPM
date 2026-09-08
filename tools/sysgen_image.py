"""Describe the immutable resident carrier used by CONFIG H's checked save."""
import struct

def sysgen_image(resident, base, records, first_record, spt):
    signature = b"BDCF" + bytes((5, 4, 4, 64))
    at = resident.index(signature)
    physical, logical = struct.unpack_from("<HH", resident, at + 8)
    if not 0 < records <= 63:
        raise ValueError("SYSGEN carrier exceeds transient workspace")
    size = records * 128
    if len(resident) > size or first_record != 8 or not 0 < spt <= 65535:
        raise ValueError("Invalid SYSGEN carrier geometry")
    for address, length in ((physical, 24), (logical, 320)):
        if not base <= address or address + length > base + len(resident):
            raise ValueError("SYSGEN configuration table outside resident image")
    header = bytearray(128)
    header[:8] = b"BCSG" + bytes((1, 5, records, first_record))
    struct.pack_into("<HHHH", header, 8, base, physical, logical, spt)
    return bytes(header) + resident.ljust(size, b"\0")
