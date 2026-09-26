#!/usr/bin/env python3
"""Qualify explicit/file SYSGEN on a larger compatible SYSTEM definition."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_ccp import assemble
from build_montezuma_extended_790k import RAW_SIZE, build
from build_system_package import compose
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_disk_utilities import medium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/test-results/sysgen-cross-format"


def setup_program() -> bytes:
    source = """        ASEG
        ORG 100H
        XOR A
        LD (REQ),A
        LD DE,REQ
        LD B,3
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD A,1
        LD (REQ),A
        LD (REQ+1),A
        LD A,(REQ+20)
        AND 0DFH
        OR 040H
        LD (REQ+20),A
        LD HL,(REQ+2)
        SRL H
        RR L
        LD (REQ+2),HL
        LD HL,6
        LD (REQ+15),HL
        LD HL,384
        LD (REQ+7),HL
        LD DE,REQ
        LD B,4
        LD C,181
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD DE,OK
        JR PRINT
BAD:    LD DE,FAIL
PRINT:  LD C,9
        CALL 5
        JP 0
OK:     DB 'B CROSS FORMAT READY',13,10,'$'
FAIL:   DB 'B CROSS FORMAT FAILED',13,10,'$'
REQ:    DS 80
        END
"""
    path = OUT / "SETCROSS.COM"
    assemble(Path.home() / "bin/z80asm", source, path, OUT / "setcross.lst", 0x100)
    return path.read_bytes()


def screen(path: Path) -> str:
    raw = path.read_bytes()[:1920]
    return "\n".join(bytes(c & 127 for c in raw[i:i + 80]).decode("ascii").rstrip()
                     for i in range(0, 1920, 80))


def run_case(name: str, command_text: str, with_package: bool) -> None:
    work = OUT / name
    work.mkdir()
    setup = setup_program()
    extras = [("SETCROSS.COM", setup)]
    if with_package:
        extras.append(("SYSTEM.SYS", compose()[0]))
    source = medium(tuple(extras))
    target = build(bytes((0xE5,)) * RAW_SIZE)
    (work / "source.dmk").write_bytes(source)
    (work / "target.dmk").write_bytes(target)
    args = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
            "-d0", str(work / "source.dmk"), "-d1", str(work / "target.dmk"),
            "-id", "2500"]
    args += key_args("SETCROSS\r") + ["-id", "2500", "-it"]
    args += key_args(command_text + "\r") + ["-id", "2500", "-it"]
    args += key_args("Y") + ["-id", "35000", "-it", "-ix"]
    subprocess.run(args, cwd=work, check=True, timeout=70)
    texts = [screen(path) for path in sorted(work.glob("trs80-text-*.bin"))]
    assert any("B CROSS FORMAT READY" in text for text in texts), texts
    assert any("System installed and verified" in text for text in texts), texts
    before = extract_raw(target)
    after = extract_raw((work / "target.dmk").read_bytes())
    assert after[20 * 1024:] == before[20 * 1024:]
    assert after[:20 * 1024] != before[:20 * 1024]
    cold = work / "cold"
    cold.mkdir()
    subprocess.run([str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                    "-d0", str(work / "target.dmk"), "-id", "4000", "-it", "-ix"],
                   cwd=cold, check=True, timeout=20)
    assert "A0>" in screen(cold / "trs80-text-0.bin")


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    run_case("drive-source", "SYSGEN A: B:", False)
    run_case("file-source", "SYSGEN SYSTEM.SYS B:", True)
    print("PASS: explicit and SYSTEM.SYS cross-format installs preserve files and boot")


if __name__ == "__main__":
    main()
