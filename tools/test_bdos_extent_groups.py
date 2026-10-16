#!/usr/bin/env python3
"""Execute production directory comparison with controlled names and EXM groups."""
from pathlib import Path
from test_bios import Z80
from test_unified_bdos import symbols, BASE

ROOT = Path(__file__).resolve().parents[1]


def main():
    image = (ROOT/'build/bdos/bdos.bin').read_bytes()
    labels = symbols()
    # Explicit examples distinguish same physical group from another group,
    # including high EX flags and a wildcard. Name-only paths ignore EX.
    cases = [(0, 0, 1, False), (0, 1, 1, True),
             (1, 0, 1, True), (1, 1, 0, True), (1, 0, 2, False),
             (3, 0, 3, True), (3, 3, 4, False),
             (7, 0, 7, True), (7, 7, 8, False),
             (15, 0, 15, True), (15, 15, 16, False),
             (1, 0x80, 0xE1, True), (1, 0, 0xF0, False),
             (0, ord('?'), 31, True)]
    for length in (11, 12):
        for exm, requested, stored, expected in cases:
            for mismatch in (False, True):
                cpu = Z80(b'')
                cpu.mem[BASE:BASE+len(image)] = image
                fcb, entry = 0x7000, 0x7100
                cpu.mem[fcb:fcb+13] = bytes((0,))+b'ENTRYTSTCOM'+bytes((requested,))
                cpu.mem[entry:entry+13] = bytes((0,))+b'ENTRYTSTCOM'+bytes((stored,))
                if mismatch:
                    cpu.mem[entry+11] = ord('X')  # last name byte, not EX
                cpu.setword(labels['UB_ITFCB'], fcb)
                cpu.mem[labels['UB_ITLEN']] = length
                cpu.mem[labels['UB_DPBC']+4] = exm
                # Stop only at the original comparison's success/failure exits;
                # avoid inventing a disk backend or changing comparison code.
                found, missed = labels['UB_ITFOUND'], labels['UB_ITMISS']
                cpu.mem[found:found+5] = bytes((0x3E, 0, 0xD3, 253, 0xC9))
                cpu.mem[missed:missed+6] = bytes((0xE1, 0x3E, 1, 0xD3, 253, 0xC9))
                result = []
                cpu.port_write = lambda port, value: result.append(value)
                cpu.hl = entry
                initial_sp = cpu.sp
                cpu.run(labels['UB_ITNAME'], limit=10000)
                want = (expected if length == 12 else True) and not mismatch
                assert result == [0 if want else 1], (length, exm, requested, stored, mismatch, result)
                assert cpu.sp == initial_sp, 'comparison unbalanced stack'
    print('PASS: EXM 0/1/3/7/15, same/different groups, EX flags, wildcard, name mismatch and name-only paths')


if __name__ == '__main__':
    main()
