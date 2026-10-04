#!/usr/bin/env python3
"""Prove z80pack DUP formats uniform media and rejects mixed media safely."""
from __future__ import annotations

import argparse
import os
import pty
import select
import shutil
import signal
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    parser.add_argument("--unsupported", action="store_true",
                        help="exercise mixed-sector pre-write rejection")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()

    with tempfile.TemporaryDirectory(prefix="bettercpm-dup-format-",
                                     dir="/private/tmp") as temporary:
        work = Path(temporary)
        shutil.copytree(image / "disks", work / "disks")
        target = work / "disks/driveb.dsk"
        target.write_bytes(b"\xa5" * len(target.read_bytes()))
        environment = dict(os.environ)
        environment["PATH"] = (str(simulator.parent / "srctools") +
                               os.pathsep + environment["PATH"])
        child, terminal = pty.fork()
        if child == 0:
            os.chdir(work)
            os.execve(str(simulator),
                      [str(simulator), "-z", "-d", str(work / "disks")],
                      environment)
        transcript = bytearray()
        pending = bytearray()

        def expect(text: str, timeout: float = 30) -> None:
            wanted = text.encode()
            deadline = time.monotonic() + timeout
            while wanted not in pending:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise AssertionError(
                        f"timeout waiting for {text!r}:\n"
                        f"{bytes(transcript[-1500:]).decode(errors='replace')}"
                    )
                ready, _, _ = select.select([terminal], [], [], remaining)
                if not ready:
                    continue
                data = os.read(terminal, 65536)
                if not data:
                    raise AssertionError(f"unexpected emulator exit before {text!r}")
                transcript.extend(data)
                pending.extend(data)
            end = pending.index(wanted) + len(wanted)
            del pending[:end]

        try:
            expect("A0>_ ")
            if args.unsupported:
                os.write(terminal, b"RSX LOAD FDF\r")
                expect("A0>_ ")
                os.write(terminal, b"CONFIG\r")
                expect("Your choice:")
                os.write(terminal, b"G")
                expect("Your choice:")
                os.write(terminal, b"B")
                for _ in range(6):
                    expect("Your choice:")
                    os.write(terminal, b".")
                expect("Your choice:")
                os.write(terminal, b"I")
                expect("Which physical disk drive")
                os.write(terminal, b"1")
                expect("Disk configuration changed")
                expect("Push ENTER for menu.")
                os.write(terminal, b"\r")
                expect("Choose the letter of the drive to change:")
                os.write(terminal, b"\003")
                expect("A0>_ ")
            os.write(terminal, b"DUP\r")
            expect("Your choice:")
            os.write(terminal, b"A")
            expect("Choose logical drive")
            expect("Your choice:")
            os.write(terminal, b"B")
            expect("Format this disk? [Y/N]")
            os.write(terminal, b"Y")
            if args.unsupported:
                expect("Unsupported operation or disk address.")
            else:
                expect("Tracks written and verified: 00080", 120)
                expect("Format complete.")
            os.write(terminal, b"\r")
            expect("Your choice:")
            os.write(terminal, b"\003")
            expect("A0>_ ")
            os.write(terminal, b"BYE\r")
            expect("System halted")
        finally:
            try:
                os.kill(child, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                os.waitpid(child, 0)
            except ChildProcessError:
                pass
            os.close(terminal)
        report = image / ("dup-format-unsupported-verification.txt"
                          if args.unsupported else "dup-format-verification.txt")
        report.write_bytes(transcript)
        actual = target.read_bytes()
        if args.unsupported:
            assert actual == b"\xa5" * len(actual), \
                "unsupported format changed raw image"
        else:
            assert actual == b"\xe5" * len(actual), "DUP did not erase raw image"
    if args.unsupported:
        print("PASS: z80pack DUP rejected mixed-sector formatting before writing")
    else:
        print("PASS: z80pack DUP formatted and verified the complete raw image")


if __name__ == "__main__":
    main()
