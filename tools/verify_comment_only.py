#!/usr/bin/env python3
"""Check that source edits changed comments/blank lines only relative to Git."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTENSIONS = {".mac", ".inc", ".sub"}


def strip_comment(line: str) -> str:
    """Keep quoted semicolons, including doubled quote escapes."""
    quote = None
    index = 0
    while index < len(line):
        char = line[index]
        if quote:
            if char == quote:
                if index + 1 < len(line) and line[index + 1] == quote:
                    index += 2
                    continue
                quote = None
        elif char in ("'", '"'):
            quote = char
        elif char == ";":
            return line[:index]
        index += 1
    return line


def executable_lines(source: str) -> list[str]:
    return [code for line in source.splitlines()
            if (code := strip_comment(line).rstrip()).strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", help="Git revision containing original source")
    args = parser.parse_args()
    paths = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", args.baseline, "src"],
        cwd=ROOT, text=True).splitlines()
    changed = []
    checked = 0
    for name in paths:
        path = ROOT / name
        if path.suffix.lower() not in EXTENSIONS or not path.exists():
            continue
        checked += 1
        baseline = subprocess.check_output(
            ["git", "show", f"{args.baseline}:{name}"], cwd=ROOT, text=True)
        current = path.read_text(encoding="ascii")
        if executable_lines(baseline) != executable_lines(current):
            changed.append(name)
    if changed:
        for name in changed:
            print(f"executable source differs: {name}")
        return 1
    print(f"Executable source unchanged in {checked} source files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
