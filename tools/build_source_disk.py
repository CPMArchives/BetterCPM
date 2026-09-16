#!/usr/bin/env python3
"""Build BetterCP/M's native build disk and complete-source companion.

Both disks use the MM 80-track, double-sided DATA layout: no reserved system
tracks, 2K allocation blocks, and a 128-entry directory. All files reside in
user zero. SOURCES.DOC records the shortened or disambiguated 8.3 names.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from build_montezuma_extended_790k import RAW_SIZE, build, verify


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/trs80"
BLOCK_SIZE = 2048
DIRECTORY_ENTRIES = 128
FIRST_DATA_BLOCK = 2
BLOCK_COUNT = RAW_SIZE // BLOCK_SIZE
MM_800K_SKEW = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)


def z80pack_raw(logical: bytes) -> bytes:
    """Place logical MM sectors into z80pack's physical image slots."""
    sector_size = 512
    track_size = len(MM_800K_SKEW) * sector_size
    if len(logical) % track_size:
        raise ValueError("MM image is not an integral number of tracks")
    physical = bytearray(len(logical))
    for base in range(0, len(logical), track_size):
        for logical_sector, physical_slot in enumerate(MM_800K_SKEW):
            source = base + logical_sector * sector_size
            target = base + physical_slot * sector_size
            physical[target:target + sector_size] = logical[source:source + sector_size]
    return bytes(physical)


def z80pack_logical(physical: bytes) -> bytes:
    """Undo z80pack_raw for qualification and host-side inspection."""
    sector_size = 512
    track_size = len(MM_800K_SKEW) * sector_size
    if len(physical) % track_size:
        raise ValueError("MM image is not an integral number of tracks")
    logical = bytearray(len(physical))
    for base in range(0, len(physical), track_size):
        for logical_sector, physical_slot in enumerate(MM_800K_SKEW):
            source = base + physical_slot * sector_size
            target = base + logical_sector * sector_size
            logical[target:target + sector_size] = physical[source:source + sector_size]
    return bytes(logical)

BUILD_SOURCES = (
    ("BOOT.MAC", "src/platform/trs80m4/boot.mac"),
    ("STAGE1.MAC", "src/platform/trs80m4/stage1.mac"),
    ("GATEWAY.MAC", "src/system/gateway.mac"),
    ("BDOS.MAC", "src/bdos/unified.mac"),
    ("EXTENS.MAC", "src/system/extensions.mac"),
    ("DISK.MAC", "src/bios/disk.mac"),
    ("BIOS.MAC", "src/bios/bios.mac"),
    ("FILELOAD.MAC", "src/system/fileloader.mac"),
    ("TABLES.MAC", "src/bios/tables.mac"),
    ("CCPRELOD.MAC", "src/platform/trs80m4/commandreload.mac"),
    ("RSXSEL.MAC", "src/platform/trs80m4/rsxselect.mac"),
    ("CONFIG.MAC", "src/bios/config.mac"),
    ("RSXLOAD.MAC", "src/system/rsxloader.mac"),
    ("RSXVALID.MAC", "src/system/rsxvalidator.mac"),
    ("RSXPUBL.MAC", "src/system/rsxpublish.mac"),
    ("RSXRESOL.MAC", "src/system/rsxresolver.mac"),
    ("CCP.MAC", "src/ccp/ccp.mac"),
    ("CCPALT.MAC", "src/ccp/ccp.mac"),
    ("CCPCHK.MAC", "src/ccp/ccp.mac"),
)

BUILD_INCLUDES = (
    ("LAYOUT.INC", "src/system/layout.inc"),
    ("HARDWARE.INC", "src/platform/trs80m4/hardware.inc"),
    ("M4DISK.INC", "src/platform/trs80m4/m4disk.inc"),
    ("BIOSPLAT.INC", "src/bios/biosplat.inc"),
    ("M4CONS.INC", "src/platform/trs80m4/m4cons.inc"),
    ("M4SCROLL.INC", "src/platform/trs80m4/m4scroll.inc"),
    ("RELOAD.INC", "src/platform/trs80m4/reload.inc"),
    ("VERSIONS.INC", "src/bdos/versions.inc"),
    ("CORE.INC", "build/system/core.inc"),
    ("BIOSLINK.INC", "build/system/bioslink.inc"),
    ("DISKLINK.INC", "build/system/disklink.inc"),
    ("CPXLINK.INC", "build/system/cpxlink.inc"),
)

TOOL_SEARCH = (
    Path("/Users/nathanael/projects/git/cpm-compatibility/suite/build-tools"),
    Path("/Users/nathanael/git/cpm-compatibility/suite/build-tools"),
)

def text_file(data: bytes) -> bytes:
    """Give a host text file the conventional CP/M text-file ending."""
    text = data.decode("ascii").replace("\r\n", "\n").replace("\r", "\n")
    return text.replace("\n", "\r\n").encode("ascii") + b"\x1a"


def build_source(data: bytes, name: str) -> bytes:
    """Rewrite host-only include stems to canonical CP/M 8.3 names."""
    text = data.decode("ascii")
    for host, native in (("bioslinks.inc", "bioslink.inc"),
                         ("disklinks.inc", "disklink.inc"),
                         ("cpxlinks.inc", "cpxlink.inc")):
        text = text.replace(host, native)
    if name == "CCPALT.MAC":
        text = text.replace("CCPBASE         EQU     0BB00H",
                            "CCPBASE         EQU     0BC01H")
    elif name == "CCPCHK.MAC":
        text = text.replace("CCPBASE         EQU     0BB00H",
                            "CCPBASE         EQU     0BD37H")
    return text_file(text.encode("ascii"))


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
    areas = ["USER 0  BUILD SOURCES, BUILD.SUB, DOCS, ZSM4, LINK, BUILD TOOLS"]
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
shortened CP/M filename back to its repository path.

BUILDING THE OPERATING SYSTEM

BUILD.SUB, the canonical 8.3 source names, and the generated link-symbol
includes form one coherent build snapshot. Run the complete native build in
user zero:

  A0:SUBMIT B:BUILD

BUILD.SUB selects B:, assembles and links every component. RESPACK constructs the packed
RESIDENT.BIN payload, then SYSBUILD creates and read-back verifies the
161-record SYSTEM.SYS package. Use SYSGEN SYSTEM.SYS C: to install and verify
it on a prepared SYSTEM disk. SYSGEN A: C: instead obtains the package from
an already bootable source disk.

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
    subprocess.run([sys.executable, str(ROOT / "tools/build_complete_system.py")],
                   cwd=ROOT, check=True)

    files: list[tuple[int, str, bytes]] = []
    mapping: list[dict[str, object]] = []
    used: dict[int, set[str]] = {user: set() for user in range(16)}
    for name, relative in BUILD_SOURCES:
        source = ROOT / relative
        used[0].add(name)
        files.append((0, name, build_source(source.read_bytes(), name)))
        mapping.append({"user": 0, "area": "NATIVE BUILD", "name": name,
                        "source": relative})
    for name, relative in BUILD_INCLUDES:
        source = ROOT / relative
        used[0].add(name)
        files.append((0, name, text_file(source.read_bytes())))
        mapping.append({"user": 0, "area": "NATIVE BUILD", "name": name,
                        "source": relative})
    build_sub = ROOT / "src/utilities/system-build.sub"
    used[0].add("BUILD.SUB")
    files.append((0, "BUILD.SUB", text_file(build_sub.read_bytes())))
    mapping.append({"user": 0, "area": "NATIVE BUILD", "name": "BUILD.SUB",
                    "source": str(build_sub.relative_to(ROOT))})
    for name in ("ZSM4.COM", "LINK.COM"):
        used[0].add(name)
        files.append((0, name, (tools / name).read_bytes()))
    for name in ("SUBMIT.COM", "SYSBUILD.COM", "SYSGEN.COM", "RESPACK.COM",
                 "RLMBUILD.COM"):
        used[0].add(name)
        files.append((0, name, (ROOT / "build/utilities" / name).read_bytes()))
    used[0].add("BATCHIO.RSX")
    files.append((0, "BATCHIO.RSX", (ROOT / "build/rsx/BATCHIO.RSX").read_bytes()))
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
    z80pack = args.output.with_suffix(".dsk")
    z80pack.write_bytes(z80pack_raw(raw))
    diskdefs = args.output.with_name("diskdefs-build")
    diskdefs.write_text("""diskdef bettercpm-build\n seclen 512\n tracks 160\n sectrk 10\n blocksize 2048\n maxdir 128\n skew 1\n boottrk 0\n os 2.2\nend\n""")
    report = {
        "format": "MM 80T DS DATA 800K",
        "dmk": args.output.name,
        "flat": flat.name,
        "z80pack": z80pack.name,
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

    # The complete and growing source tree no longer shares an 800K disk with
    # the native toolchain. Preserve it on a companion image with the same
    # physical/data format and a complete 8.3 path map.
    archive_files: list[tuple[int, str, bytes]] = []
    archive_map: list[dict[str, object]] = []
    archive_used: set[str] = {"README.DOC", "SOURCES.DOC"}
    for source in sorted((ROOT / "src").rglob("*")):
        if not source.is_file() or source.name.startswith("."):
            continue
        name = cpm_name(source, archive_used)
        archive_files.append((0, name, text_file(source.read_bytes())))
        archive_map.append({"user": 0, "area": "SOURCE", "name": name,
                            "source": str(source.relative_to(ROOT))})
    archive_doc = ["BETTERCP/M COMPLETE SOURCE DISK", "",
                   "This companion disk preserves the complete src/ tree.",
                   "Use the build disk, BUILD.SUB and its canonical source",
                   "names to build SYSTEM.SYS. SOURCES.DOC maps this archive.", ""]
    archive_manifest = ["BETTERCP/M SOURCE FILE MAP", "", "CP/M NAME    SOURCE PATH", ""]
    archive_manifest.extend(f" 0:{item['name']:12} {item['source']}"
                            for item in sorted(archive_map, key=lambda row: str(row["name"])))
    archive_files.extend(((0, "README.DOC", text_file(("\n".join(archive_doc) + "\n").encode("ascii"))),
                          (0, "SOURCES.DOC", text_file(("\n".join(archive_manifest) + "\n").encode("ascii")))))
    archive_raw = install_files(archive_files)
    archive_output = args.output.with_name("BetterCPM-Sources-80T-DS-800K.dmk")
    archive_output.write_bytes(build(archive_raw))
    verify(archive_output.read_bytes(), require_blank=False)
    archive_output.with_suffix(".img").write_bytes(archive_raw)
    archive_output.with_suffix(".dsk").write_bytes(z80pack_raw(archive_raw))
    print(f"created {archive_output} ({len(archive_files)} files)")


if __name__ == "__main__":
    main()
