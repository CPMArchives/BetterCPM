#!/usr/bin/env python3
"""Execute TIME command parsing and native GET/SET dispatch with controlled services."""
from pathlib import Path
import re
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    names = {}
    for line in (ROOT / "build/utilities/time.lst").read_text().splitlines():
        match = re.match(r"^([0-9a-f]{4})\s+.*\s([A-Z][A-Z0-9_]*):", line, re.I)
        if match:
            names[match[2]] = int(match[1], 16)
    image = (ROOT / "build/utilities/TIME.COM").read_bytes()

    def fixture(tail):
        cpu = Z80(b"")
        cpu.mem[0x100:0x100 + len(image)] = image
        cpu.mem[0x80] = len(tail)
        cpu.mem[0x81:0x81 + len(tail)] = tail.encode("ascii")
        return cpu

    for tail, record in [(" /SET 34 12 23 59 58", bytes.fromhex("34 12 23 59 58")),
                         ("/set ff ff 00 00 00", bytes.fromhex("ff ff 00 00 00")),
                         ("/SET 00 00 09 08 07", bytes.fromhex("00 00 09 08 07"))]:
        cpu = fixture(tail)
        cpu.run(names["TM_PARSE"])
        require(cpu.z and cpu.mem[names["TM_MODE"]] == 2, f"valid SET rejected: {tail}")
        require(bytes(cpu.mem[names["TM_REQUEST"]:names["TM_REQUEST"] + 10]) ==
                bytes((1, 10, 1, 0)) + record + b"\0", "wrong canonical SET request")

    invalid = ["/SET", "/SET 34 12 24 00 00", "/SET 34 12 00 60 00",
               "/SET 34 12 00 00 60", "/SET 34 12 1A 00 00",
               "/SET 34 12 00 5A 00", "/SET 34 12 00 00 5A",
               "/SET 3G 12 00 00 00", "/SET 34 12 00 00 0",
               "/SET 34 12 00 00 00 X", "/GET 34 12 00 00 00",
               "/SETX34 12 00 00 00", "/SET 34-12 00 00 00"]
    for tail in invalid:
        cpu = fixture(tail)
        cpu.run(names["TM_PARSE"])
        require(not cpu.z, f"invalid SET accepted: {tail}")
        # Trap lookup with HALT; malformed input must reach usage first.
        cpu.mem[5] = 0x76
        cpu.mem[names["TM_USAGE"]] = 0xC9
        cpu.run(names["START"])

    for status, target in [(0, "TM_SETDONE"), (8, "TM_CLOCKERR"),
                           (6, "TM_CLOCKERR"), (5, "TM_CLOCKERR")]:
        cpu = fixture("/SET 34 12 23 59 58")
        # Controlled registry exposes a service at 7000h. Real utility dispatch
        # must pass the canonical request in DE, operation 1, and balance SP.
        cpu.mem[5:11] = bytes((0x21, 0, 0x70, 0xAF, 0xC9, 0))
        cpu.mem[0x7000:0x7003] = bytes((0x3E, status, 0xC9))
        for key in ["TM_SETDONE", "TM_CLOCKERR"]:
            cpu.mem[names[key]] = 0xC9
        before = cpu.sp
        cpu.run(names["START"])
        require(cpu.de == names["TM_REQUEST"] and cpu.sp == before, "wrong request or stack")
        require(cpu.pc == 0xFFFF, "utility did not return at result boundary")
        # Exercise real result branching separately with only expected target
        # returning; the unexpected target traps.
        cpu = fixture("")
        cpu.mem[names["TM_MODE"]] = 2
        cpu.mem[names["TM_SETDONE"]] = 0xC9 if status == 0 else 0x76
        cpu.mem[names["TM_CLOCKERR"]] = 0x76 if status == 0 else 0xC9
        cpu.a = status
        cpu.run(names["TM_GOT"])

    cpu = fixture("/SET 34 12 23 59 58")
    cpu.mem[5:11] = bytes((0x21, 0, 0, 0x3E, 1, 0xC9))
    cpu.mem[names["TM_NOCLOCK"]] = 0xC9
    cpu.run(names["START"])
    require(cpu.mem[names["TM_DSTAT"]] == 1, "missing service was not reported")
    for tail, mode in [("", 0), ("   ", 0), ("/PROVIDER", 1), (" /provider", 1)]:
        cpu = fixture(tail)
        cpu.run(names["TM_PARSE"])
        require(cpu.z and cpu.mem[names["TM_MODE"]] == mode, "GET/provider parse regression")
    cpu = fixture("")
    cpu.mem[5:10] = bytes((0x21, 0, 0x70, 0xAF, 0xC9))
    cpu.mem[0x7000] = 0xC9
    cpu.mem[names["TM_GOT"]] = 0xC9
    cpu.run(names["START"])
    require(cpu.mem[names["TM_REQUEST"] + 2] == 0, "GET operation changed")
    print("TIME SET parsing, canonical request, dispatch, failures and GET/provider regression passed")


if __name__ == "__main__":
    main()
