#!/usr/bin/env python3
"""Build the self-contained BetterCP/M source and native-tools disk.

The disk uses the MM 80-track, double-sided DATA layout: no reserved system
tracks, 2K allocation blocks, and a 128-entry directory.  All build tools and
sources reside in user zero.  SOURCES.DOC records the shortened or disambiguated
8.3 name assigned to every repository path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from build_montezuma_extended_790k import RAW_SIZE, build, verify


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/trs80"
BLOCK_SIZE = 2048
DIRECTORY_ENTRIES = 128
FIRST_DATA_BLOCK = 2
BLOCK_COUNT = RAW_SIZE // BLOCK_SIZE

TOOL_SEARCH = (
    Path("/Users/nathanael/projects/git/cpm-compatibility/suite/build-tools"),
    Path("/Users/nathanael/git/cpm-compatibility/suite/build-tools"),
)

def text_file(data: bytes) -> bytes:
    """Give a host text file the conventional CP/M text-file ending."""
    text = data.decode("ascii").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii") + b"\x1a"


def cpm_name(path: Path, used: set[str]) -> str:
    """Make a stable, unique 8.3 name within one CP/M user area."""
    suffix = path.suffix[1:].upper()
    suffix = {"MD": "DOC"}.get(suffix, suffix)[:3]
    stem = re.sub(r"[^A-Z0-9]", "", path.stem.upper()) or "SOURCE"
    candidate = f"{stem[:8]}.{suffix}" if suffix else stem[:8]
    if candidate not in used:
        used.add(candidate)
        return candidate
    for number in range(1, 100):
        short = (stem[:6] + f"{number:02d}")[:8]
        candidate = f"{short}.{suffix}" if suffix else short
        if candidate not in used:
            used.add(candidate)
            return candidate
    raise ValueError(f"cannot assign CP/M name to {path}")


def source_area(path: Path) -> tuple[int, str]:
    """Keep the native build environment together in ordinary user zero."""
    return 0, "SOURCE"


def install_files(files: list[tuple[int, str, bytes]]) -> bytes:
    """Create a flat CP/M DATA image and install files in 16K extents."""
    raw = bytearray([0xE5]) * RAW_SIZE
    next_entry = 0
    next_block = FIRST_DATA_BLOCK
    for user, filename, content in files:
        stem, _, suffix = filename.partition(".")
        records = (len(content) + 127) // 128
        padded = content.ljust(records * 128, b"\x1a")
        block_total = (len(padded) + BLOCK_SIZE - 1) // BLOCK_SIZE
        extent_total = max(1, (records + 127) // 128)
        content_at = 0
        for extent in range(extent_total):
            if next_entry >= DIRECTORY_ENTRIES:
                raise ValueError("build disk exceeds its 128-entry directory")
            entry = bytearray(32)
            entry[0] = user
            entry[1:9] = stem.ljust(8).encode("ascii")
            entry[9:12] = suffix.ljust(3).encode("ascii")
            entry[12] = extent & 0x1F
            entry[14] = extent >> 5
            entry[15] = min(128, max(0, records - extent * 128))
            blocks_here = min(8, block_total - extent * 8)
            for slot in range(blocks_here):
                if next_block >= BLOCK_COUNT:
                    raise ValueError("build disk exceeds its 800K data area")
                entry[16 + slot * 2:18 + slot * 2] = next_block.to_bytes(2, "little")
                chunk = padded[content_at:content_at + BLOCK_SIZE]
                start = next_block * BLOCK_SIZE
                raw[start:start + len(chunk)] = chunk
                next_block += 1
                content_at += len(chunk)
            start = next_entry * 32
            raw[start:start + 32] = entry
            next_entry += 1
    return bytes(raw)


def extract_files(raw: bytes) -> dict[tuple[int, str], bytes]:
    """Read back the directory; used as an independent build-time check."""
    extents: dict[tuple[int, str], list[tuple[int, int, bytes]]] = {}
    for offset in range(0, DIRECTORY_ENTRIES * 32, 32):
        entry = raw[offset:offset + 32]
        if entry[0] > 15:
            continue
        stem = entry[1:9].decode("ascii").rstrip()
        suffix = bytes(x & 0x7F for x in entry[9:12]).decode("ascii").rstrip()
        name = stem + ("." + suffix if suffix else "")
        number = entry[12] + 32 * entry[14]
        records = entry[15]
        payload = bytearray()
        for slot in range(8):
            block = int.from_bytes(entry[16 + slot * 2:18 + slot * 2], "little")
            if block:
                payload.extend(raw[block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE])
        extents.setdefault((entry[0], name), []).append((number, records, bytes(payload)))
    recovered = {}
    for key, parts in extents.items():
        content = bytearray()
        for _number, records, payload in sorted(parts):
            content.extend(payload[:records * 128])
        recovered[key] = bytes(content)
    return recovered


def find_tools(explicit: Path | None) -> Path:
    choices = (explicit,) if explicit else TOOL_SEARCH
    for directory in choices:
        if directory and (directory / "ZSM4.COM").is_file() and (directory / "LINK.COM").is_file():
            return directory
    raise SystemExit("ZSM4.COM and LINK.COM were not found; pass --tools DIRECTORY")


def build_docs(mapping: list[dict[str, object]], tools: Path) -> tuple[bytes, bytes]:
    areas = ["USER 0  ALL SOURCES, BUILD.DOC, SOURCES.DOC, ZSM4.COM, LINK.COM"]
    guide = """BETTERCP/M SOURCE AND NATIVE BUILD DISK

This is an MM 80T DS DATA disk: 800K, 512-byte sectors, 2K blocks,
128 directory entries, and no reserved system tracks.  It is intended as
drive B: beside a bootable BetterCP/M system disk in drive A:.

CONTENTS

{areas}

All files are in B0:.  SOURCES.DOC maps each short CP/M filename to its
repository path.

ASSEMBLING A TRANSIENT PROGRAM

  B0:
  B0:ZSM4 B:ERA=B:ERA
  B0:LINK B:ERA[A]

ZSM4 creates ERA.REL and LINK creates ERA.COM.  SOURCES.DOC maps every
shortened CP/M filename back to its repository path.  Several resident and
platform modules need generated link-symbol includes; use the repository
host build for these until the native GENSYS composer is implemented.

BUILDING THE OPERATING SYSTEM

The resident sources assemble the same way, but the linked pieces are not a
single ordinary COM file.  BetterCP/M's boot sector, stage-one loader, packed
resident image, reloader, control overlay, RSX manager, and relocatable CCP
must be placed at defined offsets in a 20K protected-system image.

At present the repository's host build performs that composition:

  python3 tools/build_complete_system.py

It writes build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk.  The current
SYSGEN.COM then installs by copying and verifying that complete protected
area from the running A: system disk to a prepared compatible system disk.
It does not yet consume separately assembled REL files or a SYSTEM.IMG file.

Therefore a completely native source-to-system-track build still needs one
additional program: a GENSYS-style composer, followed by a SYSGEN mode that
reads the composed image and writes it to the system tracks.  Until that is
implemented, native assembly on this disk is useful for development and
binary comparison, while final system composition is done by the host build.

INSTALLING AN EXISTING BUILT SYSTEM

  1. Boot the BetterCP/M system disk in A:.
  2. Use DUP to format a compatible SYSTEM disk in the target drive.
  3. Run SYSGEN and select that target.  SYSGEN copies all 20K of protected
     boot/system content, verifies it, and leaves the CP/M filesystem intact.

NATIVE TOOL IDENTIFICATION

ZSM4.COM SHA256:
  {zsm4}
LINK.COM SHA256:
  {link}
""".format(
        areas="\n".join(areas),
        zsm4=hashlib.sha256((tools / "ZSM4.COM").read_bytes()).hexdigest(),
        link=hashlib.sha256((tools / "LINK.COM").read_bytes()).hexdigest(),
    )
    manifest = ["BETTERCP/M SOURCE FILE MAP", "", "CP/M NAME    SOURCE PATH", ""]
    for item in sorted(mapping, key=lambda row: (int(row["user"]), str(row["name"]))):
        manifest.append(f"{int(item['user']):2}:{str(item['name']):12} {item['source']}")
    return text_file(guide.encode("ascii")), text_file(("\n".join(manifest) + "\n").encode("ascii"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", type=Path, help="directory containing ZSM4.COM and LINK.COM")
    parser.add_argument("--output", type=Path,
                        default=OUT / "BetterCPM-Build-80T-DS-800K.dmk")
    args = parser.parse_args()
    tools = find_tools(args.tools)

    files: list[tuple[int, str, bytes]] = []
    mapping: list[dict[str, object]] = []
    used: dict[int, set[str]] = {user: set() for user in range(16)}
    for source in sorted((ROOT / "src").rglob("*")):
        if not source.is_file():
            continue
        user, label = source_area(source)
        name = cpm_name(source, used[user])
        content = text_file(source.read_bytes())
        files.append((user, name, content))
        mapping.append({"user": user, "area": label, "name": name,
                        "source": str(source.relative_to(ROOT))})

    for name in ("ZSM4.COM", "LINK.COM"):
        used[0].add(name)
        files.append((0, name, (tools / name).read_bytes()))
    license_path = tools / "zsm4-source/LICENSE"
    if license_path.is_file():
        files.append((0, "ZSM4.LIC", text_file(license_path.read_bytes())))
        used[0].add("ZSM4.LIC")

    build_doc, sources_doc = build_docs(mapping, tools)
    files.extend(((0, "BUILD.DOC", build_doc), (0, "SOURCES.DOC", sources_doc)))
    raw = install_files(files)
    recovered = extract_files(raw)
    for user, name, content in files:
        actual = recovered.get((user, name))
        if actual is None or not actual.startswith(content):
            raise SystemExit(f"read-back failed for {user}:{name}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build(raw))
    verify(args.output.read_bytes(), require_blank=False)
    flat = args.output.with_suffix(".img")
    flat.write_bytes(raw)
    diskdefs = args.output.with_name("diskdefs-build")
    diskdefs.write_text("""diskdef bettercpm-build\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n""")
    report = {
        "format": "MM 80T DS DATA 800K",
        "dmk": args.output.name,
        "flat": flat.name,
        "sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "files": len(files),
        "directory_entries_used": sum(max(1, ((len(data) + 127) // 128 + 127) // 128)
                                      for _user, _name, data in files),
        "allocation_blocks_used": FIRST_DATA_BLOCK + sum(
            (((len(data) + 127) // 128) * 128 + BLOCK_SIZE - 1) // BLOCK_SIZE
            for _user, _name, data in files),
        "source_map": mapping,
    }
    args.output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"created {args.output} ({report['files']} files, "
          f"{report['directory_entries_used']}/{DIRECTORY_ENTRIES} directory entries, "
          f"{report['allocation_blocks_used']}/{BLOCK_COUNT} blocks)")
    print(f"{report['sha256']}  {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
