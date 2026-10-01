#!/usr/bin/env python3
"""Exercise independent FDB v1 framing, pool, TLV, and support validation."""
from pathlib import Path
import struct

from fdf_v1 import FDBError, compile_file, crc16, read_fdb


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests" / "fixtures" / "fdf-v1" / "qualified.fdf"


def with_crc(value: bytearray) -> bytes:
    value[14:16] = b"\0\0"
    value[14:16] = crc16(value).to_bytes(2, "little")
    return bytes(value)


def reject(value: bytes, fragment: str) -> None:
    try:
        read_fdb(value)
    except FDBError as error:
        assert fragment in str(error), (fragment, str(error))
    else:
        raise AssertionError(f"accepted malformed FDB; expected {fragment!r}")


def extension_offset(value: bytes, index: int) -> int:
    first = int.from_bytes(value[10:12], "little")
    stride = value[7]
    return int.from_bytes(value[first + index * stride + 62:first + index * stride + 64],
                          "little")


def main() -> None:
    payload = compile_file(SOURCE)
    database = read_fdb(payload)
    assert [item.ident for item in database.descriptors] == ["CCS40DS", "MMSUPER", "CYLTEST"]
    assert all(item.supported and item.format is not None for item in database.descriptors)
    assert database.descriptors[1].format.sector_sizes == (1024,) * 5 + (512,)
    assert database.descriptors[2].format.logical_track == "CYLINDER"

    changed = bytearray(payload)
    changed[-1] ^= 1
    reject(bytes(changed), "CRC-16")

    changed = bytearray(payload)
    changed[6] = 15
    reject(with_crc(changed), "header size")

    changed = bytearray(payload)
    changed[128 + 59] -= 1
    reject(with_crc(changed), "duplicated sector count")

    changed = bytearray(payload)
    changed[128 + 60:128 + 62] = (321).to_bytes(2, "little")
    reject(with_crc(changed), "overlap")

    changed = bytearray(payload)
    changed[-1] = 1
    reject(with_crc(changed), "nonzero unowned pool byte")

    changed = bytearray(payload + bytes(128))
    reject(with_crc(changed), "extra record padding")

    # An unknown optional extension is skipped; a required one makes only its
    # descriptor unsupported.  Offset 370 lies in the qualified fixture's
    # zero-filled final record and does not overlap another pool object.
    for kind, supported in ((0x03, True), (0x83, False)):
        changed = bytearray(payload)
        changed[370:375] = bytes((kind, 1, 0xAA, 0, 0))
        changed[128 + 58] |= 0x80
        changed[128 + 62:128 + 64] = (370).to_bytes(2, "little")
        decoded = read_fdb(with_crc(changed)).descriptors[0]
        assert decoded.supported is supported
        if supported:
            assert decoded.format is not None and not decoded.unsupported_required
        else:
            assert decoded.format is None and decoded.unsupported_required == (3,)

    changed = bytearray(payload)
    mixed = extension_offset(payload, 1)
    changed[mixed] = 0x01
    reject(with_crc(changed), "not required")

    changed = bytearray(payload)
    changed[mixed + 2:mixed + 8] = bytes((2,) * 6)
    reject(with_crc(changed), "maximum disagrees")

    changed = bytearray(payload)
    cylinder = extension_offset(payload, 2)
    changed[cylinder + 2] = 2
    reject(with_crc(changed), "logical-track extension")

    changed = bytearray(payload)
    changed[5] = 1
    assert read_fdb(with_crc(changed)).minor == 1

    print("FDB v1 reader tests passed")


if __name__ == "__main__":
    main()
