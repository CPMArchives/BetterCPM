#!/usr/bin/env python3
"""Exercise the emitted FCB activation routine across grouped subextents."""
from test_unified_bdos import IMAGE, BASE, symbols
from test_bios import Z80


def main():
    state = symbols()
    cases = 0
    for mask in (0, 1, 3, 7):
        for requested in range(8):
            for populated in range(8):
                if requested & ~mask != populated & ~mask:
                    continue
                for records in (0, 1, 127, 128):
                    cpu = Z80(b'')
                    cpu.mem[BASE:BASE + len(IMAGE.read_bytes())] = IMAGE.read_bytes()
                    cpu.sp = 0xa000
                    fcb, entry = 0x7000, 0x7100
                    original = bytearray(36)
                    original[0] = 2
                    original[12] = requested
                    original[32:36] = bytes((19, 123, 45, 0))
                    directory = bytearray(range(32))
                    directory[12] = populated
                    directory[14] = 3
                    directory[15] = records
                    cpu.mem[fcb:fcb + 36] = original
                    cpu.mem[entry:entry + 32] = directory
                    cpu.ix = fcb
                    cpu.setword(state['UB_ITFCB'], fcb)
                    cpu.setword(state['UB_OPENENT'], entry)
                    cpu.mem[state['UB_ITRET']] = 2
                    # Isolate activation after a successful directory lookup.
                    cpu.mem[state['UB_OPENCORE']:state['UB_OPENCORE'] + 2] = bytes((0xaf, 0xc9))
                    cpu.run(state['UB_ACTIVATE'])
                    expected = bytearray(directory + bytes(4))
                    expected[0] = original[0]
                    expected[12] = requested
                    expected[14] |= 128
                    expected[15] = records if populated == requested else (128 if populated > requested else 0)
                    expected[32:36] = original[32:36]
                    assert cpu.mem[fcb:fcb + 36] == expected, (mask, requested, populated, records)
                    assert cpu.a == 2 and not cpu.carry
                    cases += 1
    print(f'Grouped FCB activation preserves EX/CR, normalizes RC and retains attributes/maps: {cases} cases')


if __name__ == '__main__':
    main()
