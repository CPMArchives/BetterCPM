#!/usr/bin/env python3
"""Rebuild every resident/layout-dependent component before creating a disk."""
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = (
    "fdf_catalog",
    "bdos", "ccp", "ccpreload", "rcp_cpx", "hello_cpx",
    "hello_rsx", "echo_rsx", "fdf_rsx", "p2dos_rsx", "frehd_time_rsx", "zprtc_rsx",
    "test_service_rsx", "svctest",
    "stateful_test_rsx", "stattst",
    "rsxloader", "rsxresolver",
    "rsx_runtime_overlays", "fileloader", "system", "utilities",
    "trs80_boot", "system_package",
)
if __name__ == "__main__":
    for component in COMPONENTS:
        subprocess.run([sys.executable, str(ROOT / "tools" / f"build_{component}.py")],
                       cwd=ROOT, check=True)
    # The ROM/RAM ownership inventory is tied to emitted symbol addresses. Run
    # its drift check only after every resident listing has been regenerated.
    subprocess.run([sys.executable,
                    str(ROOT / "tools/test_rom_ownership_inventory.py"),
                    "--platform", "trs80"],
                   cwd=ROOT, check=True)
