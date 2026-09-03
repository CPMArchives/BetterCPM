#!/usr/bin/env python3
"""Report actual packed protected memory, including every reserved workspace."""
from pathlib import Path
from build_system import COMPONENTS, BUILD
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]
RESERVATIONS = (
    ("Persistent history", LAYOUT["HISTORY"], 512),
    ("Dynamic gateway (no RSXs)", LAYOUT["TPA"], 3),
    ("Active RSX table", LAYOUT["RSX_STATE"], 41),
    ("Reload/CCP stack", LAYOUT["STACK_LOW"], LAYOUT["STACK_TOP"] - LAYOUT["STACK_LOW"]),
    ("Directory buffer", LAYOUT["DIRBUF"], 128),
    ("Physical/module buffer", LAYOUT["MODULEBUF"], 512),
)


def ranges():
    result = [(Path(path).name, base, (BUILD / path).stat().st_size)
              for base, path in COMPONENTS]
    return sorted(result + list(RESERVATIONS), key=lambda item: item[1])


def main():
    entries = ranges()
    end = LAYOUT["TPA"]
    occupied = 0
    print("Protected range    Bytes  Component")
    for name, base, size in entries:
        if base < end:
            raise SystemExit(f"overlap at {base:04X}h: {name}")
        if base > end:
            print(f"{end:04X}..{base-1:04X}     {base-end:4}  Padding")
        print(f"{base:04X}..{base+size-1:04X}     {size:4}  {name}")
        end = base + size
        occupied += size
    assert end <= LAYOUT["CEILING"]
    span = LAYOUT["CEILING"] - LAYOUT["TPA"]
    tpa = LAYOUT["TPA"] - 0x100
    print(f"Occupied/reserved: {occupied}; protected span: {span}; padding: {span-occupied}")
    print(f"TPA: {tpa} bytes = {tpa // 1024}K + {tpa % 1024} bytes")
    print(f"Recovered from previous BDFDh gateway: {LAYOUT['TPA'] - 0xBDFD} bytes")
    print(f"Further reduction for 56K TPA: {56 * 1024 - tpa} bytes")
    print("CPXs/CCP share the TPA; installed RSXs subtract their actual allocations.")


if __name__ == "__main__":
    main()
