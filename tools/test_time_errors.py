#!/usr/bin/env python3
"""Execute TIME.COM native-status routing independently of console output."""
from pathlib import Path
import re
from test_bios import Z80, require

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    names = {}
    for line in (ROOT / "build/utilities/time.lst").read_text().splitlines():
        match = re.match(r"^([0-9a-f]{4})\s+.*\s(TM_[A-Z0-9_]+):", line, re.I)
        if match:
            names[match[2]] = int(match[1], 16)
    image = (ROOT / "build/utilities/TIME.COM").read_bytes()
    for status, message in [(8, "TM_SETNO"), (6, "TM_BADREC"),
                            (5, "TM_CERR"), (1, "TM_CERR"),
                            (2, "TM_CERR"), (3, "TM_CERR"), (4, "TM_CERR")]:
        cpu = Z80(b"")
        cpu.mem[0x100:0x100 + len(image)] = image
        # Stop at the shared output boundary: execute the real routing code.
        cpu.mem[names["TM_ERROR"]] = 0xC9
        cpu.a = status
        stack = cpu.sp
        cpu.run(names["TM_CLOCKERR"], limit=50)
        require(cpu.de == names[message], f"status {status} selected wrong message")
        require(cpu.sp == stack, "status routing changed stack balance")
    require(len({names[key] for key in ["TM_SETNO", "TM_BADREC", "TM_CERR", "TM_NOMSG"]}) == 4,
            "SET, input, provider and discovery diagnostics must be distinct")
    print("TIME native error routing: unsupported SET, invalid record, provider errors passed")


if __name__ == "__main__":
    main()
