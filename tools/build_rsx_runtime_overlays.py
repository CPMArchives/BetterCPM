#!/usr/bin/env python3
"""Build file-backed Stage-3 overlays without enlarging reserved tracks."""
from __future__ import annotations

import argparse
from pathlib import Path

from build_ccp import assemble
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build/system"


def source(name: str, symbol: str, address: int) -> str:
    text = (ROOT / "src/system" / name).read_text(encoding="ascii")
    start = next(line for line in text.splitlines() if line.startswith(symbol))
    text = text.replace(start, f"{symbol:<16}EQU     0{address:04X}H")
    return expand_layout(text).replace(
        "        CSEG\n        .PHASE  ", "        ASEG\n        ORG     ").replace(
            "        .DEPHASE\n", "")


def build(assembler: Path, stem: str, name: str, symbol: str, address: int) -> bytes:
    output = BUILD / f"{stem}.bin"
    data = assemble(assembler, source(name, symbol, address), output,
                    output.with_suffix(".lst"), address)
    if not data:
        raise ValueError(f"empty {stem} overlay")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    cfg = LAYOUT["CONFIG"]
    rsx = LAYOUT["RSX"]

    plan = build(args.assembler, "r3plan", "rsxplan.mac", "RPBASE", cfg)
    slots = build(args.assembler, "r3slots", "rsxslots.mac", "SUBASE", cfg)
    mover = build(args.assembler, "r3mover", "rsxmover.mac", "RMBASE", cfg)
    schedule = build(args.assembler, "r3sched", "rsxschedule.mac", "RSBASE", cfg + 0x120)
    handoff = build(args.assembler, "r3ovload", "rsxovload.mac", "ROBASE", cfg + 0x320)
    commit = build(args.assembler, "r3commit", "rsxcommit.mac", "RCBASE", rsx)

    for label, data in (("planner", plan), ("slot preparer", slots)):
        if len(data) > 1024:
            raise ValueError(f"{label} exceeds the shared overlay: {len(data)}")
    regions = ((0, mover, "mover"), (0x120, schedule, "scheduler"),
               (0x320, handoff, "handoff"))
    image = bytearray(1024)
    end = 0
    for offset, data, label in regions:
        if offset < end or offset + len(data) > len(image):
            raise ValueError(f"{label} overlaps the move overlay")
        image[offset:offset + len(data)] = data
        end = offset + len(data)
    if len(commit) > 1021:
        raise ValueError(f"commit overlay exceeds gateway-safe slot: {len(commit)}")
    gateway = bytes((0xC3, LAYOUT["BDOS"] & 0xFF, LAYOUT["BDOS"] >> 8))
    outputs = {
        "R3PLAN.RSX": plan,
        "R3SLOTS.RSX": slots,
        "R3MOVE.RSX": bytes(image),
        "R3COMIT.RSX": commit.ljust(1021, b"\0") + gateway,
    }
    for name, data in outputs.items():
        (BUILD / name).write_bytes(data)
        print(f"{name}: {len(data)} bytes")


if __name__ == "__main__":
    main()
