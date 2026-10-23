#!/usr/bin/env python3
"""Smoke-test the standalone command against stock CP/M 2.2 on z80pack.

Uses disposable IBM-3740 media copied from the emulator's CP/M library.
Checks extracted binary/padding, destination B:, collisions, bad checksum,
unsafe embedded names and the original compressed input files afterward.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_usq import build
from test_usq import squeeze
from test_usq_com import padded


def run(*command, **kwargs):
    return subprocess.run(list(map(str, command)), check=True, capture_output=True,
                          text=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembler", type=Path, default=Path.home() / "bin/z80asm")
    parser.add_argument("--z80pack", type=Path, default=Path.home() / "projects/git/z80pack")
    args = parser.parse_args()
    simulator = args.z80pack / "cpmsim/cpmsim"
    template = args.z80pack / "cpmsim/disks/library/cpm22-62khd.dsk"
    with tempfile.TemporaryDirectory(prefix="bettercpm-usq-real-cpm-") as temporary:
        work = Path(temporary)
        image = build(args.assembler, work)
        disks = work / "disks"
        disks.mkdir()
        for letter in "ab":
            shutil.copy2(template, disks / f"drive{letter}.dsk")
        run("mkfs.cpm", "-f", "ibm-3740", disks / "driveb.dsk")
        run("cpmcp", "-f", "ibm-3740", disks / "drivea.dsk", work / "USQ.COM", "0:USQ.COM")
        data = bytes(range(256)) * 3 + b"CP/M binary\x1a\x00\x90\xff"
        good = squeeze(data, name=b"OUT.BIN")
        bad = bytearray(squeeze(b"checksum failure" * 20, name=b"BAD.BIN"))
        bad[2] ^= 1
        fixtures = {"GOOD.SQ": good, "BAD.SQ": bytes(bad),
                    "UNSAFE.SQ": squeeze(b"unsafe", name=b"B:EVIL.BIN"),
                    "EMPTY.SQ": squeeze(b"", name=b"EMPTY.BIN")}
        originals = {}
        for name, raw in fixtures.items():
            host = work / name
            host.write_bytes(raw)
            run("cpmcp", "-f", "ibm-3740", disks / "drivea.dsk", host, f"0:{name}")
            snapshot = work / ("BEFORE-" + name)
            run("cpmcp", "-f", "ibm-3740", disks / "drivea.dsk", f"0:{name}", snapshot)
            originals[name] = snapshot.read_bytes()
        script = r'''
set timeout 10
proc await {text} {
 expect {
  -exact $text {return}
  timeout {puts "TIMEOUT waiting for $text"; exit 1}
  eof {puts "EOF waiting for $text"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
await "A>"
send -- "USQ GOOD.SQ B:\r"
await "USQ: complete."
await "A>"
send -- "USQ GOOD.SQ B:\r"
await "USQ: output exists; nothing replaced."
await "A>"
send -- "USQ BAD.SQ B:\r"
await "USQ: checksum mismatch."
await "A>"
send -- "USQ UNSAFE.SQ B:\r"
await "USQ: unsafe embedded filename."
await "A>"
send -- "USQ EMPTY.SQ B:\r"
await "USQ: complete."
await "A>"
send -- "USQ\r"
await "Usage: USQ"
await "A>"
send -- "\034"
expect eof
'''
        (work / "test.exp").write_text(script)
        env = dict(os.environ)
        env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env["PATH"]
        result = subprocess.run(["expect", str(work / "test.exp"), str(simulator), str(disks)],
                                cwd=work, env=env, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        for name, expected in (("OUT.BIN", padded(data)), ("EMPTY.BIN", b"")):
            host = work / name
            run("cpmcp", "-f", "ibm-3740", disks / "driveb.dsk", f"0:{name}", host)
            assert host.is_file(), (name, result.stdout, result.stderr)
            assert host.read_bytes() == expected, (name, result.stdout, result.stderr)
        listing = run("cpmls", "-f", "ibm-3740", disks / "driveb.dsk").stdout.upper()
        assert "BAD.BIN" not in listing and "EVIL.BIN" not in listing and ".$$$" not in listing, listing
        # Verify the source directory and every squeezed source after all runs.
        for name, raw in fixtures.items():
            host = work / ("CHECK-" + name)
            run("cpmcp", "-f", "ibm-3740", disks / "drivea.dsk", f"0:{name}", host)
            actual = host.read_bytes()
            assert actual[:len(raw)] == raw, (name, "source data changed", len(raw), len(actual))
            assert actual == originals[name], (name, "source contents/length changed")
        assert (work / "USQ.COM").read_bytes() == image
        print("PASS: 6 stock CP/M 2.2 commands; binary output, padding, collision,")
        print("checksum cleanup, unsafe names, empty output and source preservation verified.")


if __name__ == "__main__":
    main()
