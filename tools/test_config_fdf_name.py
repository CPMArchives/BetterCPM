#!/usr/bin/env python3
"""Keep a normalized mixed-sector binding tied to its CONFIG catalogue name."""
from pathlib import Path
import tempfile

from test_disk_utilities import run

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    extras = [
        ("FDF.RSX", (ROOT / "build/rsx/FDF.RSX").read_bytes()),
        ("RSX.COM", (ROOT / "build/utilities/RSX.COM").read_bytes()),
    ]
    with tempfile.TemporaryDirectory(prefix="bettercpm-config-fdf-name-") as tmp:
        screens, _, _ = run(
            Path(tmp),
            "identify-super",
            [
                ("RSX LOAD FDF\r", 2500),
                ("CONFIG\r", 2200),
                ("G", 500),
                ("C", 500),
                ("P", 500),
                ("2", 500),
                ("\r", 700),
            ],
            extras=extras,
        )
        line = next(line for line in screens[-1][0].splitlines() if "[ C ]" in line)
        expected = "Montezuma Micro 80T SUPER DS DATA (80T, DS, DD, 880K)"
        assert expected in line, screens[-1][0]
    print("PASS: normalized SUPER binding retains its CONFIG catalogue name")


if __name__ == "__main__":
    main()
