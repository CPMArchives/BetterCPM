#!/usr/bin/env python3
"""Prove raw images are interchangeable between BetterCP/M and cpmtools."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MARKER = b"BETTERCPM CPMTOOLS INTERCHANGE PASS\r\n"
PAYLOAD = (MARKER * ((1280 + len(MARKER) - 1) // len(MARKER)))[:1280]
CASES = (
    ("mm-standard-system", 40 * 18 * 256, "A", 40,
     "Montezuma Micro Standard SYSTEM"),
    ("mm-80t-ds-data", 160 * 10 * 512, "H", 80,
     "Montezuma Micro 80T DS DATA"),
    ("ampro-little-board", 40 * 10 * 512, ".F", 40,
     "Ampro Little Board"),
    ("ampro-little-board-ds", 80 * 10 * 512, ".G", 40,
     "Ampro Little Board double-sided"),
)


def run_case(image: Path, simulator: Path,
             case: tuple[str, int, str, int, str]) -> None:
    slug, image_size, selection, cylinders, description = case
    fmt = "bettercpm-" + slug
    with tempfile.TemporaryDirectory(prefix=f"bettercpm-z80pack-{slug}-",
                                     dir="/private/tmp") as tmp:
        work = Path(tmp)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        medium = work / "disks/driveb.dsk"
        medium.write_bytes(b"\xe5" * image_size)
        subprocess.run(["mkfs.cpm", "-f", fmt, str(medium)], check=True,
                       cwd=work)
        source = work / "HOST.DAT"
        source.write_bytes(PAYLOAD)
        subprocess.run(["cpmcp", "-T", "raw", "-f", fmt, str(medium),
                        str(source), "0:HOST.DAT"], check=True, cwd=work)

        # Use current CONFIG's stable command interface, not obsolete menu keys.
        from test_z80pack_sysgen_install import session
        names = {'mm-standard-system': 'MM Standard SYSTEM',
                 'mm-80t-ds-data': 'MM 80T DS DATA',
                 'ampro-little-board': 'Ampro Little Board 40T SS',
                 'ampro-little-board-ds': 'Ampro Little Board 40T DS'}
        sides = 2 if slug in ('mm-80t-ds-data','ampro-little-board-ds') else 1
        interactions = []
        for text in (f'CONFIG /PHYSICAL=1 /TRACKS={cylinders} /SIDES={sides} /STEP=6',
                     f'CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="{names[slug]}"'):
            interactions.extend([(text.encode()+b'\r',b'Disk configuration changed (until cold boot).',30),
                                 (b'',b'A0>_ ',30)])
        interactions.extend([(b'TYPE B:HOST.DAT\r',MARKER.rstrip(),30),
                             (b'',b'A0>_ ',30),
                             (b'COPY B:HOST.DAT B:ROUND.DAT\r',b'A0>_ ',30)])
        session(simulator, work/'disks', interactions, image/f'interchange-{slug}.txt')

        extracted = work / "ROUND.DAT"
        subprocess.run(["cpmcp", "-T", "raw", "-f", fmt, str(medium),
                        "0:ROUND.DAT", str(extracted)], check=True, cwd=work)
        actual = extracted.read_bytes()
        if actual != PAYLOAD:
            mismatch = next((index for index, pair in
                             enumerate(zip(actual, PAYLOAD))
                             if pair[0] != pair[1]),
                            min(len(actual), len(PAYLOAD)))
            raise AssertionError(f"{description}: extracted length {len(actual)} "
                                 f"!= {len(PAYLOAD)}, first mismatch {mismatch}")
        print(f"PASS: {description} is byte-identical after cpmtools -> "
              "BetterCP/M -> cpmtools")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()
    for case in CASES:
        run_case(image, simulator, case)


if __name__ == "__main__":
    main()
