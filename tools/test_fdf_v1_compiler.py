#!/usr/bin/env python3
"""Verify deterministic FDF v1 parsing, validation, and FDB serialization."""
from pathlib import Path
import hashlib
import struct
import tempfile

from fdf_v1 import FDFError, compile_file, crc16, parse, serialize

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests/fixtures/fdf-v1/qualified.fdf"


def reject(body: str, phrase: str) -> None:
    try:
        parse("FDF_VERSION 1\nFORMAT\n" + body + "\nEND\n", "negative.fdf")
    except FDFError as error:
        assert phrase in str(error), (phrase, str(error))
    else:
        raise AssertionError(f"accepted invalid FDF expecting {phrase}")


def main() -> None:
    formats = parse(SOURCE.read_text(encoding="ascii"), str(SOURCE))
    assert [item.ident for item in formats] == ["CCS40DS", "MMSUPER", "CYLTEST"]
    assert formats[0].extensions == () and formats[0].flags == 3
    assert formats[1].extensions == ((0x81, bytes((3, 3, 3, 3, 3, 2))),)
    assert formats[2].extensions == ((0x82, b"\x01"),)
    payload = serialize(formats)
    assert payload == compile_file(SOURCE)
    assert len(payload) == 384 and payload[:4] == b"BFDB"
    assert hashlib.sha256(payload).hexdigest() == \
        "50d60d2835026235afca02adc01eef8cb3c34c58a0709608366448d62d001cd9"
    major, minor, hsize, stride = payload[4:8]
    count, first, pool, stored_crc = struct.unpack_from("<HHHH", payload, 8)
    assert (major, minor, hsize, stride, count, first, pool) == (1, 0, 16, 64, 3, 128, 320)
    check = bytearray(payload)
    check[14:16] = b"\0\0"
    assert stored_crc == crc16(check) and crc16(b"123456789") == 0x29B1
    assert payload == serialize(formats), "serialization is not deterministic"

    with tempfile.TemporaryDirectory() as temporary:
        output = Path(temporary) / "DISK.FDB"
        output.write_bytes(payload)
        assert output.read_bytes() == payload
        padded = Path(temporary) / "PADDED.FDF"
        padded.write_bytes(SOURCE.read_bytes() + b"\x1a\xff\xfeignored")
        assert compile_file(padded) == payload

    common = """ID TEST\nSPT 16\nBSH 3\nDSM 38\nDRM 31\nAL0 0x80\nAL1 0\nCKS 8\nOFF 2\nPSECTORS 8\nSECSIZE 256\nCYLINDERS 40\nSIDES 1\nENCODING MFM\nSECTOR_IDS 1,2,3,4,5,6,7,8"""
    reject(common + "\nSPT 16", "duplicate field SPT")
    reject(common.replace("ID TEST", "ID TOO-LONG-ID"), "ID: expected")
    reject(common.replace("SECTOR_IDS 1,2,3,4,5,6,7,8", "SECTOR_IDS 1,2,3,4,5,6,7,7"), "distinct")
    reject(common.replace("SPT 16", "SPT 15"), "SPT: expected 16")
    reject(common.replace("AL0 0x80", "AL0 0"), "reserve every directory block")
    reject(common + "\nUNKNOWN 1", "unknown field")
    reject(common + "\nLOGICAL_TRACK CYLINDER", "CYLINDER requires two sides")
    try:
        parse("FDF_VERSION 1\nFORMAT\n" + common + "\nEND\nFORMAT\n" +
              common + "\nEND\n", "duplicate.fdf")
    except FDFError as error:
        assert "duplicate ID TEST" in str(error)
    else:
        raise AssertionError("accepted duplicate format IDs")

    print("FDF v1 compiler: uniform, mixed-sector, cylinder-track, CRC, "
          "determinism, and negative validation passed")


if __name__ == "__main__":
    main()
