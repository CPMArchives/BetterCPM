#!/usr/bin/env python3
"""Run BIOSTEST 0471 against cpmsim's assigned and absent RDR providers."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BIOSTEST = ROOT.parent / "cpm-compatibility/suite/build/BIOSTEST.COM"


def run_expect(simulator: Path, disks: Path, script: str, report: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".exp", delete=False) as stream:
        stream.write(script)
        script_path = Path(stream.name)
    try:
        env = dict(os.environ)
        env["PATH"] = str(simulator.parent / "srctools") + os.pathsep + env["PATH"]
        run = subprocess.run(["expect", str(script_path), str(simulator), str(disks),
                              str(report)],
                             cwd=disks.parent, env=env, capture_output=True,
                             text=True, timeout=120)
        if run.returncode:
            evidence = report.read_text(errors="replace")[-1500:]
            raise AssertionError(f"cpmsim reader stage failed: {report}\n{evidence}")
    finally:
        script_path.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--biostest", type=Path, default=DEFAULT_BIOSTEST)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    biostest = args.biostest.resolve()
    if not biostest.is_file():
        raise SystemExit(f"BIOSTEST.COM not found: {biostest}")
    with tempfile.TemporaryDirectory(prefix="bettercpm-reader-") as temporary:
        work = Path(temporary)
        image = (args.output or work / "z80pack-reader").resolve()
        subprocess.run(["python3", str(ROOT / "tools/build_z80pack_boot.py"),
                        "--output", str(image)], cwd=ROOT, check=True,
                       stdout=subprocess.DEVNULL)
        shutil.copy2(biostest, work / "BIOSTEST.COM")
        subprocess.run(["cpmcp", "-T", "raw", "-f", "bettercpm-z80pack-system",
                        str(image / "disks/drivea.dsk"), str(work / "BIOSTEST.COM"),
                        "0:BIOSTEST.COM"], cwd=image, check=True)
        simulator = Path.home() / "CPM/z80pack/cpmsim/cpmsim"
        sender = simulator.parent / "srctools/cpmsend"
        byte_file = work / "reader.txt"
        byte_file.write_bytes(b"R")
        # cpmsend is designed to wait on z80pack's auxin FIFO before cpmsim
        # starts.  This leaves the byte queued before the one-shot READER call.
        sending = subprocess.Popen([str(sender), str(byte_file)], cwd=work,
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, text=True)
        common = """set timeout 30
proc must_exact {pattern} {
    expect {
        -exact $pattern {return}
        timeout {puts "TEST TIMEOUT waiting for: $pattern"; exit 1}
        eof {puts "TEST EOF waiting for: $pattern"; exit 1}
    }
}
proc must_regex {pattern} {
    expect {
        -re $pattern {return}
        timeout {puts "TEST TIMEOUT waiting for expression: $pattern"; exit 1}
        eof {puts "TEST EOF waiting for expression: $pattern"; exit 1}
    }
}
log_file -noappend [lindex $argv 2]
spawn [lindex $argv 0] -z -d [lindex $argv 1]
must_regex {\\r\\nA0>}
send -- "BIOSTEST /0471\\r"
must_exact "Run controlled console/logical-device tests (Y/N)?"
send -- "Y"
must_exact "Type one uppercase K now:"
send -- "K"
"""
        stage1 = common + """must_exact "Y calls READER"
send -- "Y"
must_exact "0471 stage 1 saved"
must_regex {\\r\\nA0>}
send -- "BYE\\r"
expect eof
"""
        try:
            run_expect(simulator, image / "disks", stage1,
                       image / "reader-stage1.txt")
            _, sender_error = sending.communicate(timeout=15)
        finally:
            if sending.poll() is None:
                sending.terminate()
                sending.wait(timeout=5)
        if sending.returncode:
            raise AssertionError(f"cpmsend failed during normal-reader stage: "
                                 f"{sender_error.strip()}")
        stage2 = common + """must_exact "Y=call verified provider"
send -- "Y"
must_exact "READER returned R; absent READER returned Ctrl-Z"
must_regex {\\r\\nA0>}
send -- "BYE\\r"
expect eof
"""
        run_expect(simulator, image / "disks", stage2, image / "reader-stage2.txt")
        if args.output:
            print(f"Evidence: {image / 'reader-stage1.txt'}")
            print(f"Evidence: {image / 'reader-stage2.txt'}")
    print("PASS: z80pack normal and absent READER providers satisfy BIOSTEST 0471.")


if __name__ == "__main__":
    main()
