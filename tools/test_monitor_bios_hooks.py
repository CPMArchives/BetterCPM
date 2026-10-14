#!/usr/bin/env python3
"""Execute production BIOS monitor hooks with a bounded synthetic provider.

Provider loading is deliberately not exercised: RSX transaction integration is
separate. This verifies the primitive on which that integration will depend.
"""
import argparse
from pathlib import Path
from test_monitor_profiles import load
from system_layout import LAYOUT

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--z80pack-build', type=Path)
    args = parser.parse_args()
    cpu, labels = load(args.z80pack_build or ROOT / 'build/bios')
    output = []
    cpu.port_write = lambda port, value: output.append((port & 255, value))
    base = LAYOUT['BIOS']
    for name, offset in [('BIOCHCAP', 63), ('MONCALL', 66),
                         ('MONRAW', 69), ('MONBASE', 72)]:
        assert labels[name] == base + offset
        assert cpu.mem[base + offset] == 0xC3
    cpu.mem[3] = 0x55
    cpu.run(labels['MONBASE'])
    cell, raw = labels['MP_MON'], labels['MC_RAW']
    assert cpu.word(cell) == raw
    # Callback records operation/input and returns an intentionally noncanonical
    # status/high-bit input, exercising the public wrappers' normalization.
    provider = 0x8000
    code = bytes((0x32, 0, 0x82, 0x79, 0x32, 1, 0x82, 0x3E, 0xFE, 0xC9))
    cpu.mem[provider:provider + len(code)] = code
    cpu.setword(cell, provider)
    for offset, op, result in [(12, 0, 0xFE), (6, 1, 0xFF),
                               (9, 2, 0x7E), (54, 3, 0xFE), (15, 0, 0xFE)]:
        cpu.c = ord('X')
        initial_sp = cpu.sp
        cpu.run(base + offset)
        assert cpu.mem[0x8200:0x8202] == bytes((op, ord('X'))), (offset, bytes(cpu.mem[0x8200:0x8202]))
        assert cpu.a == result and cpu.sp == initial_sp
    for op in (4, 5):
        cpu.a = op
        cpu.run(labels['MONCALL'])
        assert cpu.mem[0x8200] == op
    # Raw output bypasses the provider, and detach makes its old storage safe
    # to reuse without leaving a dangling callback.
    cpu.mem[0x8200] = 0xCC
    cpu.a, cpu.c = 0, ord('A')
    cpu.run(labels['MONRAW'])
    assert cpu.mem[0x8200] == 0xCC
    assert output == [(1, ord('A'))] if args.z80pack_build else cpu.mem[0xF800] == ord('A')
    cpu.run(labels['MONBASE'])
    cpu.mem[provider:provider + len(code)] = b'\xff' * len(code)
    cpu.c = ord('B')
    cpu.run(base + 12)
    assert output[-1] == (1, ord('B')) if args.z80pack_build else cpu.mem[0xF801] == ord('B')
    before = bytes(cpu.mem[0xF800:0xFF80])
    cpu.a = 5
    cpu.run(labels['MONCALL'])
    assert bytes(cpu.mem[0xF800:0xFF80]) == before
    cpu.a = 6
    cpu.run(labels['MONRAW'])
    assert cpu.a == 0xFF
    print('PASS: production monitor vectors, routed console/list/cursor,')
    print('normalized input/status, raw bypass, detach fallback and reset no-op')


if __name__ == '__main__':
    main()
