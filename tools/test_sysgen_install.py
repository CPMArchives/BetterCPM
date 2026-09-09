#!/usr/bin/env python3
"""Install BetterCP/M on a disposable formatted disk and cold boot it."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess

from add_cpm_file_to_dmk import extract_raw
from build_ccp import assemble
from build_disk_utilities import builtin_source
from build_montezuma_extended_790k import build, RAW_SIZE
from build_trs80_boot import install_files
from run_trs80_command import DEFAULT_EMULATOR, key_args
from test_disk_utilities import medium

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/test-results/sysgen-install"


def setup_program() -> bytes:
    """Make B: an MM Extended SYSTEM alias on physical drive one."""
    source = """        ASEG
        ORG 100H
        XOR A
        LD (REQ),A
        LD DE,REQ
        LD B,3
        LD C,207
        CALL 5
        LD A,L
        OR A
        JR NZ,BAD
        LD A,1
        LD (REQ),A
        LD (REQ+1),A
        LD A,(REQ+20)
        BIT 5,A
        JR Z,SETIT
        AND 0DFH
        OR 040H
        LD (REQ+20),A
        LD HL,(REQ+2)
        SRL H
        RR L
        LD (REQ+2),HL
_toolong: LD HL,(REQ+15)
        ADD HL,HL
        LD (REQ+15),HL
SETIT:  LD DE,REQ
        LD B,4
        LD C,207
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
OK:     DB 'B SYSTEM READY',13,10,'$'
FAIL:   DB 'B SYSTEM SETUP FAILED',13,10,'$'
REQ:    DS 80
        END
"""
    path = OUT / "SETBSYS.COM"
    assemble(Path.home() / "bin/z80asm", source, path, OUT / "setbsys.lst", 0x100)
    return path.read_bytes()


def screen(path: Path) -> str:
    raw = path.read_bytes()[:1920]
    return "\n".join(
        bytes(c & 127 for c in raw[i:i + 80]).decode("ascii").rstrip()
        for i in range(0, 1920, 80)
    )


def main() -> None:
    shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True)
    setup = setup_program()
    source = medium((("SETBSYS.COM", setup),))
    (OUT / "source.dmk").write_bytes(source)

    target_raw = bytearray([0xE5]) * RAW_SIZE
    install_files(target_raw, [("KEEP.TXT", b"SYSGEN PRESERVES THIS FILE\r\n")])
    target_before = build(bytes(target_raw))
    (OUT / "target-before.dmk").write_bytes(target_before)
    (OUT / "target.dmk").write_bytes(target_before)

    command = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
               "-d0", str(OUT / "source.dmk"),
               "-d1", str(OUT / "target.dmk"), "-id", "2500"]
    command += key_args("SETBSYS\r") + ["-id", "1500", "-it"]
    command += key_args("SYSGEN\r") + ["-id", "1200", "-it"]
    command += key_args("B") + ["-id", "800", "-it"]
    command += key_args("Y") + ["-id", "35000", "-it", "-ix"]
    subprocess.run(command, cwd=OUT, check=True, timeout=70)
    captures = sorted(OUT.glob("trs80-text-*.bin"))
    texts = [screen(path) for path in captures]
    for i, text in enumerate(texts):
        (OUT / f"install-{i}.txt").write_text(text)
    assert any("B SYSTEM READY" in text for text in texts), texts
    assert any("System installed and verified" in text for text in texts), texts

    source_raw = extract_raw(source)
    installed_raw = extract_raw((OUT / "target.dmk").read_bytes())
    before_raw = extract_raw(target_before)
    reserved = 2 * 80 * 128
    assert installed_raw[:reserved] == source_raw[:reserved]
    assert installed_raw[reserved:] == before_raw[reserved:]

    (OUT / "cold").mkdir()
    cold = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
            "-d0", str(OUT / "target.dmk"), "-id", "3500", "-it", "-ix"]
    subprocess.run(cold, cwd=OUT / "cold", check=True, timeout=20)
    cold_capture = OUT / "cold/trs80-text-0.bin"
    cold_text = screen(cold_capture)
    (OUT / "cold-boot.txt").write_text(cold_text)
    assert "A0>" in cold_text, cold_text
    assert b"SYSGEN PRESERVES THIS FILE" in installed_raw[reserved:]
    print("PASS: full system area copied and verified; file area preserved; target cold-boots")


if __name__ == "__main__":
    main()
