#!/usr/bin/env python3
"""Destroy the entire advertised TPA in a real transient, then warm boot."""
from pathlib import Path
import subprocess
import tempfile

from build_ccp import assemble
from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args
from system_layout import LAYOUT

SOURCE = """
        INCLUDE layout.inc
        ORG     00100H
        LD      SP,001F0H
        LD      A,(00080H)
        OR      A
        LD      DE,LY_TPA
        JR      Z,BOUND
        LD      DE,LY_TPA-00400H
BOUND:
        LD      HL,(00006H)
        OR      A
        SBC     HL,DE
        JR      NZ,FAIL
        LD      HL,(00006H)
        LD      DE,00200H
        OR      A
        SBC     HL,DE
        LD      B,H
        LD      C,L
        DEC     BC
        LD      HL,00200H
        LD      DE,00201H
        LD      (HL),0A5H
        LDIR
        LD      HL,(00006H)
        LD      DE,00200H
        OR      A
        SBC     HL,DE
        LD      B,H
        LD      C,L
        LD      HL,00200H
CHECK:
        LD      A,(HL)
        CP      0A5H
        JR      NZ,FAIL
        INC     HL
        DEC     BC
        LD      A,B
        OR      C
        JR      NZ,CHECK
        LD      C,12
        CALL    00005H
        CP      022H
        JR      NZ,FAIL
        LD      DE,OKMSG
        JR      PRINT
FAIL:
        LD      DE,BADMSG
PRINT:
        LD      C,9
        CALL    00005H
        JP      00000H
OKMSG:  DB      'TPA overwrite verified',13,10,'$'
BADMSG: DB      'TPA overwrite FAILED',13,10,'$'
        END
"""


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bettercpm-packed-tpa-") as temporary:
        work = Path(temporary)
        program = work / "TPAFILL.COM"
        binary = assemble(Path("/Users/nathanael/bin/z80asm"), SOURCE,
                          program, work / "tpafill.lst", 0x100)
        assert len(binary) < 0xE0, "test code overlaps its private stack"
        disk = work / "packed.dmk"
        subprocess.run(["python3", str(ROOT / "tools/build_trs80_boot.py"),
                        "--include", str(program), "--output", str(disk)],
                       cwd=ROOT, check=True, capture_output=True)
        # Each execution overwrites the CCP and all CPX code, including the
        # old C000h/C100h kernel locations. The second also has a live RSX.
        commands = ("TPAFILL", "CPX LIST", "RSX LOAD HELLO", "TPAFILL R",
                    "RSXTEST", "RSX UNLOAD HELLO", "CPX LIST")
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-d0", str(disk), "-id", "3000"]
        for command in commands:
            invocation.extend(key_args(command + "\r"))
            invocation.extend(("-id", "3000"))
        invocation.extend(("-it", "-ix"))
        subprocess.run(invocation, cwd=work, check=True)
        screen = (work / "trs80-text-0.bin").read_bytes()[:80 * 24]
        assert screen.count(b"TPA overwrite verified") == 2, screen
        assert b"FAILED" not in screen, screen
        assert b"RSX function 201 returned 5253h" in screen, screen
        assert screen.count(b"BASIC : DIR, ERA, TYPE, REN, SAVE, USER, CLR, VER") == 2, screen
        expected = f"TPA available: {(LAYOUT['TPA'] - 0x100) // 1024}K".encode()
        assert screen.count(expected) == 2, screen
    print("Full TPA overwrite, BDOS survival, CPX reconstruction, and resident RSX survival passed")


if __name__ == "__main__":
    main()
