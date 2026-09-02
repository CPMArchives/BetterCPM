#!/usr/bin/env python3
"""Verify runtime BASIC.CPX list, unload, and reload in one boot session."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def main() -> None:
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing CPX manager test input: {path}")
    commands = (
        "CPX LIST", "CPX UNLOAD BASIC", "CPX LIST", "TYPE",
        "CPX LOAD BASIC", "CPX LIST", "TYPE",
    )
    with tempfile.TemporaryDirectory(prefix="bettercpm-cpx-manager-") as temporary:
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-d0", str(IMAGE), "-id", "1200"]
        for index, command in enumerate(commands):
            if index:
                invocation.extend(("-id", "1400"))
            invocation.extend(key_args(command + "\r"))
        invocation.extend(("-id", "2500", "-it", "-ix"))
        subprocess.run(invocation, cwd=temporary, check=True)
        screen = Path(temporary, "trs80-text-0.bin").read_bytes()[:80 * 24]
    ordered = (
        b"A>CPX LIST", b"BASIC : DIR, ERA, TYPE, REN",
        b"TPA available: 47K", b"A>CPX UNLOAD BASIC",
        b"No CPXs loaded", b"TPA available: 47K", b"A>TYPE", b"?",
        b"A>CPX LOAD BASIC", b"BASIC : DIR, ERA, TYPE, REN",
        b"TPA available: 47K", b"A>TYPE", b"TYPE filename",
    )
    position = 0
    for expected in ordered:
        position = screen.find(expected, position)
        if position < 0:
            raise SystemExit(f"CPX manager workflow lacks {expected!r}: {screen!r}")
        position += len(expected)
    print("CPX.COM list/unload/reload and WBOOT reconstruction passed")


if __name__ == "__main__":
    main()
