#!/usr/bin/env python3
"""Verify that CCP reconstruction preserves protected command history."""
from system_layout import LAYOUT
from test_bios import require
from test_ccp import BASE, call, cpu, symbol


def main() -> None:
    machine = cpu()
    command = b"BASELINE COMMAND"
    count = symbol("CCP_COUNT")
    data = symbol("CCP_DATA")
    machine.mem[count] = len(command)
    machine.mem[data:data + len(command)] = command
    call(machine, symbol("CCP_HADD"))

    history = LAYOUT["HISTORY"]
    before = bytes(machine.mem[history:LAYOUT["SYSTEM"]])

    # WBOOT reconstructs the reclaimable CCP while leaving the protected PDS
    # intact. Model that exact memory ownership boundary with a fresh CCP image.
    rebuilt = cpu()
    machine.mem[BASE:history] = rebuilt.mem[BASE:history]
    call(machine, symbol("CCP_HINIT"))

    require(bytes(machine.mem[history:LAYOUT["SYSTEM"]]) == before,
            "CCP reconstruction changed protected command history")
    machine.a = 0
    call(machine, symbol("CCP_HGET"))
    length = machine.mem[count]
    require(bytes(machine.mem[data:data + length]) == command,
            "reconstructed CCP could not retrieve prior command history")
    print("CCP reconstruction preserved and retrieved command history")


if __name__ == "__main__":
    main()
