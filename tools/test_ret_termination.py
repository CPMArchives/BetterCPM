#!/usr/bin/env python3
"""Prove that entry RET bypasses the public page-zero WBOOT gateway."""
from pathlib import Path
import subprocess
import tempfile

from build_ccp import assemble
from run_trs80_command import DEFAULT_EMULATOR, key_args

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bettercpm-ret-") as temporary:
        work = Path(temporary)
        source = """        ORG 100H
        LD HL,(1)
        LD (OLD+1),HL
        LD DE,HOOK
        LD (1),DE
        RET
HOOK:   LD DE,MSG
        LD C,9
        CALL 5
OLD:    JP 0
MSG:    DB 13,10,'RET INVOKED WBOOT',13,10,'$'
        END
"""
        assemble(Path("/Users/nathanael/bin/z80asm"), source,
                 work / "RETPATH.COM", work / "retpath.lst", 0x100)
        image = work / "ret-test.dmk"
        subprocess.run([
            "python3", str(ROOT / "tools/build_trs80_boot.py"),
            "--include-as", f"RETPATH.COM={work / 'RETPATH.COM'}",
            "--output", str(image),
        ], cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
        command = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                   "-d0", str(image), "-id", "3500"]
        for text in ("RETPATH", "VER"):
            command += key_args(text + "\r") + ["-id", "6500", "-it"]
        command += ["-ix"]
        subprocess.run(command, cwd=work, check=True, timeout=180,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        screens = []
        for path in sorted(work.glob("trs80-text-*.bin")):
            data = path.read_bytes()[:1920]
            rows = [bytes(value & 127 for value in data[pos:pos + 80])
                    .decode("ascii", errors="replace").rstrip()
                    for pos in range(0, 1920, 80)]
            screens.append("\n".join(rows))
        transcript = "\n\n--- SCREEN ---\n\n".join(screens)
        if "RET INVOKED WBOOT" in transcript:
            raise AssertionError("entry RET passed through the public WBOOT vector")
        if "BetterCP/M" not in transcript or transcript.count("A0>") < 2:
            raise AssertionError("entry RET did not restore a usable CCP")
    print("PASS: entry RET bypasses page-zero WBOOT and restores the CCP (0509).")


if __name__ == "__main__":
    main()
