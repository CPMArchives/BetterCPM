#!/usr/bin/env python3
"""Distinguish cold history reset from warm/reconstruction preservation."""
from __future__ import annotations

import re
from pathlib import Path

from system_layout import LAYOUT
from test_bios import SENTINEL, Z80, require
from test_system import bdos_symbol
from test_ccp import call as call_ccp
from test_ccp import cpu as ccp_cpu
from test_ccp import symbol as ccp_symbol

ROOT = Path(__file__).resolve().parents[1]
RESIDENT = ROOT / "build/system/resident.bin"
GATEWAY_LISTING = ROOT / "build/system/gateway.lst"


def gateway_symbol(name: str) -> int:
    matches = re.findall(rf"^([0-9a-f]{{4}})\s+.*\b{name}:",
                         GATEWAY_LISTING.read_text(encoding="ascii"),
                         re.MULTILINE | re.IGNORECASE)
    require(matches, f"gateway listing lacks {name}")
    return int(matches[-1], 16)


def seeded_system() -> tuple[Z80, bytes]:
    resident = RESIDENT.read_bytes()
    machine = Z80(b"")
    machine.mem[LAYOUT["SYSTEM"]:LAYOUT["SYSTEM"] + len(resident)] = resident
    history = bytes(b"BH\x01\x01\x04\x00") + bytes((0xA5, 0x5A, 0xC3, 0x3C)) + b"\x03DIR"
    machine.mem[LAYOUT["HISTORY"]:LAYOUT["HISTORY"] + len(history)] = history
    # Stop at the common reconstruction body. The lifecycle distinction being
    # tested occurs entirely in the stable cold/warm gateway entries.
    enter = gateway_symbol("SYS_ENTER")
    machine.mem[enter:enter + 3] = bytes((0xC3, SENTINEL & 0xFF, SENTINEL >> 8))
    return machine, history


def main() -> None:
    history_base = LAYOUT["HISTORY"]

    cold, _seed = seeded_system()
    cold.run(gateway_symbol("SYS_COLD"))
    require(cold.mem[history_base] != ord("B"),
            "cold entry preserved a valid-looking history object")

    # The CCP owns the history representation. Cold entry invalidates it, and
    # the owner's ordinary validation path must create the canonical empty v1
    # object rather than making the gateway duplicate that private format.
    owner = ccp_cpu()
    owner.mem[history_base:LAYOUT["SYSTEM"]] = cold.mem[history_base:LAYOUT["SYSTEM"]]
    call_ccp(owner, ccp_symbol("CCP_HINIT"))
    require(bytes(owner.mem[history_base:history_base + 6]) == b"BH\x01\x00\x00\x00",
            "cold invalidation did not become an empty history-v1 object")

    warm, seed = seeded_system()
    # Warm entry reads protected core state after recovering a loader abort.
    warm.mem[bdos_symbol("UB_DRIVE")] = 2
    warm.run(gateway_symbol("SYS_WARM"))
    require(bytes(warm.mem[history_base:history_base + len(seed)]) == seed,
            "warm entry changed valid persistent history")

    for caller in (0, 3, 31):
        aborted, seed = seeded_system()
        aborted.mem[0x46] = caller
        aborted.mem[0x48] = 1
        aborted.mem[bdos_symbol("UB_USERNO")] = (caller + 1) & 31
        aborted.mem[bdos_symbol("UB_DRIVE")] = 1
        aborted.run(gateway_symbol("SYS_WARM"))
        require(aborted.mem[bdos_symbol("UB_USERNO")] == caller and aborted.mem[0x48] == 0,
                "WBOOT did not recover and disarm an abandoned lookup user")
        require(aborted.a == 1, "lookup recovery changed the warm drive")
        require(bytes(aborted.mem[history_base:history_base + len(seed)]) == seed,
                "lookup recovery changed history")
    ordinary, _ = seeded_system()
    ordinary.mem[0x46] = 3
    ordinary.mem[0x48] = 0
    ordinary.mem[bdos_symbol("UB_USERNO")] = 31
    ordinary.run(gateway_symbol("SYS_WARM"))
    require(ordinary.mem[bdos_symbol("UB_USERNO")] == 31,
            "ordinary WBOOT reverted a program's user selection")
    print("cold/warm history and armed/disarmed loader-abort user recovery passed")


if __name__ == "__main__":
    main()
