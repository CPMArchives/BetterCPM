#!/usr/bin/env python3
"""Exercise newly completed BASIC.CPX and transient command paths."""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT

IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"


def run(command: str, *responses: str) -> str:
    arguments = [
        "python3", str(ROOT / "tools/run_trs80_command.py"), command,
        "--emulator", str(DEFAULT_EMULATOR), "--image", str(IMAGE),
        "--boot-delay", "3000", "--run-delay", "3500",
    ]
    for response in responses:
        arguments.extend(("--response", f"3000:{response}\\r"))
    return subprocess.run(arguments, cwd=ROOT, check=True,
                          capture_output=True, text=True).stdout


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    for path in (DEFAULT_EMULATOR, IMAGE):
        if not path.is_file():
            raise SystemExit(f"missing completed-command test input: {path}")

    output = run("CPX LIST")
    require("BASIC : DIR, ERA, TYPE, REN, SAVE, USER, CLR, VER" in output,
            "CPX LIST did not publish the completed BASIC inventory")

    output = run("USER 5")
    require("A5>" in output, "resident USER did not select user 5")
    output = run("A:USER 7")
    require("A7>" in output, "transient USER.COM did not select user 7")

    output = run("VER")
    require("BetterCP/M 0.3" in output, "resident VER did not report the version")
    output = run("VER /V")
    for line in (
        "Command environment: API 1.0; implementation 1.1",
        "Basic Disk Operating System: API 1.1; implementation 1.2",
        "Basic Input/Output System: API 1.0; implementation 1.1",
    ):
        require(line in output, f"resident VER /V omitted {line}")
    require("Extension facility" not in output,
            "VER /V reported manager-owned CPX/RSX versions")
    output = run("A:VER")
    require("BetterCP/M 0.3" in output, "transient VER.COM did not match VER")
    output = run("A:VER /V")
    require("Basic Disk Operating System: API 1.1; implementation 1.2" in output,
            "transient VER.COM did not share verbose subsystem reporting")

    output = run("A:DIR")
    require("DIR      COM" in output and "USER     COM" in output and
            "CLR      COM" in output and "VER      COM" in output,
            "transient DIR.COM did not list the completed command files")

    # A drive-qualified name bypasses the transitional core command and proves
    # the ordinary CLR.COM fallback. Its success is a clean screen and prompt.
    output = run("A:CLR")
    require("A0>" in output and "A:CLR" not in output,
            "transient CLR.COM did not clear the screen and restore the prompt")

    output = run("A:WARM")
    require(output.count("A0>") >= 2,
            "transient WARM.COM did not complete through a fresh prompt")

    print("completed BASIC commands and DIR/USER/CLR/VER/WARM transients passed")


if __name__ == "__main__":
    main()
