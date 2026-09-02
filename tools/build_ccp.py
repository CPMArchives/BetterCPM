#!/usr/bin/env python3
"""Cross-assemble the initial resident BetterCP/M CCP."""
from __future__ import annotations

import argparse
import hashlib
import struct
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/ccp/ccp.mac"
BUILD = ROOT / "build/ccp"
LINK_BASE = 0xBB00
ALTERNATE_BASE = 0xBC01
ALLOCATION_SIZE = 0x0500
MODULE_HEADER_SIZE = 512


def assemble(assembler: Path, text: str, output: Path, listing: Path,
             origin: int) -> bytes:
    with tempfile.TemporaryDirectory(prefix="bettercpm-ccp-") as temporary:
        staged = Path(temporary) / SOURCE.name
        staged.write_text(text, encoding="ascii")
        subprocess.run([str(assembler), "-fb", f"-o{output}",
                        f"-l{listing}", staged.name], check=True,
                       cwd=staged.parent)
    data = output.read_bytes()
    if len(data) > origin and data[:origin] == bytes(origin):
        data = data[origin:]
        output.write_bytes(data)
    return data


def relocation_offsets(linked: bytes, alternate: bytes) -> list[int]:
    if len(linked) != len(alternate):
        raise SystemExit("CCP alternate-origin size changed")
    delta = ALTERNATE_BASE - LINK_BASE
    changed = {index for index, pair in enumerate(zip(linked, alternate))
               if pair[0] != pair[1]}
    candidates = []
    for offset in range(len(linked) - 1):
        old = int.from_bytes(linked[offset:offset + 2], "little")
        new = int.from_bytes(alternate[offset:offset + 2], "little")
        covered = changed.intersection((offset, offset + 1))
        if covered and (old + delta) & 0xFFFF == new:
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
    relocated = bytearray(linked)
    for offset in selected:
        value = int.from_bytes(relocated[offset:offset + 2], "little")
        relocated[offset:offset + 2] = ((value + delta) & 0xFFFF).to_bytes(2, "little")
    if bytes(relocated) != alternate:
        raise SystemExit("generated CCP relocation table does not reproduce alternate image")
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
    if not data or len(data) > 0x500:
        raise SystemExit(f"CCP size outside BB00h..BFFFh: {len(data)} bytes")

    alternate_text = text.replace("CCPBASE         EQU     0BB00H",
                                  "CCPBASE         EQU     0BC01H")
    alternate = assemble(args.assembler, alternate_text,
                         BUILD / "ccp-alt.bin", BUILD / "ccp-alt.lst",
                         ALTERNATE_BASE)
    offsets = relocation_offsets(data, alternate)
    if len(offsets) > (MODULE_HEADER_SIZE - 16) // 2:
        raise SystemExit("CCP relocation directory exceeds one sector")
    header = bytearray(MODULE_HEADER_SIZE)
    header[:16] = struct.pack("<4sBBHHHHH", b"BCM1", 1, 1, LINK_BASE,
                              len(data), ALLOCATION_SIZE, 0, len(offsets))
    for index, offset in enumerate(offsets):
        struct.pack_into("<H", header, 16 + index * 2, offset)
    module = BUILD / "ccp.rlm"
    module.write_bytes(header + data)
    print(f"{hashlib.sha256(data).hexdigest()}  {output.relative_to(ROOT)}")
    print(f"CCP bytes: {len(data)}")
    print(f"CCP relocations: {len(offsets)}; module bytes: {module.stat().st_size}")


if __name__ == "__main__":
    main()
