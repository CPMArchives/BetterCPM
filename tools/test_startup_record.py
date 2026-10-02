#!/usr/bin/env python3
"""Qualify the v1 saved startup record and its protected-media placement."""
from __future__ import annotations

from pathlib import Path

from build_system_package import compose
from startup_record import (COMMAND_CAPACITY, HEADER_SIZE, RECORD_SIZE, build,
                            parse)
from system_layout import LAYOUT


def rejected(record: bytes, message: str) -> None:
    try:
        parse(record, system_base=LAYOUT["SYSTEM"])
    except ValueError:
        return
    raise AssertionError(message)


def main() -> None:
    disabled = build(system_base=LAYOUT["SYSTEM"])
    assert len(disabled) == RECORD_SIZE
    assert parse(disabled, system_base=LAYOUT["SYSTEM"]) == ""

    command = "X" * COMMAND_CAPACITY
    enabled = build(command, system_base=LAYOUT["SYSTEM"])
    assert parse(enabled, system_base=LAYOUT["SYSTEM"]) == command

    for offset, message in ((4, "version"), (7, "flags"), (8, "length"),
                            (12, "checksum"), (14, "layout"),
                            (HEADER_SIZE, "command"), (RECORD_SIZE - 1, "tail")):
        damaged = bytearray(enabled)
        damaged[offset] ^= 0x01
        rejected(bytes(damaged), f"damaged {message} was accepted")

    try:
        build("X" * (COMMAND_CAPACITY + 1), system_base=LAYOUT["SYSTEM"])
    except ValueError:
        pass
    else:
        raise AssertionError("overlength startup command was accepted")

    package, _ = compose()
    payload = package[128:]
    assert payload[128:128 + RECORD_SIZE] == disabled
    assert payload[128 + RECORD_SIZE:512] == bytes(128)
    native = (Path(__file__).resolve().parents[1] /
              "build/utilities/SYSBUILD.COM").read_bytes()
    at = native.index(b"BCST")
    assert native[at:at + RECORD_SIZE] == disabled
    print("PASS: startup record validates and occupies protected records 1-2")


if __name__ == "__main__":
    main()
