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

    entry = build(args.assembler, "r3entry", "r3entry.mac", "RVBASE", rsx)
    entry_source = (ROOT / "src/system/r3entry.mac").read_text(encoding="ascii")
    helper = entry_source[entry_source.index("RI_ENTRY:"):entry_source.index("RI_END:")]
    io = assemble(args.assembler, "        INCLUDE layout.inc\n        ASEG\n        ORG 0\n" + helper + "        END\n",
                  BUILD / "rsxio.bin", BUILD / "rsxio.lst", 0)
    if len(io) > 256 or len(entry) > 1012:
        raise ValueError("transaction entry exceeds its execution slot")

    plan = build(args.assembler, "r3plan", "rsxplan.mac", "RPBASE", cfg)
    slots = build(args.assembler, "r3slots", "rsxslots.mac", "SUBASE", cfg)
    snapshot = build(args.assembler, "r3snapshot", "r3snap.mac", "RNBASE", cfg)
    carrier = build(args.assembler, "r3carrier", "r3carr.mac", "RXBASE", cfg)
    metadata = build(args.assembler, "r3metadata", "r3meta.mac", "RMBASE", cfg)
    coordinator = build(args.assembler, "r3coord", "r3coord.mac", "RCBASE", rsx)
    profile = build(args.assembler, "r3profile", "r3prof.mac", "PFBASE", rsx)
    retained_context = build(args.assembler, "r3kctx", "r3kctx.mac", "KCBASE", rsx)
    retained = build(args.assembler, "r3keep", "r3keep.mac", "KEBASE", rsx)
    retained_prepare = build(args.assembler, "r3kpre", "r3kpre.mac", "KPBASE", rsx)
    finalizer = build(args.assembler, "r3final", "r3final.mac", "RFBASE", rsx)
    removal = build(args.assembler, "r3drop", "r3drop.mac", "RDBASE", rsx)
    mover = build(args.assembler, "r3mover", "rsxmover.mac", "RMBASE", cfg)
    schedule = build(args.assembler, "r3sched", "rsxsched.mac", "RSBASE", cfg + 0x120)
    handoff = build(args.assembler, "r3ovload", "r3ovload.mac", "ROBASE", cfg + 0x310)
    persistent = build(args.assembler, "r3persist", "r3pst.mac", "RTBASE", cfg + 0x38F)
    commit = build(args.assembler, "r3commit", "r3comit.mac", "RCBASE", rsx)
    resolver = (BUILD / "rsxresolver.bin").read_bytes()

    for label, data in (("planner", plan), ("slot preparer", slots),
                        ("snapshot constructor", snapshot),
                        ("carrier preparer", carrier),
                        ("metadata preparer", metadata)):
        if len(data) > 1024:
            raise ValueError(f"{label} exceeds the shared overlay: {len(data)}")
    regions = ((0, mover, "mover"), (0x120, schedule, "scheduler"),
               (0x310, handoff, "handoff"),
               (0x38F, persistent, "persistent publisher"))
    image = bytearray(1024)
    end = 0
    for offset, data, label in regions:
        if offset < end or offset + len(data) > len(image):
            raise ValueError(f"{label} overlaps the move overlay")
        image[offset:offset + len(data)] = data
        end = offset + len(data)
    if len(coordinator) > 1012:
        raise ValueError("carrier coordinator exceeds gateway-safe slot: "
                         f"{len(coordinator)}")
    if len(profile) > 1012:
        raise ValueError("profile builder exceeds gateway-safe slot: "
                         f"{len(profile)}")
    if len(retained_context) > 1012:
        raise ValueError("retained context constructor exceeds gateway-safe slot: "
                         f"{len(retained_context)}")
    if len(retained) > 1012:
        raise ValueError("retained carrier loader exceeds gateway-safe slot: "
                         f"{len(retained)}")
    if len(retained_prepare) > 1012:
        raise ValueError("retained preparer exceeds gateway-safe slot: "
                         f"{len(retained_prepare)}")
    if len(finalizer) > 1012:
        raise ValueError("transaction finalizer exceeds gateway-safe slot: "
                         f"{len(finalizer)}")
    if len(removal) > 1012:
        raise ValueError("removal coordinator exceeds gateway-safe slot: "
                         f"{len(removal)}")
    if len(commit) > 1012:
        raise ValueError(f"commit overlay exceeds gateway-safe slot: {len(commit)}")
    if len(resolver) > 1012:
        raise ValueError("resolver exceeds gateway-safe slot: "
                         f"{len(resolver)}")
    gateway = bytes((0xC3, LAYOUT["BDOS"] & 0xFF, LAYOUT["BDOS"] >> 8))
    outputs = {
        "R3ENTRY.RSX": entry.ljust(1021, b"\0") + gateway,
        "R3PLAN.RSX": plan.ljust(1024, b"\0"),
        "R3SLOTS.RSX": slots.ljust(1024, b"\0"),
        "R3SNAP.RSX": snapshot.ljust(1024, b"\0"),
        "R3CARR.RSX": carrier.ljust(1024, b"\0"),
        "R3META.RSX": metadata.ljust(1024, b"\0"),
        "R3COORD.RSX": coordinator.ljust(1021, b"\0") + gateway,
        "R3PROF.RSX": profile.ljust(1021, b"\0") + gateway,
        "R3KCTX.RSX": retained_context.ljust(1021, b"\0") + gateway,
        "R3KEEP.RSX": retained.ljust(1021, b"\0") + gateway,
        "R3KPRE.RSX": retained_prepare.ljust(1021, b"\0") + gateway,
        "R3FINAL.RSX": finalizer.ljust(1021, b"\0") + gateway,
        "R3DROP.RSX": removal.ljust(1021, b"\0") + gateway,
        "R3MOVE.RSX": bytes(image),
        "R3COMIT.RSX": commit.ljust(1021, b"\0") + gateway,
        "R3RESOL.RSX": resolver.ljust(1021, b"\0") + gateway,
    }
    for name, data in outputs.items():
        (BUILD / name).write_bytes(data)
        print(f"{name}: {len(data)} bytes")


if __name__ == "__main__":
    main()
