#!/usr/bin/env python3
"""Qualify stateful RSX reconstruction and rollback on both 1.0 platforms."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from run_trs80_command import DEFAULT_EMULATOR, ROOT, key_args

TRS_IMAGE = ROOT / "build/trs80/BetterCPM-Extended-80T-DS-System-790K.dmk"
DEFAULT_Z80 = ROOT / "build/z80pack"
DEFAULT_CPMSIM = Path.home() / "projects/git/z80pack/cpmsim/cpmsim"

SUCCESS = (
    ("RSX LOAD HELLO", ()),
    ("RSX LOAD STATEFUL", ()),
    ("STATTST I", ("STATEFUL INIT PASS",)),
    ("STATTST M", ("STATEFUL MUTATE PASS",)),
    ("RSX UNLOAD HELLO", ()),
    ("STATTST C", ("STATEFUL CHECK PASS",)),
    ("WARM", ()),
    ("STATTST C", ("STATEFUL CHECK PASS",)),
)

ROLLBACK = (
    ("RSX LOAD HELLO", ()),
    ("RSX LOAD STATEFUL", ()),
    ("STATTST I", ("STATEFUL INIT PASS",)),
    ("STATTST M", ("STATEFUL MUTATE PASS",)),
    ("ERA R3RESOL.RSX", ()),
    ("RSX UNLOAD HELLO", ("RSX module or profile error",)),
    ("STATTST C", ("STATEFUL CHECK PASS",)),
    ("RSX LIST", ("HELLO", "STATEFUL")),
)


def tcl_quote(text: str) -> str:
    """Quote controlled ASCII text as one Tcl braced word."""
    if any(character in text for character in "{}"):
        raise ValueError(f"unsupported Tcl text: {text!r}")
    return "{" + text + "}"


def run_cpmsim(image: Path, simulator: Path,
               commands: tuple[tuple[str, tuple[str, ...]], ...],
               label: str) -> None:
    with tempfile.TemporaryDirectory(prefix=f"bettercpm-stage3-{label}-") as tmp:
        work = Path(tmp)
        shutil.copytree(image / "disks", work / "disks")
        lines = [
            "set timeout 30",
            "set send_slow {1 .02}",
            "log_file -noappend [lindex $argv 2]",
            "expect_before timeout {puts {TEST TIMEOUT}; exit 1}",
            "proc prompt {} {",
            " expect {",
            "  -exact {A0>_ } {}",
            "  timeout {puts {PROMPT TIMEOUT}; exit 1}",
            "  eof {puts {UNEXPECTED EXIT}; exit 1}",
            " }",
            "}",
            "spawn [lindex $argv 0] -z -d [lindex $argv 1]",
            "expect -exact {Booting...}",
            "prompt",
        ]
        for command, expected in commands:
            lines.append(f'send -s -- "{command}\\r"')
            for item in expected:
                lines.append(f"expect -exact {tcl_quote(item)}")
            lines.append("prompt")
        lines.extend(('send -s -- "BYE\\r"', "expect eof"))
        script = work / "stage3.exp"
        script.write_text("\n".join(lines) + "\n")
        environment = dict(os.environ)
        environment["PATH"] = (str(simulator.parent / "srctools") +
                               os.pathsep + environment["PATH"])
        result = subprocess.run(
            ["expect", str(script), str(simulator), str(work / "disks"),
             str(work / "transcript.txt")],
            cwd=work, env=environment, capture_output=True, text=True,
            timeout=240,
        )
        if result.returncode:
            transcript = (work / "transcript.txt").read_text(
                errors="replace") if (work / "transcript.txt").exists() else ""
            raise AssertionError(
                f"cpmsim {label} qualification failed:\n{transcript[-5000:]}\n"
                f"{result.stdout[-3000:]}"
                f"\n{result.stderr[-1000:]}"
            )


def trs_screen(commands: tuple[tuple[str, tuple[str, ...]], ...]) -> bytes:
    with tempfile.TemporaryDirectory(prefix="bettercpm-stage3-trs80-") as tmp:
        work = Path(tmp)
        disk = work / TRS_IMAGE.name
        disk.write_bytes(TRS_IMAGE.read_bytes())
        invocation = [str(DEFAULT_EMULATOR), "-m4", "-batch", "-turbo",
                      "-d0", str(disk), "-id", "3000"]
        for index, (command, _) in enumerate(commands):
            if index:
                invocation.extend(("-id", "12000"))
            invocation.extend(key_args(command + "\r"))
        invocation.extend(("-id", "1800", "-it", "-ix"))
        subprocess.run(invocation, cwd=work, check=True)
        return (work / "trs80-text-0.bin").read_bytes()[:80 * 24]


def require_ordered(screen: bytes, expected: tuple[bytes, ...], label: str) -> None:
    position = 0
    for item in expected:
        position = screen.find(item, position)
        if position < 0:
            rows = "\n".join(screen[offset:offset + 80].decode(
                "ascii", errors="replace").rstrip()
                for offset in range(0, len(screen), 80))
            raise AssertionError(f"trs80gp {label} lacks {item!r}:\n{rows}")
        position += len(item)


def run_trs80(commands: tuple[tuple[str, tuple[str, ...]], ...], label: str) -> None:
    expected = tuple(item.encode("ascii") for _, items in commands for item in items)
    require_ordered(trs_screen(commands), expected, label)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=("all", "cpmsim", "trs80gp"),
                        default="all")
    parser.add_argument("--image-dir", type=Path, default=DEFAULT_Z80)
    parser.add_argument("--simulator", type=Path, default=DEFAULT_CPMSIM)
    args = parser.parse_args()

    if args.platform in ("all", "cpmsim"):
        image = args.image_dir.expanduser().resolve()
        simulator = args.simulator.expanduser().resolve()
        for path in (image / "disks", simulator):
            if not path.exists():
                raise SystemExit(f"missing cpmsim qualification input: {path}")
        run_cpmsim(image, simulator, SUCCESS, "success")
        run_cpmsim(image, simulator, ROLLBACK, "rollback")
        print("cpmsim stateful relocation, warm boot, and rollback passed")

    if args.platform in ("all", "trs80gp"):
        for path in (DEFAULT_EMULATOR, TRS_IMAGE):
            if not path.is_file():
                raise SystemExit(f"missing trs80gp qualification input: {path}")
        run_trs80(SUCCESS, "success")
        run_trs80(ROLLBACK, "rollback")
        print("trs80gp stateful relocation, warm boot, and rollback passed")


if __name__ == "__main__":
    main()
