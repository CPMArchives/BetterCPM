#!/usr/bin/env python3
"""Install onto a populated z80pack disk, preserve files, and cold boot it."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pty
import select
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def session(simulator: Path, disks: Path,
            commands: list[tuple[bytes, bytes, float]],
            transcript_path: Path | None = None) -> bytes:
    environment = dict(os.environ)
    environment["PATH"] = (str(simulator.parent / "srctools") +
                           os.pathsep + environment["PATH"])
    child, terminal = pty.fork()
    if child == 0:
        os.chdir(disks.parent)
        os.execve(str(simulator),
                  [str(simulator), "-z", "-d", str(disks)], environment)
    transcript = bytearray()
    pending = bytearray()

    def expect(wanted: bytes, timeout: float) -> None:
        deadline = time.monotonic() + timeout
        while wanted not in pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError(
                    f"timeout waiting for {wanted!r}:\n"
                    f"{bytes(transcript[-2000:]).decode(errors='replace')}")
            ready, _, _ = select.select([terminal], [], [], remaining)
            if not ready:
                continue
            data = os.read(terminal, 65536)
            if not data:
                raise AssertionError(f"emulator exited before {wanted!r}")
            transcript.extend(data)
            if transcript_path is not None:
                transcript_path.write_bytes(transcript)
            pending.extend(data)
        end = pending.index(wanted) + len(wanted)
        del pending[:end]

    try:
        expect(b"A0>_ ", 30)
        for outgoing, wanted, timeout in commands:
            os.write(terminal, outgoing)
            expect(wanted, timeout)
    finally:
        try:
            os.kill(child, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + 1
        while True:
            try:
                result, _ = os.waitpid(child, os.WNOHANG)
            except ChildProcessError:
                break
            if result:
                break
            if time.monotonic() >= deadline:
                try:
                    os.kill(child, signal.SIGKILL)
                    os.waitpid(child, 0)
                except (ChildProcessError, ProcessLookupError):
                    pass
                break
            time.sleep(0.02)
        os.close(terminal)
    return bytes(transcript)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-dir", type=Path,
                        default=ROOT / "build/z80pack")
    parser.add_argument("--simulator", type=Path,
                        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim")
    args = parser.parse_args()
    image = args.image_dir.resolve()
    simulator = args.simulator.expanduser().resolve()
    manifest = json.loads((image / "manifest.json").read_text())
    reserved = manifest["reserved_records"] * 128
    report = ROOT / "build/test-results/z80pack-sysgen-install"
    shutil.rmtree(report, ignore_errors=True)
    report.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="bettercpm-z80-sysgen-",
                                     dir="/private/tmp") as temporary:
        work = Path(temporary)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        target = work / "disks/driveb.dsk"
        sentinel = work / "KEEP.TXT"
        sentinel.write_bytes(b"SYSGEN PRESERVES THIS FILE\r\n")
        subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                        str(target), str(sentinel), "0:"], cwd=work, check=True)
        before = target.read_bytes()
        install = session(simulator, work / "disks", [
            (b"SYSGEN A: B:\r", b"Proceed (Y/N)?", 30),
            (b"Y", b"System installed and verified.", 60),
            (b"BYE\r", b"System halted", 30),
        ])
        after = target.read_bytes()
        assert after[:reserved] != before[:reserved], "system area was unchanged"
        assert after[reserved:] == before[reserved:], "filesystem area changed"
        recovered = work / "RECOVERED.TXT"
        subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-default",
                        str(target), "0:KEEP.TXT", str(recovered)],
                       cwd=work, check=True)
        assert recovered.read_bytes() == sentinel.read_bytes()

        installed = work / "disks/library/installed-system.dsk"
        installed.write_bytes(after)
        drive_a = work / "disks/drivea.dsk"
        drive_a.unlink()
        drive_a.symlink_to(Path("library/installed-system.dsk"))
        cold = session(simulator, work / "disks", [])

        (report / "install-transcript.txt").write_bytes(install)
        (report / "cold-boot-transcript.txt").write_bytes(cold)
        (report / "target-before.dsk").write_bytes(before)
        (report / "target-installed.dsk").write_bytes(after)
        evidence = {
            "command": "SYSGEN A: B:",
            "format": manifest["format"],
            "reserved_records": manifest["reserved_records"],
            "before_sha256": digest(before),
            "installed_sha256": digest(after),
            "filesystem_sha256": digest(after[reserved:]),
            "simulator": str(simulator),
        }
        (report / "evidence.json").write_text(
            json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print("PASS: z80pack SYSGEN preserved populated filesystem and cold-booted target")


if __name__ == "__main__":
    main()
