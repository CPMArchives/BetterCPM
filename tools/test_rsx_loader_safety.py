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
CALLS = 0x3400
SOURCE1 = 0x3600
SOURCE2 = 0x3A00


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


def assemble_selector(work: Path, name: str, relative: str) -> bytes:
    source = expand_layout((ROOT / relative).read_text(encoding="ascii"))
    source = source.replace("        CSEG\n        .PHASE  ",
                            "        ASEG\n        ORG     ")
    source = source.replace("        .DEPHASE\n", "")
    return assemble(ASSEMBLER, source, work / f"{name}.bin",
                    work / f"{name}.lst", LAYOUT["CONFIG"] + 0x380)


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


def assert_overlay(cpu: Z80, first: bytes, final: bytes,
                   split: int, final_prefix: int) -> None:
    base = LAYOUT["RSX"]
    assert bytes(cpu.mem[base:base + split]) == first
    assert bytes(cpu.mem[base + split:base + 0x3F4]) == \
        final[:final_prefix]
    assert bytes(cpu.mem[base + 0x3F4:base + 0x3FD]) == bytes((0xA5,)) * 9
    assert bytes(cpu.mem[base + 0x3FD:base + 0x400]) == final[-3:]


def test_trs80_selector_tail(work: Path) -> None:
    selector = assemble_selector(
        work, "trs80-selector", "src/platform/trs80m4/rsxsel.mac")
    stub = assemble_text(work, "trs80-physical-read", f"""
        ASEG
        ORG     0{LAYOUT['BIOS'] + 51:04X}H
        LD      A,(0{CALLS:04X}H)
        OR      A
        LD      DE,0{SOURCE1:04X}H
        JR      Z,COPY
        LD      DE,0{SOURCE2:04X}H
COPY:   PUSH    HL
        EX      DE,HL
        LD      BC,0200H
        LDIR
        POP     HL
        LD      HL,0{CALLS:04X}H
        INC     (HL)
        XOR     A
        RET
        END
""", LAYOUT["BIOS"] + 51)
    first = bytes((index & 0xFF for index in range(512)))
    final = bytes(((index + 0x40) & 0xFF for index in range(512)))
    cpu = Z80(b"")
    entry = LAYOUT["CONFIG"] + 0x380
    cpu.mem[entry:entry + len(selector)] = selector
    cpu.mem[LAYOUT["BIOS"] + 51:LAYOUT["BIOS"] + 51 + len(stub)] = stub
    cpu.mem[SOURCE1:SOURCE1 + len(first)] = first
    cpu.mem[SOURCE2:SOURCE2 + len(final)] = final
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + 0x400] = bytes((0xA5,)) * 0x400
    cpu.a = 0
    cpu.sp = 0x9000
    cpu.run(entry, limit=5000)
    assert_overlay(cpu, first, final, 0x200, 0x1F4)


def test_z80pack_selector_tail(work: Path) -> None:
    selector = assemble_selector(
        work, "z80pack-selector", "src/platform/z80pack/rsxsel.mac")
    stub = assemble_text(work, "z80pack-system-read", f"""
        ASEG
        ORG     0{LAYOUT['DISK'] + 15:04X}H
        LD      A,(0{CALLS:04X}H)
        OR      A
        LD      DE,0{SOURCE1:04X}H
        JR      Z,SIZE
        LD      DE,0{SOURCE2:04X}H
SIZE:   LD      A,B
        CP      7
        JR      NZ,LAST
        LD      BC,0380H
        JR      COPY
LAST:   LD      BC,0080H
COPY:
        EX      DE,HL
        LDIR
        LD      HL,0{CALLS:04X}H
        INC     (HL)
        XOR     A
        RET
        END
""", LAYOUT["DISK"] + 15)
    first = bytes(((index + 0x10) & 0xFF for index in range(0x380)))
    final = bytes(((index + 0x80) & 0xFF for index in range(0x80)))
    cpu = Z80(b"")
    entry = LAYOUT["CONFIG"] + 0x380
    cpu.mem[entry:entry + len(selector)] = selector
    cpu.mem[LAYOUT["DISK"] + 15:LAYOUT["DISK"] + 15 + len(stub)] = stub
    cpu.mem[SOURCE1:SOURCE1 + len(first)] = first
    cpu.mem[SOURCE2:SOURCE2 + len(final)] = final
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + 0x400] = bytes((0xA5,)) * 0x400
    cpu.a = 0
    cpu.sp = 0x9000
    cpu.run(entry, limit=5000)
    assert_overlay(cpu, first, final, 0x380, 0x74)


def main() -> None:
    for path in (ROOT / "build/system/extensions.bin",
                 ROOT / "build/system/extensions.lst"):
        if not path.is_file():
            raise SystemExit(f"missing built input: {path}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-loader-safety-") as tmp:
        work = Path(tmp)
        test_model4_selector(work)
        test_recovery_stack(work)
        test_trs80_selector_tail(work)
        test_z80pack_selector_tail(work)
    assert symbol("EX_RLOAD") < symbol("EX_RFAIL")
    print("RSX loaders preserve read status and both platform selectors keep "
          "the live replacement frame outside overwritten bytes")


if __name__ == "__main__":
    main()
