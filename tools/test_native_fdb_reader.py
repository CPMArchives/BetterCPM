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

        cpu = Z80(b"")
        cpu.mem[0x100:0x100 + len(code)] = code
        cpu.mem[FDFRAM:FDFRAM + len(payload)] = payload
        cpu.setword(names["FDBLEN"], len(payload))
        cpu.run(names["ENTRY"], limit=3_000_000)
        assert cpu.mem[names["FCOUNT"]] == 107
        assert cpu.word(names["FDBPOOL"]) == 128 + 107 * 64
        assert cpu.mem[FDFRAM + 14:FDFRAM + 16] == payload[14:16]

    print("Native FDB reader: header, version, bounds, reserved bytes and CRC pass")


if __name__ == "__main__":
    main()
