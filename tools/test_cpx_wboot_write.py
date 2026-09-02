#!/usr/bin/env python3
"""Verify physical writes after runtime CPX reconstruction and WBOOT."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def main() -> None:
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing CPX write test input: {path}")
    commands = ("CPX LOAD HELLO", "CPX LIST", "HELLOX", "HELLO TOM",
                "ERA HELLO.COM", "DIR")
    with tempfile.TemporaryDirectory(prefix="bettercpm-cpx-write-") as temporary:
        disk = Path(temporary, IMAGE.name)
        disk.write_bytes(IMAGE.read_bytes())
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-d0", str(disk), "-id", "3000"]
        for index, command in enumerate(commands):
            if index:
                invocation.extend(("-id", "2500"))
            invocation.extend(key_args(command + "\r"))
        invocation.extend(("-id", "2200", "-it", "-ix"))
        subprocess.run(invocation, cwd=temporary, check=True)
        screen = Path(temporary, "trs80-text-0.bin").read_bytes()[:80 * 24]
    ordered = (
        b"BASIC : DIR, ERA, TYPE, REN, SAVE", b"HELLO : HELLO",
        b"A0>HELLOX", b"?",
        b"A0>HELLO TOM", b"Hello from HELLO.CPX TOM",
        b"A0>ERA HELLO.COM", b"A0>DIR", b"CPX      COM", b"A0>",
    )
    position = 0
    for expected in ordered:
        position = screen.find(expected, position)
        if position < 0:
            raise SystemExit(f"CPX/WBOOT write workflow lacks {expected!r}: {screen!r}")
        position += len(expected)
    if b"HELLO    COM" in screen[screen.find(b"A0>DIR"):]:
        raise SystemExit("HELLO.COM remained after ERA in CPX/WBOOT write test")
    print("runtime CPX reconstruction preserved physical directory writes")


if __name__ == "__main__":
    main()
