#!/usr/bin/env python3
"""Run CP/M 2.2 SUBMIT/XSUB workflows on private TRS-80 disk images."""
from __future__ import annotations

import subprocess
import tempfile
import re
from pathlib import Path

from add_cpm_file_to_dmk import extract_raw
from build_ccp import assemble
from build_trs80_boot import DIRECTORY_ENTRIES, FILESYSTEM_FIRST_SECTOR, SECTOR_SIZE
from run_trs80_command import DEFAULT_EMULATOR, key_args
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
ASSEMBLER = Path("/Users/nathanael/bin/z80asm")


def screen(path: Path) -> str:
    data = path.read_bytes()[:80 * 24]
    return "\n".join(bytes(value & 0x7F for value in data[index:index + 80])
                     .decode("ascii", "replace").rstrip()
                     for index in range(0, len(data), 80))


def no_submit_file(image: Path) -> bool:
    raw = extract_raw(image.read_bytes())
    start = FILESYSTEM_FIRST_SECTOR * SECTOR_SIZE
    for index in range(DIRECTORY_ENTRIES):
        entry = raw[start + index * 32:start + (index + 1) * 32]
        if entry[0] < 32 and entry[1:12] == b"$$$     SUB":
            return False
    return True


def marker(temporary: Path) -> bytes:
    source = """        ORG 0100H
        LD DE,PREFIX
        LD C,9
        CALL 5
        LD A,(0080H)
        LD B,A
        LD HL,0081H
MORE:   LD A,B
        OR A
        JR Z,DONE
        PUSH BC
        PUSH HL
        LD E,(HL)
        LD C,2
        CALL 5
        POP HL
        POP BC
        INC HL
        DJNZ MORE
DONE:
        LD DE,NL
        LD C,9
        CALL 5
        RET
PREFIX: DB 'MARK:','$'
NL:     DB 13,10,'$'
        END
"""
    return assemble(ASSEMBLER, source, temporary / "MARK.COM",
                    temporary / "mark.lst", 0x100)


def pending_probe(temporary: Path) -> bytes:
    """Seed the protected console-pending byte, then return through WBOOT."""
    listing = (ROOT / "build/bdos/bdos.lst").read_text()
    matches = re.findall(r"^([0-9a-f]{4})\s+.*\bUB_PENDING:",
                         listing, re.MULTILINE | re.IGNORECASE)
    if not matches:
        raise SystemExit("cannot locate UB_PENDING in current BDOS listing")
    source = f"""        ORG 0100H
        LD A,'X'
        LD (0{int(matches[-1], 16):04X}H),A
        RET
        END
"""
    return assemble(ASSEMBLER, source, temporary / "PENDING.COM",
                    temporary / "pending.lst", 0x100)


def full_program(temporary: Path, xsub: bool) -> bytes:
    if xsub:
        source = """        ORG 0100H
        LD SP,0500H
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
GOOD:   DB 13,10,'FULLIN OK',13,10,'$'
FAIL:   DB 13,10,'FULLIN FAILED',13,10,'$'
        END
"""
        name, ceiling = "FULLIN", LAYOUT["RSX"] - 512 - 3
    else:
        source = """        ORG 0100H
        LD DE,GOOD
        LD C,9
        CALL 5
        RET
GOOD:   DB 13,10,'FULLTPA OK',13,10,'$'
        END
"""
        name, ceiling = "FULLTPA", LAYOUT["TPA"]
    code = assemble(ASSEMBLER, source, temporary / f"{name}.COM",
                    temporary / f"{name.lower()}.lst", 0x100)
    size = ((ceiling - 0x100) // 128) * 128
    if len(code) > 128:
        raise SystemExit(f"{name} probe no longer fits its first record")
    return code.ljust(size, b"\0")


def build_image(temporary: Path, name: str, files: dict[str, bytes]) -> Path:
    arguments = []
    for filename, content in files.items():
        path = temporary / filename
        path.write_bytes(content)
        arguments.extend(("--include-as", f"{filename}={path}"))
    image = temporary / f"{name}.dmk"
    subprocess.run(["python3", str(ROOT / "tools/build_trs80_boot.py"),
                    *arguments, "--output", str(image)], cwd=ROOT,
                   check=True, stdout=subprocess.DEVNULL)
    return image


def run(temporary: Path, image: Path, command: str, delay: int = 20000) -> str:
    work = temporary / (image.stem + "-run")
    work.mkdir()
    invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                  "-d0", str(image), "-id", "4000", *key_args(command + "\r"),
                  ]
    invocation.extend(("-id", str(delay), "-it", "-ix"))
    subprocess.run(invocation, cwd=work, check=True, timeout=180,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    captures = sorted(work.glob("trs80-text-*.bin"))
    if not captures:
        raise SystemExit("trs80gp produced no SUBMIT/XSUB capture")
    return screen(captures[-1])


def ordered(text: str, expected: tuple[str, ...]) -> None:
    position = 0
    for item in expected:
        position = text.find(item, position)
        if position < 0:
            raise SystemExit(f"batch screen lacks {item!r}:\n{text}")
        position += len(item)


def main() -> None:
    for path in (ASSEMBLER, DEFAULT_EMULATOR):
        if not path.is_file():
            raise SystemExit(f"missing batch-test dependency: {path}")
    # Boot-image construction deliberately rejects a resident assembled against
    # an older BIOS.  Start from one coherent snapshot of the current tree.
    subprocess.run(["python3", str(ROOT / "tools/build_complete_system.py")],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix="bettercpm-submit-xsub-") as name:
        temporary = Path(name)
        mark = marker(temporary)
        pending = pending_probe(temporary)

        # The last source line deliberately has no CR: CP/M text EOF must still
        # submit it. FULLTPA overwrites all reclaimable CCP/CPX bytes before RET.
        order = build_image(temporary, "order", {
            "MARK.COM": mark,
            "FULLTPA.COM": full_program(temporary, False),
            "ORDER.SUB": b"FULLTPA\r\nMARK $1\r\nMARK $$2\r\nMARK LAST",
        })
        result = run(temporary, order, "SUBMIT ORDER FIRST")
        ordered(result, ("FULLTPA OK", "MARK: FIRST", "MARK: $2", "MARK: LAST"))
        if not no_submit_file(order):
            raise SystemExit("ORDER left A:$$$.SUB after EOF")

        # This maximum active-XSUB image also overwrites CCP/CPX, then receives
        # its Function-10 record from protected BATCHIO and returns through WBOOT.
        xsub = build_image(temporary, "xsub", {
            "MARK.COM": mark,
            "FULLIN.COM": full_program(temporary, True),
            "XFULL.SUB": b"XSUB\r\nFULLIN\r\nBATCHFULL\r\nMARK AFTER",
        })
        result = run(temporary, xsub, "SUBMIT XFULL")
        ordered(result, ("(xsub active)", "FULLIN OK", "MARK: AFTER"))
        if not no_submit_file(xsub):
            raise SystemExit("XSUB left A:$$$.SUB after EOF")

        bad = build_image(temporary, "bad", {
            "MARK.COM": mark,
            "BAD.SUB": b"NOEXIST\r\nMARK SHOULDNOT",
            "PARM.SUB": b"MARK $X",
        })
        result = run(temporary, bad, "SUBMIT BAD")
        if "?" not in result or "SHOULDNOT" in result or not no_submit_file(bad):
            raise SystemExit(f"bad submitted command did not cancel/clean up:\n{result}")

        cancel = build_image(temporary, "cancel", {
            "MARK.COM": mark,
            "PENDING.COM": pending,
            "CANCEL.SUB": b"PENDING\r\nMARK SHOULDNOT",
        })
        result = run(temporary, cancel, "SUBMIT CANCEL")
        if "MARK: SHOULDNOT" in result or not no_submit_file(cancel):
            raise SystemExit(f"console cancellation did not remove the stream:\n{result}")
        # A new private image keeps this utility-error case independent.
        parm = build_image(temporary, "parm", {"PARM.SUB": b"MARK $X"})
        result = run(temporary, parm, "SUBMIT PARM")
        if "Parameter Error" not in result or not no_submit_file(parm):
            raise SystemExit(f"parameter error contract failed:\n{result}")

    print("SUBMIT ordering/substitution/EOF/error cleanup and full-TPA WBOOT passed")
    print("XSUB protected Function-10 input and post-overwrite command continuation passed")


if __name__ == "__main__":
    main()
