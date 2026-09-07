#!/usr/bin/env python3
"""Rebuild every resident/layout-dependent component before creating a disk."""
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = (
    "bdos", "ccp", "ccpreload", "basic_cpx", "hello_cpx", "basic_transients",
    "warm", "cpx_utility", "hello_rsx", "echo_rsx", "rsx_utilities", "rsxloader",
    "fileloader", "era", "ren", "type", "system", "disk_utilities", "trs80_boot",
)
if __name__ == "__main__":
    for component in COMPONENTS:
        subprocess.run([sys.executable, str(ROOT / "tools" / f"build_{component}.py")],
                       cwd=ROOT, check=True)
