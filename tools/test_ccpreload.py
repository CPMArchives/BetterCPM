#!/usr/bin/env python3
"""Verify disk-backed CCP restoration and relocation in the Model 4 reloader."""
from __future__ import annotations

import struct
import re
from pathlib import Path
from system_layout import LAYOUT

from test_bios import Z80, require
from build_cpx_module import make_module

ROOT = Path(__file__).resolve().parents[1]
RELOADER = ROOT / "build/trs80/ccpreload.bin"
MODULE = ROOT / "build/ccp/ccp.rlm"
CCP = ROOT / "build/ccp/ccp.bin"
BASIC_MODULE = ROOT / "build/cpx/RCP.CPX"
HELLO_MODULE = ROOT / "build/cpx/HELLO.CPX"
BASE = LAYOUT["RELOADER"]
MODULE_SOURCE = 0x6000
DESCRIPTOR_CCP = (LAYOUT["SYSTEM"] + 0x8C)
SYSTEM_WBOOT = (LAYOUT["SYSTEM"] + 0x23)
PHYSICAL_READ = LAYOUT["BIOS"] + 51
FILE_LOADER = LAYOUT["FILE"]
DIR_LOGIN = LAYOUT["EXTENSIONS"] + 3


def relocated(module: bytes, target: int) -> bytes:
    if module[:4] == b"BCPX":
        link = struct.unpack_from("<H", module, 10)[0]
        size = struct.unpack_from("<H", module, 12)[0]
        count = struct.unpack_from("<H", module, 22)[0]
        payload = struct.unpack_from("<H", module, 26)[0]
        table = struct.unpack_from("<H", module, 28)[0]
    else:
        _magic, _version, header_sectors, link, size, _allocation, _entry, count = (
            struct.unpack_from("<4sBBHHHHH", module))
        payload, table = header_sectors * 512, 16
    image = bytearray(module[payload:payload + size])
    delta = target - link
    for index in range(count):
        offset = struct.unpack_from("<H", module, table + index * 2)[0]
        value = int.from_bytes(image[offset:offset + 2], "little")
        image[offset:offset + 2] = ((value + delta) & 0xFFFF).to_bytes(2, "little")
    return bytes(image)


def run_at(target: int, with_cpx: bool = False, with_two_cpx: bool = False,
           cpx_module: bytes | None = None, expect_reject: bool = False,
           read_failure: int | None = None, reset_failure: bool = False,
           bad_ccp: bool = False, rejected_first: bool = False) -> bytes:
    module = MODULE.read_bytes()
    allocation = struct.unpack_from("<H", module, 10)[0]
    machine = Z80(b"")
    machine.mem[LAYOUT["BIOS"]+66:LAYOUT["BIOS"]+70] = b'\x32\x00\xf7\xc9'
    machine.mem[0xF700] = 0xCC
    reloader = RELOADER.read_bytes()
    machine.mem[BASE:BASE + len(reloader)] = reloader
    # Function 37 is the reloader's only BDOS dependency.  This unit test
    # supplies a successful reset while the full boot tests exercise the real
    # production BDOS at the same address.
    machine.mem[LAYOUT["BDOS"]:LAYOUT["BDOS"] + 2] = bytes((0xAF, 0xC9))
    listing = (ROOT / "build/trs80/ccpreload.lst").read_text()
    table = int(re.findall(r"^([0-9a-f]{4})\s+.*\bCRSECTS:",
                           listing, re.MULTILINE | re.IGNORECASE)[-1], 16) - BASE
    sectors = [tuple(reloader[table + index * 3:table + index * 3 + 3])
               for index in range(13)]

    def install_slots(first: int, content: bytes) -> None:
        padded = content.ljust(((len(content) + 511) // 512) * 512, b"\x00")
        for offset in range(0, len(padded), 512):
            _track, side, physical = sectors[first + offset // 512]
            source = MODULE_SOURCE + (side * 16 + physical - 6) * 512
            machine.mem[source:source + 512] = padded[offset:offset + 512]

    install_slots(0, (b'INVALID' + module[7:]) if bad_ccp else module)
    # Protected filename-loader test double. OPEN selects RCP/HELLO from the
    # first stem byte; NEXT copies a 512-byte unit and advances; RESET rewinds.
    # Keep the test provider below every possible CCP destination.  The
    # old D010h stubs became part of the 53K CCP image after layout compaction
    # and were overwritten while the loader was still using them.
    vectors = bytes((0xC3, 0x10, 0x50, 0xC3, 0x00, 0x51,
                     0xC3, 0x00, 0x52))
    open_stub = bytes((
        0x7E, 0xFE, 0x52, 0x11, 0x00, 0x20, 0x28, 0x03,
        0x11, 0x00, 0x48, 0xEB, 0x22, 0x00, 0x59,
        0x22, 0x02, 0x59, 0xAF, 0xC9,
    ))
    next_stub = bytes((
        0xE5, 0x2A, 0x00, 0x59, 0xD1,
        0x01, 0x00, 0x02, 0xED, 0xB0, 0xEB, 0xE5,
        0x2A, 0x00, 0x59, 0x11, 0x00, 0x02, 0x19,
        0x22, 0x00, 0x59, 0xE1, 0xAF, 0xC9,
    ))
    reset_stub = bytes((0x2A, 0x02, 0x59, 0x22, 0x00, 0x59, 0xAF, 0xC9))
    machine.mem[FILE_LOADER:FILE_LOADER + len(vectors)] = vectors
    machine.mem[0x5010:0x5010 + len(open_stub)] = open_stub
    if read_failure is not None:
        next_stub = bytes((0x3A, 0x04, 0x59, 0x3C, 0x32, 0x04, 0x59,
                           0xFE, read_failure, 0x20, 4, 0x3E, 1, 0xB7, 0xC9)) + next_stub
    if reset_failure:
        reset_stub = b'\x3e\x01\xb7\xc9'
    machine.mem[0x5100:0x5100 + len(next_stub)] = next_stub
    machine.mem[0x5200:0x5200 + len(reset_stub)] = reset_stub
    # Count diagnostic calls through real reloader instructions. Function 37
    # still succeeds; Function 9 is intercepted before any host console I/O.
    diagnostic_stub = bytes((0x79, 0xFE, 9, 0x20, 7,
                             0x3A, 0x05, 0x59, 0x3C, 0x32, 0x05, 0x59,
                             0xAF, 0xC9))
    machine.mem[LAYOUT['BDOS']:LAYOUT['BDOS'] + 3] = b'\xc3\x00\x53'
    machine.mem[0x5300:0x5300 + len(diagnostic_stub)] = diagnostic_stub
    machine.mem[DIR_LOGIN:DIR_LOGIN + 2] = bytes((0xAF, 0xC9))
    cpx_allocation = 0
    if with_two_cpx:
        basic_module = BASIC_MODULE.read_bytes()
        hello_module = HELLO_MODULE.read_bytes()
        if cpx_module is not None:
            if rejected_first:
                basic_module = cpx_module
            else:
                hello_module = cpx_module
        machine.mem[0x2000:0x2000 + len(basic_module)] = basic_module
        machine.mem[0x4800:0x4800 + len(hello_module)] = hello_module
        machine.mem[(LAYOUT["SYSTEM"] + 0x94)] = 2
        machine.mem[(LAYOUT["SYSTEM"] + 0x96):(LAYOUT["SYSTEM"] + 0x9E)] = b"RCP     "
        machine.mem[(LAYOUT["SYSTEM"] + 0x9E):(LAYOUT["SYSTEM"] + 0xA6)] = b"HELLO   "
        cpx_allocation = (struct.unpack_from("<H", BASIC_MODULE.read_bytes(), 14)[0] +
                          struct.unpack_from("<H", HELLO_MODULE.read_bytes(), 14)[0])
    elif with_cpx:
        if cpx_module is None:
            payload = bytes((0, 0, 8, 0x80, 0, 0, 0, 0,
                             0xC9, 0xC9, 0xC9))
            file_module = make_module(
                name="RCP", version=(0, 0), commands=[], linked_base=0x8000,
                code=payload, relocations=[2], init_offset=9,
                shutdown_offset=10)
        else:
            file_module = cpx_module
        machine.mem[0x2000:0x2000 + len(file_module)] = file_module
        machine.mem[(LAYOUT["SYSTEM"] + 0x94)] = 1
        machine.mem[(LAYOUT["SYSTEM"] + 0x96):(LAYOUT["SYSTEM"] + 0x9E)] = b"RCP     "
        cpx_allocation = 0x100

    gateway = target + allocation + cpx_allocation
    machine.mem[(LAYOUT["SYSTEM"] + 0x90):(LAYOUT["SYSTEM"] + 0x92)] = gateway.to_bytes(2, "little")
    machine.mem[target:target + allocation] = bytes((0xA5,)) * allocation

    # Source fixtures are indexed by side and actual Model 4 sector number.
    # Eleven command sectors cross the side boundary, so C alone is no longer
    # a unique key as it was for the original seven-sector carrier.
    reader = bytes((
        0xE5,                   # PUSH HL (destination)
        # Compact the fixture below the destination; physical sector 6 is
        # the first carrier slot. The unadjusted final slot overlapped CCP.
        0x78, 0x07, 0x07, 0x07, 0x07, 0x81, 0xD6, 6,
        0x67, 0x2E, 0x00, 0x29,        # HL=A*512
        0x11, 0x00, 0x60, 0x19,  # HL+=6000h
        0xD1,                   # POP DE (destination)
        0x01, 0x00, 0x02, 0xED, 0xB0,  # LDIR 512 bytes
        0xEB,                   # return HL=destination+512 like M4_READ
        0xAF, 0xC9,             # success
    ))
    machine.mem[0x5800:0x5800 + len(reader)] = reader
    machine.mem[PHYSICAL_READ:PHYSICAL_READ + 3] = b"\xc3\x00\x58"
    machine.mem[SYSTEM_WBOOT:SYSTEM_WBOOT + 2] = bytes((0x18, 0xFE))
    try:
        machine.run(BASE, limit=200000)
    except AssertionError as error:
        require("execution limit reached" in str(error),
                f"reloader failed unexpectedly: {error}")
    if bad_ccp:
        failure = int(re.findall(r"^([0-9a-f]{4})\s+.*\bCRFAIL:",
                                 listing, re.MULTILINE | re.IGNORECASE)[-1], 16)
        require(machine.pc == failure,
                f"malformed CPX stopped at {machine.pc:04X}h, not CRFAIL")
        require(machine.mem[0x5905] == 0, "required CCP failure was treated as optional")
        return b""
    if expect_reject:
        require(machine.pc == SYSTEM_WBOOT, "failed optional CPX prevented CCP recovery")
        require(machine.mem[0x5905] == 1, "failed optional CPX did not report CPX?")
        require(machine.mem[LAYOUT['SYSTEM'] + 0x94] == (2 if with_two_cpx else 1),
                "recovery changed the persistent CPX profile")
        target += (struct.unpack_from('<H', (BASIC_MODULE if rejected_first else HELLO_MODULE).read_bytes(), 14)[0]
                   if with_two_cpx else cpx_allocation)
        if with_two_cpx and rejected_first:
            hello_base = gateway - struct.unpack_from('<H', HELLO_MODULE.read_bytes(), 14)[0]
            require(machine.word(0x004B) == hello_base and machine.word(hello_base) == 0,
                    "valid CPX after rejected first carrier was not linked")
            require(bytes(machine.mem[hello_base:hello_base + len(relocated(
                        HELLO_MODULE.read_bytes(), hello_base))]) ==
                    relocated(HELLO_MODULE.read_bytes(), hello_base),
                    "valid following CPX was damaged by recovery")
        elif with_two_cpx:
            basic_base = gateway - struct.unpack_from('<H', BASIC_MODULE.read_bytes(), 14)[0]
            require(machine.word(0x004B) == basic_base and machine.word(basic_base) == 0,
                    "failed later module damaged the earlier valid CPX chain")
        else:
            require(machine.word(0x004B) == 0, "failed CPX was published")
    else:
        require(machine.mem[0x5905] == 0, "valid reconstruction reported CPX failure")
    expected = relocated(module, target)
    require(machine.mem[0xF700] == 5, "reconstruction did not reset monitor sequence")
    actual = bytes(machine.mem[target:target + len(expected)])
    mismatch = next((index for index, pair in enumerate(zip(actual, expected))
                     if pair[0] != pair[1]), None)
    state = {}
    for name in ("CRMLINK", "CRMSIZE", "CRMALLOC", "CRMRELOCS",
                 "CRMHEADSZ", "CRMPAYLOAD", "CRMRELTABLE", "CRSKIP",
                 "CRBASE", "CRSLOT"):
        address = int(re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:",
                                 listing, re.MULTILINE | re.IGNORECASE)[-1], 16)
        state[name] = machine.word(address) if name != "CRSLOT" else machine.mem[address]
    require(actual == expected,
            f"CCP was not restored and relocated at {target:04X}h; "
            f"reloader stopped at {machine.pc:04X}h; "
            f"state={state}; "
            f"header={bytes(machine.mem[LAYOUT['MODULEBUF']:LAYOUT['MODULEBUF'] + 16]).hex()}; "
            f"first mismatch={mismatch!r}; "
            f"actual={actual[mismatch:mismatch + 16].hex() if mismatch is not None else ''} "
            f"expected={expected[mismatch:mismatch + 16].hex() if mismatch is not None else ''}")
    if with_two_cpx and not expect_reject:
        basic_allocation = struct.unpack_from("<H", BASIC_MODULE.read_bytes(), 14)[0]
        hello_allocation = struct.unpack_from("<H", HELLO_MODULE.read_bytes(), 14)[0]
        basic_base = gateway - basic_allocation
        hello_base = basic_base - hello_allocation
        require(machine.word(0x004B) == basic_base and
                machine.word((LAYOUT["SYSTEM"] + 0x86)) == 0 and
                machine.word(basic_base) == hello_base and
                machine.word(hello_base) == 0,
                "two-module CPX chain was not restored in table order")
        require(bytes(machine.mem[basic_base + 4:basic_base + len(relocated(
                    BASIC_MODULE.read_bytes(), basic_base))]) ==
                relocated(BASIC_MODULE.read_bytes(), basic_base)[4:],
                "linking HELLO corrupted relocated RCP.CPX payload")
        require(bytes(machine.mem[hello_base:hello_base + len(relocated(
                    HELLO_MODULE.read_bytes(), hello_base))]) ==
                relocated(HELLO_MODULE.read_bytes(), hello_base),
                "HELLO.CPX relocation or payload integrity failed")
    elif with_cpx and not expect_reject:
        cpx_base = gateway - 0x100
        init = struct.unpack_from("<H", file_module, 18)[0]
        shutdown = struct.unpack_from("<H", file_module, 20)[0]
        expected_init = 0 if init == 0xFFFF else cpx_base + init
        expected_shutdown = 0 if shutdown == 0xFFFF else cpx_base + shutdown
        require(machine.word(0x004B) == cpx_base and
                machine.word((LAYOUT["SYSTEM"] + 0x86)) == 0 and
                machine.word(cpx_base) == 0 and
                machine.word(cpx_base + 2) == cpx_base + 8 and
                machine.word(cpx_base + 4) == expected_init and
                machine.word(cpx_base + 6) == expected_shutdown,
                "ordered CPX profile was not restored, relocated, and linked")
    return expected


def main() -> None:
    module = MODULE.read_bytes()
    allocation = struct.unpack_from("<H", module, 10)[0]
    calculated = LAYOUT["TPA"] - allocation
    require(run_at(calculated) == relocated(module, calculated),
            "calculated-base module payload was not relocated correctly")
    # Derive a deliberately non-page-aligned alternate below the live base.
    # A fixed B601h target eventually crossed C100h as the CCP grew and tested
    # the loader's bounds rejection rather than relocation.
    alternate_target = calculated - 0x1EC
    alternate = run_at(alternate_target)
    require(alternate != CCP.read_bytes(),
            "alternate-base CCP did not apply relocation records")
    print(f"disk-backed CCP restoration passed at calculated {calculated:04X}h")
    print(f"relocatable CCP restoration passed at {alternate_target:04X}h")
    run_at(calculated - 0x100, with_cpx=True)
    print("one-module CPX profile restored with lifecycle entries")
    bad_payload = bytes((0, 0, 8, 0x80, 0, 0, 0, 0,
                         0xC9, 0xC9, 0xC9))
    malformed = bytearray(make_module(
        name="RCP", version=(0, 0), commands=[], linked_base=0x8000,
        code=bad_payload, relocations=[2]))
    struct.pack_into("<H", malformed, 18, len(bad_payload))
    run_at(calculated - 0x100, with_cpx=True, cpx_module=bytes(malformed),
           expect_reject=True)
    print("out-of-range CPX lifecycle entry rejected with bare CCP recovery")
    run_at(calculated - 0x100, with_cpx=True,
           cpx_module=b'INVALID HEADER'.ljust(128, b'\0'), expect_reject=True)
    valid = make_module(name='RCP', version=(0, 0), commands=[], linked_base=0x8000,
                        code=bad_payload, relocations=[2])
    for field, value in ((6, 2), (8, 1), (12, 0), (14, 1),
                         (16, len(bad_payload)), (20, len(bad_payload)),
                         (24, 0), (26, 0), (28, 0xFFFF)):
        invalid = bytearray(valid)
        struct.pack_into('<H', invalid, field, value)
        run_at(calculated - 0x100, with_cpx=True,
               cpx_module=bytes(invalid), expect_reject=True)
    bad_relocation = bytearray(valid)
    struct.pack_into('<H', bad_relocation, 48, len(bad_payload))
    run_at(calculated - 0x100, with_cpx=True,
           cpx_module=bytes(bad_relocation), expect_reject=True)
    for failure in (1, 2, 3):
        run_at(calculated - 0x100, with_cpx=True,
               cpx_module=valid, read_failure=failure, expect_reject=True)
    run_at(calculated - 0x100, with_cpx=True, cpx_module=valid,
           reset_failure=True, expect_reject=True)
    run_at(calculated, bad_ccp=True)
    print("signature/layout/payload/reset/relocation failures recover; required CCP stays fatal")
    cpx_allocation = (
        struct.unpack_from("<H", BASIC_MODULE.read_bytes(), 14)[0] +
        struct.unpack_from("<H", HELLO_MODULE.read_bytes(), 14)[0]
    )
    two_cpx_target = 0xBFFD - allocation - cpx_allocation
    run_at(two_cpx_target, with_two_cpx=True)
    print("real RCP and HELLO modules restored, relocated, and linked")
    damaged_hello = bytearray(HELLO_MODULE.read_bytes())
    struct.pack_into('<H', damaged_hello, 20, struct.unpack_from('<H', damaged_hello, 12)[0])
    run_at(two_cpx_target, with_two_cpx=True,
           cpx_module=bytes(damaged_hello), expect_reject=True)
    print("late failure of second CPX preserves first CPX and restores allocation")
    run_at(two_cpx_target, with_two_cpx=True, rejected_first=True,
           cpx_module=b'INVALID HEADER'.ljust(128, b'\0'), expect_reject=True)
    print("valid following CPX loads after first carrier rejection")


if __name__ == "__main__":
    main()
