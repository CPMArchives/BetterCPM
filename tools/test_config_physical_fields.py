#!/usr/bin/env python3
"""Exercise CONFIG's constrained physical-drive field controls."""
from pathlib import Path
import tempfile

from build_ccp import assemble
from test_disk_utilities import run


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bettercpm-config-fields-") as tmp:
        work = Path(tmp)
        detach = assemble(
            Path.home() / "bin/z80asm",
            """        ASEG
        ORG 100H
        LD SP,4000H
        LD B,4
        LD C,181
        LD DE,REQ
        CALL 5
        JP 0
REQ:    DB 1,0FFH
        DS 78
        END
""",
            work / "DETACH.COM", work / "detach.lst", 0x100,
        )
        screens, _, _ = run(
            work, "physical-fields",
            [
                ("DETACH\r", 1800),
                ("CONFIG\r", 2200),
                ("F", 500),
                ("B", 500),
                ("A", 700),
                ("A", 700),
                ("C", 700),
                ("C", 700),
                ("B", 500),
                ("\x03", 400),
                ("D", 500),
            ],
            extras=[("DETACH.COM", detach)],
        )
        first_toggle = screens[4][0]
        second_toggle = screens[5][0]
        assert "Type of drive (inches):     8" in first_toggle, first_toggle
        assert "Type of drive (inches):     5" in second_toggle, second_toggle
        assert "Number of sides:            1" in screens[6][0], screens[6][0]
        assert "Number of sides:            2" in screens[7][0], screens[7][0]
        assert "Track choices:" in screens[8][0], screens[8][0]
        assert "Step rate choices (ms):" in screens[10][0], screens[10][0]
    print("CONFIG physical toggles and constrained selection lists passed")


if __name__ == "__main__":
    main()
