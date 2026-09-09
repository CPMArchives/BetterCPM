#!/usr/bin/env python3
"""Cross-assemble the initial resident BetterCP/M CCP."""
from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path
from system_layout import LAYOUT, expand_layout

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ccp/ccp.mac"
BUILD = ROOT / "build/ccp"
LINK_BASE = 0xBB00
ALTERNATE_BASE = 0xBC01
CHECK_BASE = 0xBD37
# The original one-sector relocation directory was sufficient for the small
# bring-up CCP.  The finalized resident monitor needs a second sector; the
# carrier records its header length so old one-sector modules remain legible.
MODULE_HEADER_SIZE = 1024
DEFAULT_GATEWAY = LAYOUT["TPA"]


def assemble(assembler: Path, text: str, output: Path, listing: Path,
             origin: int) -> bytes:
    with tempfile.TemporaryDirectory(prefix="bettercpm-ccp-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(expand_layout(text), encoding="ascii")
        subprocess.run([str(assembler), "-fb", f"-o{output}",
                        f"-l{listing}", staged.name], check=True,
                       cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > origin and data[:origin] == bytes(origin):
        data = data[origin:]
        output.write_bytes(data)
    return data


def relocation_offsets(linked: bytes,
                       alternates: list[tuple[bytes, int]]) -> list[int]:
    if any(len(linked) != len(image) for image, _origin in alternates):
        raise SystemExit("CCP alternate-origin size changed")
    changed = {
        index
        for image, _origin in alternates
        for index, pair in enumerate(zip(linked, image))
        if pair[0] != pair[1]
    }
    candidates = []
    for offset in range(len(linked) - 1):
        old = int.from_bytes(linked[offset:offset + 2], "little")
        covered = changed.intersection((offset, offset + 1))
        if covered and all(
            (old + origin - LINK_BASE) & 0xFFFF ==
            int.from_bytes(image[offset:offset + 2], "little")
            for image, origin in alternates
        ):
            candidates.append((offset, covered))
    selected = []
    uncovered = set(changed)
    while uncovered:
        useful = [(len(covered & uncovered), offset, covered)
                  for offset, covered in candidates if covered & uncovered]
        if not useful:
            raise SystemExit(f"unexplained CCP relocation bytes: {sorted(uncovered)}")
        _score, offset, covered = max(useful)
        selected.append(offset)
        uncovered -= covered
    selected.sort()
    for alternate, origin in alternates:
        relocated = bytearray(linked)
        delta = origin - LINK_BASE
        for offset in selected:
            value = int.from_bytes(relocated[offset:offset + 2], "little")
            relocated[offset:offset + 2] = (
                (value + delta) & 0xFFFF).to_bytes(2, "little")
        if bytes(relocated) != alternate:
            raise SystemExit(
                "generated CCP relocation table does not reproduce alternate image")
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--assembler", type=Path,
                        default=Path("/Users/nathanael/bin/z80asm"))
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    source = SOURCE.read_text(encoding="ascii")
    text = source.replace("        CSEG\n        .PHASE  ",
                          "        ASEG\n        ORG     ")
    text = text.replace("        .DEPHASE\n", "")
    output = BUILD / "ccp.bin"
    data = assemble(args.assembler, text, output, BUILD / "ccp.lst", LINK_BASE)
    if not data:
        raise SystemExit("empty CCP image")
    allocation_size = (len(data) + 0xFF) & ~0xFF
    if allocation_size > LINK_BASE - 0x0100:
        raise SystemExit(f"CCP cannot fit above the 0100h transient origin: {len(data)} bytes")

    alternate_text = text.replace("CCPBASE         EQU     0BB00H",
                                  "CCPBASE         EQU     0BC01H")
    alternate = assemble(args.assembler, alternate_text,
                         BUILD / "ccp-alt.bin", BUILD / "ccp-alt.lst",
                         ALTERNATE_BASE)
    check_text = text.replace("CCPBASE         EQU     0BB00H",
                              "CCPBASE         EQU     0BD37H")
    check = assemble(args.assembler, check_text,
                     BUILD / "ccp-check.bin", BUILD / "ccp-check.lst",
                     CHECK_BASE)
    offsets = relocation_offsets(
        data, [(alternate, ALTERNATE_BASE), (check, CHECK_BASE)])
    if len(offsets) > (MODULE_HEADER_SIZE - 16) // 2:
        raise SystemExit("CCP relocation directory exceeds its header")
    header = bytearray(MODULE_HEADER_SIZE)
    header[:16] = struct.pack("<4sBBHHHHH", b"BCM1", 1, 2, LINK_BASE,
                              len(data), allocation_size, 0, len(offsets))
    for index, offset in enumerate(offsets):
        struct.pack_into("<H", header, 16 + index * 2, offset)
    module = BUILD / "ccp.rlm"
    module.write_bytes(header + data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"CCP bytes: {len(data)}")
    print(f"CCP allocation: {allocation_size} bytes; calculated base: "
          f"{DEFAULT_GATEWAY - allocation_size:04X}h")
    print(f"CCP relocations: {len(offsets)}; module bytes: {module.stat().st_size}")


if __name__ == "__main__":
    main()
