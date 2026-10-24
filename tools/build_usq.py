#!/usr/bin/env python3
"""Build standalone USQ.COM for the Utilities disk."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import tempfile

from codec_version import prepare_version, version_text as codec_version_text, recorded_build

ROOT = Path(__file__).resolve().parents[1]


def version_text():
    return codec_version_text("USQ")


@recorded_build('USQ')
def build(assembler, destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bettercpm-usq-com-build-") as temporary:
        work = Path(temporary)
        prepare_version("USQ", work)
        for name in ("codec.inc", "codec.mac", "usq.inc", "usq.mac"):
            shutil.copy2(ROOT / "src/codec" / name, work / name)
        shutil.copy2(ROOT / "src/utilities/common/codecfile.mac", work / "codecfile.mac")
        shutil.copy2(ROOT / "src/utilities/usq.mac", work / "command.mac")
        subprocess.run([str(assembler), "-e32", "-fb", "-ousq.bin", "-lusq.lst",
                        "command.mac"], cwd=work, check=True)
        image = (work / "usq.bin").read_bytes()
        if image[:0x100] == bytes(0x100):
            image = image[0x100:]
        if not image or image[0] != 0xC3 or len(image) > 0xCF00:
            raise ValueError("invalid or oversized USQ.COM image")
        (destination / "USQ.COM").write_bytes(image)
        shutil.copy2(work / "usq.lst", destination / "usq.lst")
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "build/utilities")
    parser.add_argument('--identity-state',choices=('auto','assigned','development'),default='auto')
    parser.add_argument('--target',choices=('z80pack','trs80gp'),default='z80pack')
    args = parser.parse_args()
    image = build(args.assembler, args.output_dir, identity_state=args.identity_state, target=args.target)
    print(f"{len(image)} bytes; SHA-256 {hashlib.sha256(image).hexdigest()}")
    print(args.output_dir / "USQ.COM")


if __name__ == "__main__":
    main()
