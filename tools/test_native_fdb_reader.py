#!/usr/bin/env python3
"""Execute the native FDB header and CRC validator against focused mutations."""
from pathlib import Path
import re
import tempfile

from build_ccp import assemble
from fdf_v1 import compile_file, crc16
from test_bios import Z80


ROOT = Path(__file__).resolve().parents[1]
FDFRAM = 0x4000


def symbols(path: Path) -> dict[str, int]:
    return {
        name.upper(): int(address, 16)
        for address, name in re.findall(
            r"^([0-9A-F]{4})\s+.*?\b([A-Z][A-Z0-9_]*):", path.read_text(), re.M | re.I)
    }


def repaired(value: bytearray) -> bytes:
    value[14:16] = b"\0\0"
    value[14:16] = crc16(value).to_bytes(2, "little")
    return bytes(value)


def main() -> None:
    payload = compile_file(ROOT / "metadata" / "DISK.FDF")
    reader = (ROOT / "src/utilities/disk/fdbread.inc").read_text()
    validator = reader[reader.index("FDBVALID:"):]
    source = """        ASEG
        ORG 0100H
ENTRY:  CALL FDBVALID
        RET
FCOUNT: DB 0
FDFRAM  EQU 04000H
FDFLIM  EQU 07F80H
""" + validator + "\n        END\n"
    with tempfile.TemporaryDirectory(prefix="bettercpm-native-fdb-") as directory:
        work = Path(directory)
        output = work / "reader.com"
        listing = work / "reader.lst"
        code = assemble(Path.home() / "bin/z80asm", source, output, listing, 0x100)
        names = symbols(listing)

        def accepts(data: bytes) -> bool:
            cpu = Z80(b"")
            cpu.mem[0x100:0x100 + len(code)] = code
            cpu.mem[FDFRAM:FDFRAM + len(data)] = data
            cpu.setword(names["FDBLEN"], len(data))
            cpu.run(names["ENTRY"], limit=3_000_000)
            return not cpu.carry

        assert accepts(payload)
        assert not accepts(payload[:-128])
        changed = bytearray(payload)
        changed[-1] ^= 1
        assert not accepts(bytes(changed))
        for offset, value in ((0, ord("X")), (4, 2), (6, 15), (7, 63), (10, 0)):
            changed = bytearray(payload)
            changed[offset] = value
            assert not accepts(repaired(changed)), offset
        changed = bytearray(payload)
        changed[12:14] = (0x1234).to_bytes(2, "little")
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        changed[16] = 1
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        changed[5] = 1
        assert accepts(repaired(changed))

        descriptor = 128
        mutations = (
            (descriptor, ord("a")),          # ID must be uppercase
            (descriptor + 1, ord(" ")),     # no embedded ID padding
            (descriptor + 8, 0x1F),          # printable description
            (descriptor + 55, 0),            # nonzero physical sectors
            (descriptor + 56, 4),            # known size code
            (descriptor + 57, 0),            # nonzero cylinders
            (descriptor + 59, 0),            # repeated count agrees
        )
        for offset, value in mutations:
            changed = bytearray(payload)
            changed[offset] = value
            assert not accepts(repaired(changed)), offset
        changed = bytearray(payload)
        changed[descriptor + 60:descriptor + 62] = (0).to_bytes(2, "little")
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        changed[descriptor + 58] ^= 0x80
        assert not accepts(repaired(changed))

        def descriptor_offset(index: int) -> int:
            return 128 + index * 64

        def word_at(data, offset: int) -> int:
            return int.from_bytes(data[offset:offset + 2], "little")

        first_ids = word_at(payload, descriptor + 60)
        changed = bytearray(payload)
        changed[first_ids + 1] = changed[first_ids]
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        second = descriptor_offset(1)
        changed[second + 60:second + 62] = first_ids.to_bytes(2, "little")
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        changed[-1] = 1
        assert not accepts(repaired(changed))
        changed = bytearray(payload + bytes(128))
        assert not accepts(repaired(changed))

        cylinder = descriptor_offset(51)
        cylinder_ext = word_at(payload, cylinder + 62)
        for relative, value in ((0, 0x02), (0, 0x80), (2, 2), (4, 1)):
            changed = bytearray(payload)
            changed[cylinder_ext + relative] = value
            assert not accepts(repaired(changed)), (relative, value)
        changed = bytearray(payload)
        changed[cylinder_ext + 3:cylinder_ext + 8] = bytes((0x82, 1, 1, 0, 0))
        assert not accepts(repaired(changed))

        mixed = descriptor_offset(103)
        mixed_ext = word_at(payload, mixed + 62)
        changed = bytearray(payload)
        changed[mixed_ext + 1] = 5
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        changed[mixed_ext + 2] = 4
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        changed[mixed_ext + 2:mixed_ext + 8] = bytes((2, 2, 2, 2, 2, 2))
        assert not accepts(repaired(changed))
        changed = bytearray(payload)
        next_mixed = descriptor_offset(104)
        changed[next_mixed + 62:next_mixed + 64] = mixed_ext.to_bytes(2, "little")
        assert not accepts(repaired(changed))

        cpu = Z80(b"")
        cpu.mem[0x100:0x100 + len(code)] = code
        cpu.mem[FDFRAM:FDFRAM + len(payload)] = payload
        cpu.setword(names["FDBLEN"], len(payload))
        cpu.run(names["ENTRY"], limit=3_000_000)
        assert cpu.mem[names["FCOUNT"]] == 107
        assert cpu.word(names["FDBPOOL"]) == 128 + 107 * 64
        assert cpu.mem[FDFRAM + 14:FDFRAM + 16] == payload[14:16]

        for index in (0, 53, 106):
            cpu.a = index
            cpu.run(names["FDBNAME"])
            assert not cpu.carry
            expected = FDFRAM + 128 + index * 64 + 8
            assert cpu.hl == expected
            assert cpu.mem[cpu.hl:cpu.hl + 32] == payload[128 + index * 64 + 8:
                                                        128 + index * 64 + 40]
        cpu.a = 107
        cpu.run(names["FDBDESC"])
        assert cpu.carry

        for kind, supported in ((0x03, 1), (0x83, 0)):
            changed = bytearray(payload)
            changed[cylinder_ext] = kind
            changed = bytearray(repaired(changed))
            cpu = Z80(b"")
            cpu.mem[0x100:0x100 + len(code)] = code
            cpu.mem[FDFRAM:FDFRAM + len(changed)] = changed
            cpu.setword(names["FDBLEN"], len(changed))
            cpu.run(names["ENTRY"], limit=3_000_000)
            assert not cpu.carry
            cpu.a = 51
            cpu.run(names["FDBISSUPPORTED"])
            assert not cpu.carry
            assert (not cpu.z) == bool(supported)

    print("Native FDB reader: framing, descriptors, object ownership and extensions pass")


if __name__ == "__main__":
    main()
