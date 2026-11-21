"""Build and validate the BetterCP/M version-1 saved startup record."""
from __future__ import annotations

import struct

MAGIC = b"BCST"
VERSION = (2, 0)
HEADER_SIZE = 16
RECORD_SIZE = 256
COMMAND_CAPACITY = 126
ENABLED = 0x01


def _word_sum(record: bytes) -> int:
    if len(record) != RECORD_SIZE:
        raise ValueError("startup record must occupy exactly two CP/M records")
    return sum(struct.unpack("<128H", record)) & 0xFFFF


def build(command: str = "", *, system_base: int, history: int = 2,
          mcl: int = 0, variables: int = 0, version: int = 2) -> bytes:
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

    if history not in range(4) or mcl not in range(2) or variables not in range(4):
        raise ValueError('invalid command-environment capacity choice')
    if version not in (1, 2):
        raise ValueError('unsupported saved configuration version')
    if version == 1 and (history, mcl, variables) != (2, 0, 0):
        raise ValueError('BCST v1 cannot store PDS choices')
    record = bytearray(RECORD_SIZE)
    record[:4] = MAGIC
    record[4:10] = bytes((version, 0, HEADER_SIZE,
                          ENABLED if encoded else 0,
                          len(encoded), COMMAND_CAPACITY))
    struct.pack_into("<H", record, 10, RECORD_SIZE)
    struct.pack_into("<H", record, 14, system_base)
    record[HEADER_SIZE:HEADER_SIZE + len(encoded)] = encoded
    if version == 2:
        record[142:150] = b'CE' + bytes((1, history, mcl, variables, 0, 0))
    checksum = (-_word_sum(record)) & 0xFFFF
    struct.pack_into("<H", record, 12, checksum)
    return bytes(record)


def parse(record: bytes, *, system_base: int) -> str:
    """Validate a record completely and return its command, or an empty string."""
    if len(record) != RECORD_SIZE:
        raise ValueError("startup record has the wrong size")
    if record[:4] != MAGIC:
        raise ValueError("startup record has the wrong signature")
    if tuple(record[4:6]) not in ((1, 0), VERSION):
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
    if any(record[HEADER_SIZE + length:142]):
        raise ValueError("startup record has nonzero reserved data")
    if record[4] == 1:
        if any(record[142:]):
            raise ValueError('BCST v1 has nonzero reserved data')
    elif (record[142:145] != b'CE\x01' or record[145] > 3 or
          record[146] > 1 or record[147] > 3 or any(record[148:])):
        raise ValueError('invalid saved command-environment extension')
    if any(byte < 0x20 or byte == 0x7F for byte in command):
        raise ValueError("startup command contains a control character")
    if bool(flags & ENABLED) != bool(length):
        raise ValueError("startup enabled state and command length disagree")
    return command.decode("ascii")


def choices(record: bytes, *, system_base: int) -> tuple:
    parse(record, system_base=system_base)
    return tuple(record[145:148]) if record[4] == 2 else (2, 0, 0)
