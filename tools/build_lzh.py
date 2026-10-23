#!/usr/bin/env python3
"""Build standalone LZH.COM for the Utilities disk."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

from codec_version import prepare_version, version_text as codec_version_text

ROOT = Path(__file__).resolve().parents[1]


def version_text():
    return codec_version_text("LZH")


def build(assembler, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bettercpm-lzh-com-build-") as temporary:
        work = Path(temporary)
        prepare_version("LZH", work)
        for name in ("codec.inc", "codec.mac", "lzh.inc", "lzh.mac"):
            shutil.copy2(ROOT / "src/codec" / name, work / name)
        shutil.copy2(ROOT / "src/utilities/common/codecfile.mac", work / "codecfile.mac")
        shutil.copy2(ROOT / "src/utilities/lzh.mac", work / "command.mac")
        subprocess.run([str(assembler), "-e32", "-fb", "-olzh.bin", "-llzh.lst",
                        "command.mac"], cwd=work, check=True)
        image = (work / "lzh.bin").read_bytes()
        if image[:0x100] == bytes(0x100):
            image = image[0x100:]
        if not image or image[0] != 0xC3 or len(image) > 0xCF00:
            raise ValueError("invalid or oversized LZH.COM image")
        (destination / "LZH.COM").write_bytes(image)
        shutil.copy2(work / "lzh.lst", destination / "lzh.lst")
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/utilities")
    args = parser.parse_args()
    image = build(args.assembler, args.output_dir)
    print(f"{len(image)} bytes; SHA-256 {hashlib.sha256(image).hexdigest()}")
    print(args.output_dir / "LZH.COM")


if __name__ == "__main__":
    main()
