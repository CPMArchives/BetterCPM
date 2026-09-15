#!/usr/bin/env python3
"""Verify physical-first CONFIG changes detach incompatible bindings."""
from pathlib import Path
import tempfile

from test_disk_utilities import run


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bettercpm-physical-first-") as tmp:
        screens, _, _ = run(
            Path(tmp), "physical-first",
            [
                ("CONFIG\r", 2200),
                ("F", 500),
                ("B", 500),
                ("B", 500),
                ("A", 900),       # physical drive 1: 80 tracks -> 35
                ("\x03", 400),
                ("\x03", 400),
                ("G", 700),
            ],
        )
        changed = screens[4][0]
        listing = screens[7][0]
        assert "Number of tracks:          35" in changed, changed
        assert "Incompatible logical drive binding unconfigured" in changed, changed
        line = next(line for line in listing.splitlines() if "[ B ]" in line)
        assert "Undefined disk drive" in line, listing
        assert "Montezuma Micro" not in line, listing
    print("CONFIG physical-first invalidation and explicit unconfigured state passed")


if __name__ == "__main__":
    main()
