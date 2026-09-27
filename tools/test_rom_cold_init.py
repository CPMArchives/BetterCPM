#!/usr/bin/env python3
"""Execute the isolated z80pack ROM cold initializer and verify its writes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from system_layout import LAYOUT
from test_bios import Z80, require

CODE_ADDRESS = 0x8000
TEMPLATE_ADDRESS = 0x7000
STACK_ADDRESS = 0xF500


def run(code: bytes, template: bytes, bdos: int) -> bytearray:
    machine = Z80(b"")
    machine.mem[:] = bytes((0xA5,)) * 65536
    machine.mem[CODE_ADDRESS:CODE_ADDRESS + len(code)] = code
    machine.mem[TEMPLATE_ADDRESS:TEMPLATE_ADDRESS + len(template)] = template
    machine.pc = CODE_ADDRESS
    machine.sp = STACK_ADDRESS
    machine.hl = TEMPLATE_ADDRESS
    machine.ix = bdos
    machine.run(CODE_ADDRESS, limit=100)
    return machine.mem


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--initializer", type=Path, required=True)
    args = parser.parse_args()
    template_dir = args.template.resolve()
    initializer_dir = args.initializer.resolve()
    template = (template_dir / "ram-init.bin").read_bytes()
    code = (initializer_dir / "cold-init.bin").read_bytes()
    manifest = json.loads(
        (initializer_dir / "cold-init.json").read_text(encoding="ascii"))
    require(hashlib.sha256(code).hexdigest() == manifest["sha256"],
            "cold initializer hash mismatch")
    require(manifest["position_independent"] is True,
            "cold initializer is not declared position independent")
    require(manifest["template_bytes"] == len(template),
            "cold initializer and template sizes disagree")

    for bdos in (0xE123, 0xF234):
        memory = run(code, template, bdos)
        expected = bytearray(template)
        expected[0:3] = bytes((0xC3, bdos & 0xFF, bdos >> 8))
        expected[LAYOUT["HISTORY"] - LAYOUT["TPA"]] = 0
        actual = memory[LAYOUT["TPA"]:LAYOUT["TPA"] + len(template)]
        require(actual == expected,
                f"cold initializer produced the wrong RAM image for BDOS {bdos:04X}h")
        require(memory[TEMPLATE_ADDRESS:TEMPLATE_ADDRESS + len(template)] == template,
                "cold initializer modified its immutable template")
        require(memory[LAYOUT["TPA"] - 1] == 0xA5 and
                memory[LAYOUT["TPA"] + len(template)] == 0xA5,
                "cold initializer wrote outside the accepted RAM image")

    require(manifest["rom_spare_after_initializer"] >= 0,
            "cold initializer exceeded the protected-ROM budget")
    print(f"ROM cold initializer executed: {len(template)} RAM bytes, "
          f"two BDOS targets, {manifest['rom_spare_after_initializer']} ROM bytes spare")


if __name__ == "__main__":
    main()
