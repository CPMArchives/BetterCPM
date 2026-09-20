#!/usr/bin/env python3
"""Build and prove the narrow cpmsim ROM-qualification guard."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "tools/cpmsim-rom-qualification.patch"
ROM_START = "D500"
VIOLATION_EXIT = 86


def mostek(path: Path, code: bytes, address: int = 0xD600) -> None:
    path.write_bytes(bytes((0xFF, address & 0xFF, address >> 8)) + code)


def run_probe(simulator: Path, work: Path, name: str, code: bytes,
              expected: int, required: tuple[str, ...], protect: bool = True) -> None:
    image = work / f"{name}.bin"
    mostek(image, code)
    env = dict(os.environ)
    env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env.get("PATH", "")
    if protect:
        env["CPMSIM_ROM_START"] = ROM_START
    else:
        env.pop("CPMSIM_ROM_START", None)
    report = work / f"{name}.out"
    with report.open("wb") as stream:
        result = subprocess.run(
            [str(simulator), "-z", "-d", str(work / "disks"), "-x", str(image)],
            cwd=work, env=env, stdin=subprocess.DEVNULL,
            stdout=stream, stderr=subprocess.STDOUT, timeout=20)
    output = report.read_text(errors="replace")
    if result.returncode != expected:
        raise AssertionError(
            f"{name}: exit {result.returncode}, expected {expected}\n{output}")
    for item in required:
        if item not in output:
            raise AssertionError(f"{name}: missing {item!r}\n{output}")
    print(f"PASS: {name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--z80pack-source", type=Path,
        default=Path.home() / "projects/git/z80pack",
        help="z80pack checkout containing cpmsim, z80core and iodevices")
    args = parser.parse_args()
    source = args.z80pack_source.expanduser().resolve()
    for relative in ("cpmsim", "z80core", "iodevices"):
        if not (source / relative).is_dir():
            raise SystemExit(f"missing {source / relative}")

    with tempfile.TemporaryDirectory(prefix="bettercpm-rom-guard-") as temporary:
        work = Path(temporary)
        staged = work / "z80pack"
        for relative in ("cpmsim", "z80core", "iodevices"):
            ignored = ("*.o", "*.d", ".DS_Store")
            if relative == "cpmsim":
                ignored += ("disks", "roms", "auxiliary*.txt", "printer.txt", "cpmsim")
            shutil.copytree(source / relative, staged / relative,
                            ignore=shutil.ignore_patterns(*ignored))
        subprocess.run(["patch", "-p1", "-i", str(PATCH)], cwd=staged, check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run(["make"], cwd=staged / "cpmsim/srctools", check=True,
                       stdout=subprocess.DEVNULL)
        subprocess.run(["make", "ROM_QUALIFY=YES", "build"],
                       cwd=staged / "cpmsim/srcsim", check=True,
                       stdout=subprocess.DEVNULL)
        simulator = staged / "cpmsim/cpmsim"
        disks = work / "disks"
        disks.mkdir()
        # The probes read only the first sector. Four conventional images keep
        # cpmsim initialization independent of a user's mounted media.
        for letter in "abcd":
            (disks / f"drive{letter}.dsk").write_bytes(bytes(77 * 26 * 128))

        halt = bytes((0x3E, 0xAA, 0xD3, 0xA0, 0x3E, 0x80, 0xD3, 0xA0))
        run_probe(simulator, work, "execute-in-place",
                  bytes((0x3E, 0x5A, 0x32, 0x00, 0x02)) + halt, 0,
                  ("ROM QUALIFICATION ACTIVE START=D500",))
        run_probe(simulator, work, "cpu-write",
                  bytes((0x3E, 0x42, 0x32, 0x00, 0xD7, 0x76)), VIOLATION_EXIT,
                  ("ROM WRITE VIOLATION", "ADDRESS=D700", "DATA=42", "SOURCE=CPU"))
        run_probe(simulator, work, "guest-unlock",
                  bytes((0xAF, 0xD3, 0x17, 0x76)), VIOLATION_EXIT,
                  ("ROM PROTECTION VIOLATION", "PORT=17", "SOURCE=CONTROL"))
        run_probe(simulator, work, "guest-boundary-change",
                  bytes((0x3E, 0xC0, 0xD3, 0x16, 0x76)), VIOLATION_EXIT,
                  ("ROM PROTECTION VIOLATION", "PORT=16", "SOURCE=CONTROL"))
        run_probe(simulator, work, "dma-write",
                  bytes((0xAF, 0xD3, 0x0A, 0xD3, 0x0B,
                         0x3E, 0x01, 0xD3, 0x0C,
                         0xAF, 0xD3, 0x0F,
                         0x3E, 0xD7, 0xD3, 0x10,
                         0xAF, 0xD3, 0x0D, 0xDB, 0x0E, 0x76)), VIOLATION_EXIT,
                  ("ROM WRITE VIOLATION", "ADDRESS=D700", "SOURCE=DMA"))
        boot = bytearray(77 * 26 * 128)
        boot[:6] = bytes((0x3E, 0x42, 0x32, 0x00, 0xD7, 0x76))
        (disks / "drivea.dsk").write_bytes(boot)
        run_probe(simulator, work, "reset-reapplies-protection",
                  bytes((0x3E, 0xAA, 0xD3, 0xA0, 0x3E, 0x40, 0xD3, 0xA0)),
                  VIOLATION_EXIT,
                  ("ROM WRITE VIOLATION", "ADDRESS=D700", "SOURCE=CPU"))
        run_probe(simulator, work, "ordinary-mode-unchanged",
                  bytes((0x3E, 0x42, 0x32, 0x00, 0xD7)) + halt, 0, (), protect=False)

    print("PASS: cpmsim qualification guard primitives")


if __name__ == "__main__":
    main()
