#!/usr/bin/env python3
"""Qualify the required SUBMIT/XSUB path on a private z80pack disk set."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path

from build_ccp import assemble
from test_submit_xsub import marker

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER = Path("/Users/nathanael/bin/z80asm")


def input_probe(temporary: Path) -> bytes:
    source = """        ORG 0100H
        LD HL,0200H
        LD (HL),20
        EX DE,HL
        LD C,10
        CALL 5
        LD A,(0201H)
        CP 9
        JR NZ,BAD
        LD HL,0202H
        LD DE,WANT
        LD B,9
CHK:    LD A,(DE)
        CP (HL)
        JR NZ,BAD
        INC DE
        INC HL
        DJNZ CHK
        LD DE,GOOD
        JR SHOW
BAD:    LD DE,FAIL
SHOW:   LD C,9
        CALL 5
        RET
WANT:   DB 'BATCHFULL'
GOOD:   DB 13,10,'INPUT OK',13,10,'$'
FAIL:   DB 13,10,'INPUT FAILED',13,10,'$'
        END
"""
    return assemble(
        ASSEMBLER,
        source,
        temporary / "INPUT.COM",
        temporary / "input.lst",
        0x100,
    )


def copy_to_a(work: Path, source: Path, destination: str) -> None:
    subprocess.run(
        [
            "cpmcp",
            "-f",
            "bettercpm-default",
            str(work / "disks/drivea.dsk"),
            str(source),
            f"0:{destination}",
        ],
        cwd=work,
        check=True,
    )


def run_case(
    image: Path,
    simulator: Path,
    label: str,
    files: Callable[[Path], dict[str, bytes]],
    body: str,
) -> None:
    with tempfile.TemporaryDirectory(
        prefix=f"bettercpm-z80pack-{label}-"
    ) as name:
        work = Path(name)
        shutil.copytree(image / "disks", work / "disks")
        shutil.copy2(image / "diskdefs", work / "diskdefs")
        # Free two directory entries in this private image without removing
        # the R3 transaction overlays needed by Function 177.
        for disposable in ("bdosprb.com", "rsx2tst.com"):
            subprocess.run(
                [
                    "cpmrm",
                    "-f",
                    "bettercpm-default",
                    str(work / "disks/drivea.dsk"),
                    f"0:{disposable}",
                ],
                cwd=work,
                check=True,
            )
        for filename, content in files(work).items():
            path = work / filename
            path.write_bytes(content)
            copy_to_a(work, path, filename)

        report = work / "verification.txt"
        expect_file = work / "test.exp"
        expect_file.write_text(
            r'''set timeout 30
set send_slow {1 .02}
log_file -noappend [lindex $argv 2]
expect_before timeout {puts "TEST TIMEOUT"; exit 1}
proc prompt {} {
 expect {
  -exact {A0>_ } {}
  timeout {puts "PROMPT TIMEOUT"; exit 1}
  eof {puts "UNEXPECTED EXIT"; exit 1}
 }
}
spawn [lindex $argv 0] -z -d [lindex $argv 1]
expect -exact "Booting..."
prompt
'''
            + body
        )
        environment = dict(os.environ)
        environment["PATH"] = (
            str(simulator.parent / "srctools")
            + os.pathsep
            + environment["PATH"]
        )
        run = subprocess.run(
            [
                "expect",
                str(expect_file),
                str(simulator),
                str(work / "disks"),
                str(report),
            ],
            cwd=work,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if run.returncode:
            transcript = (
                report.read_text(errors="replace")[-3000:]
                if report.exists()
                else run.stdout[-3000:]
            )
            raise AssertionError(
                f"z80pack {label} test failed: {report}\n{transcript}"
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--image-dir", type=Path, default=ROOT / "build/z80pack"
    )
    parser.add_argument(
        "--simulator",
        type=Path,
        default=Path.home() / "projects/git/z80pack/cpmsim/cpmsim",
    )
    args = parser.parse_args()
    image = args.image_dir.expanduser().resolve()
    simulator = args.simulator.expanduser().resolve()

    for dependency in (image / "disks", image / "diskdefs", simulator):
        if not dependency.exists():
            raise SystemExit(f"missing z80pack batch-test dependency: {dependency}")

    run_case(
        image,
        simulator,
        "submit",
        lambda work: {
            "MARK.COM": marker(work),
            # The final line deliberately has no CR, proving physical EOF.
            "ORDER.SUB": b"MARK $1\r\nMARK $$2\r\nMARK LAST",
        },
        r'''
send -s -- "SUBMIT ORDER FIRST\r"
expect -exact "MARK: FIRST"
expect -exact {MARK: $2}
expect -exact "MARK: LAST"
prompt
send -s -- "DIR $$$.SUB\r"
expect -exact "NO FILE"
prompt
send -s -- "BYE\r"
expect eof
''',
    )
    run_case(
        image,
        simulator,
        "xsub",
        lambda work: {
            "INPUT.COM": input_probe(work),
            "XINPUT.SUB": b"XSUB\r\nINPUT\r\nBATCHFULL\r\nVER",
        },
        r'''
send -s -- "SUBMIT XINPUT\r"
expect -exact "(xsub active)"
expect -exact "INPUT OK"
expect -exact "Version 1.0"
prompt
send -s -- "DIR $$$.SUB\r"
expect -exact "NO FILE"
prompt
send -s -- "BYE\r"
expect eof
''',
    )

    print("PASS: z80pack SUBMIT ordering, substitution, EOF and cleanup")
    print("PASS: z80pack XSUB Function-10 input and command continuation")


if __name__ == "__main__":
    main()
