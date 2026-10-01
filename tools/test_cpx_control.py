#!/usr/bin/env python3
"""Exercise the protected name-based Function 176 profile handler."""
from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "build/system/config.bin"
ENTRY = LAYOUT["CONFIG"] + 9
COUNT = LAYOUT["SYSTEM"] + 0x94
TABLE = LAYOUT["SYSTEM"] + 0x96
REQUEST = 0x7000


def padded(name: str) -> bytes:
    return name.encode("ascii").ljust(8, b" ")


def main() -> None:
    cpu = Z80(b"")
    image = CONFIG.read_bytes()
    cpu.mem[LAYOUT["CONFIG"]:LAYOUT["CONFIG"] + len(image)] = image
    link = (ROOT / "build/system/cpxlink.inc").read_text(encoding="ascii")
    return_address = int(link.split("EX_RETURN EQU 0", 1)[1].split("H", 1)[0], 16)
    cpu.mem[return_address] = 0xC9
    cpu.mem[COUNT] = 1
    cpu.mem[TABLE:TABLE + 32] = padded("RCP") + bytes(24)

    def call(operation: int, name: str = "", index: int = 0,
             version: int = 1) -> int:
        request = bytes((version, operation, index, 0)) + padded(name)
        cpu.mem[REQUEST:REQUEST + 12] = request
        cpu.de = REQUEST
        cpu.run(ENTRY, limit=5000)
        require(cpu.de == REQUEST, "Function 176 did not preserve DE")
        return cpu.a

    before = bytes(cpu.mem[COUNT:TABLE + 32])
    require(call(0, version=2) == 0xFF and
            bytes(cpu.mem[COUNT:TABLE + 32]) == before,
            "Function 176 accepted an unknown request version")
    require(call(3) == 0xFF, "Function 176 accepted an unknown operation")
    require(call(0, index=0) == 1 and
            bytes(cpu.mem[REQUEST + 4:REQUEST + 12]) == padded("RCP"),
            "Function 176 did not enumerate the initial CPX")
    require(call(0, index=1) == 0, "Function 176 missed enumeration end")

    require(call(1, "TOOLS") == 0 and cpu.mem[COUNT] == 2 and
            bytes(cpu.mem[TABLE:TABLE + 16]) == padded("RCP") + padded("TOOLS"),
            "Function 176 did not append an arbitrary CPX name")
    require(call(1, "TOOLS") == 0 and cpu.mem[COUNT] == 2,
            "duplicate CPX load was not idempotent")
    require(call(1, "") == 0xFF and call(2, "") == 0xFF,
            "Function 176 accepted a blank CPX name")

    require(call(1, "HELLO") == 0 and call(1, "EXTRA") == 0 and
            cpu.mem[COUNT] == 4 and bytes(cpu.mem[TABLE:TABLE + 32]) ==
            padded("RCP") + padded("TOOLS") + padded("HELLO") + padded("EXTRA"),
            "Function 176 did not fill four profile slots in order: "
            f"count={cpu.mem[COUNT]} table={bytes(cpu.mem[TABLE:TABLE + 32])!r}")
    full = bytes(cpu.mem[COUNT:TABLE + 32])
    require(call(1, "FIFTH") == 0xFF and
            bytes(cpu.mem[COUNT:TABLE + 32]) == full,
            "Function 176 overflowed the four-record profile")

    require(call(2, "TOOLS") == 0 and cpu.mem[COUNT] == 3 and
            bytes(cpu.mem[TABLE:TABLE + 24]) ==
            padded("RCP") + padded("HELLO") + padded("EXTRA"),
            "Function 176 did not preserve order after middle removal: "
            f"count={cpu.mem[COUNT]} table={bytes(cpu.mem[TABLE:TABLE + 32])!r}")
    require(call(2, "MISSING") == 0 and cpu.mem[COUNT] == 3,
            "absent CPX unload was not idempotent")
    for index, name in enumerate(("RCP", "HELLO", "EXTRA")):
        require(call(0, index=index) == 1 and
                bytes(cpu.mem[REQUEST + 4:REQUEST + 12]) == padded(name),
                f"Function 176 enumeration lost {name}")
    require(call(0, index=3) == 0, "Function 176 enumeration exceeded count")

    print("Function 176 name-based enumeration, load, capacity, and unload passed")


if __name__ == "__main__":
    main()
