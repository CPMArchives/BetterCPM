#!/usr/bin/env python3
"""Verify post-reconstruction BRSX-v2 descriptor materialization."""
from __future__ import annotations

import tempfile
from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80, require
from test_rsxvalidator import COUNT, STREAM, file_stub

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / "build/system/rsxpublish.bin"
TEST = ROOT / "build/rsx/TEST.RSX"
BASE = 0xD004
HEAD = LAYOUT["SYSTEM"] + 0x84


def main() -> None:
    publisher = PUBLISHER.read_bytes()
    carrier = TEST.read_bytes()
    code_size = int.from_bytes(carrier[12:14], "little")
    allocation = int.from_bytes(carrier[14:16], "little")
    metadata = 512 + code_size
    advertisement = carrier[metadata + 14:metadata + 24]
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-publish-") as temporary:
        stub = file_stub(Path(temporary))
        cpu = Z80(b"")
        cpu.mem[LAYOUT["RSX"]:LAYOUT["RSX"] + len(publisher)] = publisher
        cpu.mem[LAYOUT["FILE"]:LAYOUT["FILE"] + len(stub)] = stub
        cpu.mem[STREAM:STREAM + 1024] = carrier[:1024].ljust(1024, b"\0")
        cpu.mem[BASE:BASE + code_size] = carrier[512:512 + code_size]
        cpu.mem[BASE + code_size:BASE + allocation] = bytes(
            (0xA5,)) * (allocation - code_size)
        cpu.setword(BASE, LAYOUT["BDOS"])
        cpu.setword(BASE + 2, BASE + 8)
        cpu.mem[LAYOUT["RSX_STATE"]] = 1
        cpu.mem[LAYOUT["RSX_STATE"] + 1:LAYOUT["RSX_STATE"] + 9] = b"TEST    "
        cpu.setword(HEAD, BASE)
        cpu.mem[COUNT] = 0
        cpu.run(LAYOUT["RSX"], limit=30000)
        require(cpu.a == 0, "publisher rejected validated TEST carrier")
        offset = cpu.word(BASE + 6)
        require(cpu.mem[BASE + 4] == 1 and cpu.mem[BASE + 5] == 0 and
                offset == allocation - 10,
                "runtime provider header was not published")
        require(bytes(cpu.mem[BASE + offset:BASE + offset + 10]) == advertisement,
                "callable advertisement was not materialized")
        require(bytes(cpu.mem[BASE + code_size:BASE + offset]) ==
                bytes(offset - code_size), "provider allocation tail was not zeroed")
    print("BRSX-v2 descriptor publication and allocation-tail clearing passed")


if __name__ == "__main__":
    main()
