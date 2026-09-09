#!/usr/bin/env python3
"""Build the complete BetterCP/M command-utility collection.

This is the canonical entry point for programs which an operator invokes as
ordinary .COM files.  Individual builders remain useful during development;
keeping the collection here prevents boot-image builders and release notes
from acquiring different ideas of what constitutes the BetterCP/M tool set.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Ordered roughly as an operator meets the programs: system management,
# standard CP/M commands, information, then batch processing.  Some builders
# emit more than one command, and BUILD_BATCH also emits BATCHIO.RSX because
# XSUB cannot be built or tested sensibly without its protected companion.
BUILDERS = (
    "disk_utilities",       # CONFIG.COM, DUP.COM, SYSGEN.COM
    "cpx_utility",          # CPX.COM
    "rsx_utilities",        # RSX.COM and its diagnostic companions
    "rcp_transients",       # DIR.COM, USER.COM, CLR.COM, VER.COM
    "era",
    "ren",
    "type",
    "warm",
    "stat",
    "batch",                # SUBMIT.COM, XSUB.COM, BATCHIO.RSX
)


def main() -> None:
    for name in BUILDERS:
        subprocess.run(
            [sys.executable, str(ROOT / "tools" / f"build_{name}.py")],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
