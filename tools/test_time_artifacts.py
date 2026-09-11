#!/usr/bin/env python3
"""Focused structural and calendar checks for TIME.COM and clock providers."""
from __future__ import annotations

import datetime
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def provider_day(year: int, month: int, day: int) -> int:
    """Independent model of the 2000..2099 provider conversion."""
    if not 2000 <= year <= 2099:
        raise ValueError(year)
    return (datetime.date(year, month, day) - datetime.date(1977, 12, 31)).days


def main() -> None:
    utility = (ROOT / "build/utilities/TIME.COM").read_bytes()
    for filename, name in (("FREHDCLK.RSX", b"FREHDCLK"),
                           ("ZPRTC.RSX", b"ZPRTC   ")):
        carrier = (ROOT / "build/rsx" / filename).read_bytes()
        fields = struct.unpack_from("<4sBBBBHHHHHHHHHHHH8sBBBBHH", carrier)
        magic, version = fields[0], fields[1]
        code_size, allocation, primary = fields[7], fields[8], fields[-1]
        assert magic == b"BRSX" and version == 1
        assert fields[17] == name
        assert primary == 208 and allocation >= code_size
        assert allocation % 256 == 0
    assert utility[:3] == b"\xc3\x03\x01"
    assert b"TIME" in utility and b"/PROVIDER" in utility

    known = {
        (2000, 1, 1): 8036,
        (2000, 2, 29): 8095,
        (2001, 1, 1): 8402,
        (2026, 9, 12): 17787,
        (2099, 12, 31): 44560,
    }
    for date, expected in known.items():
        assert provider_day(*date) == expected, (date, provider_day(*date))
    print("TIME artifacts, provider carriers, ABI markers, and known dates passed")


if __name__ == "__main__":
    main()
