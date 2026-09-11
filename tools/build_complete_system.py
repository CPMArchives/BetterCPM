#!/usr/bin/env python3
"""Rebuild every resident/layout-dependent component before creating a disk."""
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = (
    "bdos", "ccp", "ccpreload", "rcp_cpx", "hello_cpx",
    "hello_rsx", "echo_rsx", "fdf_rsx", "frehd_time_rsx", "rsxloader",
    "fileloader", "system", "utilities", "trs80_boot",
)
if __name__ == "__main__":
    for component in COMPONENTS:
        subprocess.run([sys.executable, str(ROOT / "tools" / f"build_{component}.py")],
                       cwd=ROOT, check=True)
