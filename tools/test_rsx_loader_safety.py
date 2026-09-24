#!/usr/bin/env python3
"""Qualify RSX selector status and failure-recovery stack ownership."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT, expand_layout
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER = Path("/Users/nathanael/bin/z80asm")
MARK = 0x3000
STUB = 0x3100
REQUEST = 0x3200


def symbol(name: str) -> int:
    listing = (ROOT / "build/system/extensions.lst").read_text(errors="replace")
    match = re.search(rf"^([0-9a-f]{{4}})\s+.*\b{name}:",
                      listing, re.MULTILINE | re.IGNORECASE)
    if not match:
        raise AssertionError(f"missing extension symbol {name}")
    return int(match.group(1), 16)


def assemble_text(work: Path, name: str, source: str, origin: int) -> bytes:
    return assemble(ASSEMBLER, expand_layout(source), work / f"{name}.bin",
                    work / f"{name}.lst", origin)


def test_model4_selector(work: Path) -> None:
    text = (ROOT / "src/platform/trs80m4/reload.inc").read_text(encoding="ascii")
    entry = text[text.index("M4_RSLOAD:"):text.index("M4_OVLOAD:")]
    image = assemble_text(work, "model4-selector", f"""
        INCLUDE layout.inc
        ASEG
        ORG 0100H
M4_FETCH       EQU     {STUB:04X}H
M4_RLTAB       EQU     3300H
{entry}
        END
""", 0x100)

    for selector in range(4):
        for incoming_zero in (False, True):
            for failure in (False, True):
                cpu = Z80(b"")
                cpu.mem[0x100:0x100 + len(image)] = image
                cpu.mem[STUB:STUB + 4] = (b"\x3E\x55\xB7\xC9" if failure
                                           else b"\xAF\xC9\0\0")
                cpu.mem[LAYOUT["CONFIG"] + 0x380:
                        LAYOUT["CONFIG"] + 0x384] = \
                    bytes((0x32, MARK & 0xFF, MARK >> 8, 0xC9))
                cpu.a = selector
                cpu.z = incoming_zero
                cpu.mem[MARK] = 0xA5
                cpu.run(0x100)
                if failure:
                    assert cpu.a == 0x55 and cpu.mem[MARK] == 0xA5
                else:
                    assert cpu.mem[MARK] == selector


def test_recovery_stack(work: Path) -> None:
    extension = (ROOT / "build/system/extensions.bin").read_bytes()
    stub = assemble_text(work, "recovery-loader", f"""
        INCLUDE layout.inc
        ASEG
        ORG {STUB:04X}H
        CP      1
        JR      NZ,RESTORE
        XOR     A
        RET
RESTORE:
        LD      HL,LY_RSX+03F4H
        LD      DE,LY_RSX+03F5H
        LD      BC,11
        LD      (HL),0A5H
        LDIR
        XOR     A
        RET
        END
""", STUB)
    cpu = Z80(b"")
    cpu.mem[LAYOUT["EXTENSIONS"]:LAYOUT["EXTENSIONS"] + len(extension)] = extension
    cpu.mem[STUB:STUB + len(stub)] = stub
    cpu.mem[LAYOUT["BIOS"] + 60:LAYOUT["BIOS"] + 63] = \
        bytes((0xC3, STUB & 0xFF, STUB >> 8))
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + 4] = b"\x3E\xFF\xB7\xC9"
    cpu.mem[LAYOUT["RSX_STATE"]] = 1
    cpu.mem[REQUEST:REQUEST + 14] = bytes((1, 1)) + bytes(12)
    cpu.c = 202
    cpu.de = REQUEST
    cpu.ix = 0x4567
    cpu.sp = 0x9000
    cpu.run(LAYOUT["EXTENSIONS"], limit=5000)
    assert cpu.a == 0xFF
    assert cpu.ix == 0x4567
    assert cpu.sp == 0x9000
    assert cpu.mem[LAYOUT["RSX"] + 0x3F4:
                   LAYOUT["RSX"] + 0x400] == bytes((0xA5,)) * 12


def main() -> None:
    for path in (ROOT / "build/system/extensions.bin",
                 ROOT / "build/system/extensions.lst"):
        if not path.is_file():
            raise SystemExit(f"missing built input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-loader-safety-") as tmp:
        work = Path(tmp)
        test_model4_selector(work)
        test_recovery_stack(work)
    assert symbol("EX_RLOAD") < symbol("EX_RFAIL")
    print("RSX loader preserves physical-read status and moves failure "
          "recovery off the replaceable manager stack")


if __name__ == "__main__":
    main()
