#!/usr/bin/env python3
"""Exercise the Stage-2 BRSX validator against in-memory carrier streams."""
from __future__ import annotations

import tempfile
from pathlib import Path

from build_ccp import assemble
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "build/system/rsxvalidator.bin"
TEST = ROOT / "build/rsx/TEST.RSX"
HELLO = ROOT / "build/rsx/HELLO.RSX"
REQUEST = 0x7000
STREAM = 0x6000
COUNT = 0x5FFF


def file_stub(work: Path) -> bytes:
    source = f"""
        ASEG
        ORG     0{LAYOUT['FILE']:04X}H
        JP      OPEN
        JP      NEXT
        JP      OPEN
OPEN:   XOR     A
        LD      ({COUNT:04X}H),A
        RET
NEXT:   PUSH    HL
        EX      DE,HL
        LD      A,({COUNT:04X}H)
        LD      L,A
        LD      H,0
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        ADD     HL,HL
        LD      BC,{STREAM:04X}H
        ADD     HL,BC
        LD      BC,0200H
        LDIR
        POP     HL
        LD      DE,0200H
        ADD     HL,DE
        LD      A,({COUNT:04X}H)
        INC     A
        LD      ({COUNT:04X}H),A
        XOR     A
        RET
        END
"""
    return assemble(Path("/Users/nathanael/bin/z80asm"), source,
                    work / "stub.bin", work / "stub.lst", LAYOUT["FILE"])


def validate(validator: bytes, stub: bytes, carrier: bytes) -> int:
    cpu = Z80(b"")
    cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + len(validator)] = validator
    cpu.mem[LAYOUT["FILE"]:LAYOUT["FILE"] + len(stub)] = stub
    cpu.mem[STREAM:STREAM + 1024] = carrier[:1024].ljust(1024, b"\0")
    cpu.mem[REQUEST:REQUEST + 14] = bytes((1, 1, 0, 0)) + b"TEST    " + bytes(2)
    cpu.de = REQUEST
    cpu.run(LAYOUT["RSX"], limit=30000)
    return cpu.a


def main() -> None:
    validator = VALIDATOR.read_bytes()
    require(0 < len(validator) <= 893, "validator does not fit overlay slot")
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-validator-") as temporary:
        stub = file_stub(Path(temporary))
        v2 = bytearray(TEST.read_bytes())
        require(validate(validator, stub, v2) == 0,
                "valid BRSX-v2 TEST carrier was rejected")
        v1 = HELLO.read_bytes()
        require(validate(validator, stub, v1) == 0,
                "valid legacy BRSX-v1 carrier was rejected")
        bad_class = bytearray(v2)
        bad_class[8] = 1
        require(validate(validator, stub, bad_class) == 0xFF,
                "unsupported STATEFUL carrier was accepted in Stage 2")
        bad_entry = bytearray(v2)
        metadata = 512 + int.from_bytes(bad_entry[12:14], "little")
        bad_entry[metadata + 20:metadata + 22] = bad_entry[12:14]
        require(validate(validator, stub, bad_entry) == 0xFF,
                "out-of-payload callable entry was accepted")
        bad_length = bytearray(v2)
        bad_length[metadata + 13] = 9
        require(validate(validator, stub, bad_length) == 0xFF,
                "malformed callable record was accepted")
        code = bytes(16)
        pointers = bytearray(make_module(
            name="PTRTEST", version=(0, 1), services=[], linked_base=0x8000,
            code=code, relocations=[], entry_offset=8, format_version=2,
            callable_services=[(b"PTRS", 1, 0, 8, 0)],
            runtime_pointers=[10, 12]))
        require(validate(validator, stub, pointers) == 0,
                "valid sorted runtime-pointer record was rejected")
        marker = pointers.index(bytes((3, 4)))
        pointers[marker + 2:marker + 6] = bytes((12, 0, 10, 0))
        require(validate(validator, stub, pointers) == 0xFF,
                "unsorted runtime-pointer record was accepted")
        duplicate = make_module(
            name="DUPTEST", version=(0, 1), services=[], linked_base=0x8000,
            code=code, relocations=[], entry_offset=8, format_version=2,
            callable_services=[(b"DUPL", 1, 0, 8, 0),
                               (b"DUPL", 1, 1, 9, 0)])
        require(validate(validator, stub, duplicate) == 0xFF,
                "duplicate service IDs within one provider were accepted")
    print("BRSX validator accepts v1/v2 and rejects class, entry, and framing errors")


if __name__ == "__main__":
    main()
