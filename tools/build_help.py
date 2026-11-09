#!/usr/bin/env python3
"""Assemble the first HELP reader and package its editable Markdown subjects."""
import argparse
import binascii
import re
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from build_profiles import PROFILES, profile_inputs
from component_build import recorded_build
from utility_help import query_source
from utility_versions import banner, strings

ROOT = Path(__file__).resolve().parents[1]
UTILITY = ROOT / "src/utilities"
SUBJECTS = ROOT / "src/help"
OUTPUT = ROOT / "build/help"


def help_library(subjects):
    """Write LUDEF directory entries and CRCs over CP/M records."""
    items = sorted(subjects.glob("*.HLP"))
    if not items:
        raise ValueError(f"No help sources in {subjects}")
    directory_records = (len(items) + 4) // 4
    directory = bytearray((b"\xff" + bytes(31)) * (4 * directory_records))
    payload = bytearray()

    def entry(slot, name, start, count, crc, pad):
        struct.pack_into("<B11sHHH8xB5x", directory, 32 * slot,
                         0, name, start, count, crc, pad)

    entry(0, b" " * 11, 0, directory_records, 0, 0)
    for slot, item in enumerate(items, 1):
        if not re.fullmatch(r"[A-Z0-9_]{1,8}", item.stem):
            raise ValueError(f"Invalid topic name {item.name}")
        text = item.read_text(encoding="ascii").replace("\n", "\r\n").encode("ascii") + b"\x1a"
        pad = (-len(text)) % 128
        block = text + b"\x1a" * pad
        entry(slot, item.stem.encode().ljust(8) + b"HLP",
              directory_records + len(payload) // 128, len(block) // 128,
              binascii.crc_hqx(block, 0), pad)
        payload.extend(block)
    struct.pack_into("<H", directory, 16, binascii.crc_hqx(directory, 0))
    return directory + payload


@recorded_build("utility:HELP")
def assemble_reader(assembler, output):
    # PATH's protected layout differs across shipped kernels. Match WBOOT and
    # the same version/capability descriptor as PATH.COM before reading it.
    layouts = set()
    for profile in PROFILES.values():
        manifest, _, _ = profile_inputs(profile, ROOT / "src/system/layout.inc")
        sym = manifest["symbols"]
        layouts.add((sym["LY_BIOS"] + 3, sym["LY_SYS"] + 0x80, sym["LY_EXT"] - 16))
    table = "\n".join(" DW " + ",".join(str(n) for n in row) for row in sorted(layouts))
    query = (UTILITY / "common/version.inc").read_text().split("\nUV_QUERY:", 1)[1]
    replacements = {"queries.inc": query_source(ROOT) + "\nUV_QUERY:" + query,
                    "help-identity.inc": strings("HELP", label="help_version"),
                    "help-title.inc": f"help_usage: DB '{banner('HELP')}',13,10\n",
                    "help-layouts.inc": table + "\n DW 0\n"}
    paths = (UTILITY / "help", UTILITY / "common", ROOT / "src/archive", ROOT / "src/codec")

    def expand(text):
        def include(match):
            name = match[1]
            if name in replacements:
                return replacements[name].rstrip()
            file = next(p / name for p in paths if (p / name).is_file())
            return expand(file.read_text(encoding="ascii")).rstrip()
        return re.sub(r"(?im)^[ \t]*include\s+([\w.-]+)[ \t]*$", include, text)

    source = expand((UTILITY / "help.mac").read_text(encoding="ascii"))
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "help.mac"
        path.write_text(source, encoding="ascii")
        raw = path.with_suffix(".bin")
        subprocess.run([str(assembler), "-e32", "-sn", "-fb", f"-o{raw}",
                        f"-l{output}/help.lst", path.name], cwd=tmp, check=True)
        data = raw.read_bytes()
    # The assembler emits trailing DS storage. Startup clears this region;
    # it costs TPA but need not occupy disk records or loader read time.
    listing = (output / "help.lst").read_text()
    match = re.search(r"^([0-9a-f]{4})\s+\d+\s+\d+\s+bss:$", listing, re.M | re.I)
    if not match or data[:1] != bytes([0xc3]):
        raise ValueError("Unexpected HELP entry or workspace layout")
    size = int(match[1], 16) - 0x100
    if not 0 < size <= len(data) or any(byte != 0xff for byte in data[size:]):
        raise ValueError("Initialized HELP data lies beyond its workspace boundary")
    image = data[:size]
    (output / "HELP.COM").write_bytes(image)
    return image


def data_disks(output):
    from build_montezuma_extended_790k import RAW_SIZE, build as model4_image
    from build_trs80_boot import install_files
    from build_z80pack_image import DEFAULT_FORMAT, disk_definition
    from fdf_format import select_fdf
    from model2_media import image as model2_image
    fmt = select_fdf(ROOT / "metadata/DISK.FDF", DEFAULT_FORMAT)
    files = [(name, (output / name).read_bytes()) for name in ("HELP.COM", "HELP.LBR")]
    with tempfile.TemporaryDirectory(dir=output) as tmp:
        work = Path(tmp)
        (work / "diskdefs").write_text(disk_definition(fmt))
        disk = work / "BetterCPM-1.2-HELP.dsk"
        disk.write_bytes(bytes([0xe5]) * fmt.image_bytes)
        for name, _ in files:
            subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                            str(disk), str(output / name), "0:" + name], cwd=work, check=True)
        disk.replace(output / disk.name)
    raw = bytearray([0xe5]) * RAW_SIZE
    install_files(raw, files)
    (output / "BetterCPM-1.2-HELP.dmk").write_bytes(model4_image(raw))
    (output / "BetterCPM-1.2-HELP.imd").write_bytes(model2_image(bytes(160 * 128), files, bootable=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", default=shutil.which("z80asm") or str(Path.home() / "bin/z80asm"))
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--subjects", type=Path, default=SUBJECTS)
    parser.add_argument("--disk", action="store_true", help="also build cpmsim, Model 4 and Model II data disks")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    library = help_library(args.subjects)
    with tempfile.TemporaryDirectory(dir=output) as tmp:
        staged = Path(tmp)
        assemble_reader(Path(args.assembler).resolve(), staged)
        (staged / "HELP.LBR").write_bytes(library)
        if args.disk:
            data_disks(staged)
        for artifact in staged.iterdir():
            artifact.replace(output / artifact.name)
    for name in ("HELP.COM", "HELP.LBR"):
        print(f"{output / name} ({(output / name).stat().st_size} bytes)")
    if args.disk:
        for ext in ("dsk", "dmk", "imd"):
            print(output / ("BetterCPM-1.2-HELP." + ext))


if __name__ == "__main__":
    main()
