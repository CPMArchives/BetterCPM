"""Build and validate the BetterCP/M version-1 saved startup record."""
from __future__ import annotations

import struct

MAGIC = b"BCST"
VERSION = (1, 0)
HEADER_SIZE = 16
RECORD_SIZE = 256
COMMAND_CAPACITY = 126
ENABLED = 0x01


def _word_sum(record: bytes) -> int:
    if len(record) != RECORD_SIZE:
        raise ValueError("startup record must occupy exactly two CP/M records")
    return sum(struct.unpack("<128H", record)) & 0xFFFF


def build(command: str = "", *, system_base: int) -> bytes:
    """Return one canonical record; an empty command disables startup."""
    try:
        encoded = command.encode("ascii")
    except UnicodeEncodeError as error:
        raise ValueError("startup command must contain ASCII characters") from error
    if len(encoded) > COMMAND_CAPACITY:
        raise ValueError("startup command exceeds the CCP command-line limit")
    if any(byte < 0x20 or byte == 0x7F for byte in encoded):
        raise ValueError("startup command contains a control character")
    if not 0 <= system_base <= 0xFFFF:
        raise ValueError("system base is outside the Z80 address space")

    record = bytearray(RECORD_SIZE)
    record[:4] = MAGIC
    record[4:10] = bytes((*VERSION, HEADER_SIZE,
                          ENABLED if encoded else 0,
                          len(encoded), COMMAND_CAPACITY))
    struct.pack_into("<H", record, 10, RECORD_SIZE)
    struct.pack_into("<H", record, 14, system_base)
    record[HEADER_SIZE:HEADER_SIZE + len(encoded)] = encoded
    checksum = (-_word_sum(record)) & 0xFFFF
    struct.pack_into("<H", record, 12, checksum)
    return bytes(record)


def parse(record: bytes, *, system_base: int) -> str:
    """Validate a record completely and return its command, or an empty string."""
    if len(record) != RECORD_SIZE:
        raise ValueError("startup record has the wrong size")
    if record[:4] != MAGIC:
        raise ValueError("startup record has the wrong signature")
    if tuple(record[4:6]) != VERSION:
        raise ValueError("startup record has an unsupported version")
    if record[6] != HEADER_SIZE or record[9] != COMMAND_CAPACITY:
        raise ValueError("startup record has an invalid layout")
    if struct.unpack_from("<H", record, 10)[0] != RECORD_SIZE:
        raise ValueError("startup record declares the wrong size")
    if struct.unpack_from("<H", record, 14)[0] != system_base:
        raise ValueError("startup record belongs to another system layout")
    if _word_sum(record):
        raise ValueError("startup record checksum does not match")

    flags, length = record[7], record[8]
    if flags & ~ENABLED or length > COMMAND_CAPACITY:
        raise ValueError("startup record has invalid flags or length")
    command = record[HEADER_SIZE:HEADER_SIZE + length]
    if any(record[HEADER_SIZE + length:]):
        raise ValueError("startup record has nonzero reserved data")
    if any(byte < 0x20 or byte == 0x7F for byte in command):
        raise ValueError("startup command contains a control character")
    if bool(flags & ENABLED) != bool(length):
        raise ValueError("startup enabled state and command length disagree")
    return command.decode("ascii")
