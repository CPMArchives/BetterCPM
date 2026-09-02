#!/usr/bin/env python3
"""Verify the proof RSX's load, intercept, warm-boot, and unload lifecycle."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def run(commands: tuple[str, ...]) -> bytes:
    with tempfile.TemporaryDirectory(prefix="bettercpm-rsx-manager-") as temporary:
        disk = Path(temporary, IMAGE.name)
        disk.write_bytes(IMAGE.read_bytes())
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-d0", str(disk), "-id", "3000"]
        for index, command in enumerate(commands):
            if index:
                invocation.extend(("-id", "2500"))
            invocation.extend(key_args(command + "\r"))
        invocation.extend(("-id", "1800", "-it", "-ix"))
        subprocess.run(invocation, cwd=temporary, check=True)
        return Path(temporary, "trs80-text-0.bin").read_bytes()[:80 * 24]


def require_ordered(screen: bytes, expected: tuple[bytes, ...]) -> None:
    position = 0
    for item in expected:
        position = screen.find(item, position)
        if position < 0:
            raise SystemExit(f"RSX workflow lacks {item!r}: {screen!r}")
        position += len(item)


def main() -> None:
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing RSX manager test input: {path}")

    first = run(("RSXTEST", "RSX LIST", "RSX LOAD HELLO.RSX", "RSX LIST",
                 "RSXTEST"))
    require_ordered(first, (
        b"RSX function 201 unsupported", b"No RSXs loaded",
        b"TPA available: 47K", b"HELLO : BDOS 201",
        b"TPA available: 46K", b"Hello from HELLO.RSX",
        b"RSX function 201 returned 5253h",
    ))

    second = run(("RSX LOAD HELLO", "RSXTEST", "HELLO WARM", "RSXTEST",
                  "RSX UNLOAD HELLO.RSX", "RSX LIST", "RSXTEST"))
    require_ordered(second, (
        b"Hello from HELLO.RSX", b"RSX function 201 returned 5253h",
        b"Hello from BetterCP/M WARM", b"Hello from HELLO.RSX",
        b"RSX function 201 returned 5253h", b"No RSXs loaded",
        b"TPA available: 47K", b"RSX function 201 unsupported",
    ))
    print("RSX load/intercept/WBOOT/unload and TPA-boundary restoration passed")


if __name__ == "__main__":
    main()
