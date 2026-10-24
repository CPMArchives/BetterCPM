#!/usr/bin/env python3
"""Sequential writes eagerly prepare an extent; random writes bypass it."""
from pathlib import Path
from test_bios import Z80
from test_unified_bdos import BASE, symbols

ROOT = Path(__file__).resolve().parents[1]


def main():
    image = (ROOT / 'build/bdos/bdos.bin').read_bytes()
    labels = symbols()
    cases = 0
    for cr in (1,127,128):
        for write_status in (0,1,2,255):
            for growth_status in (0,2,5):
                cpu = Z80(b'')
                cpu.mem[BASE:BASE+len(image)] = image
                cpu.sp, cpu.ix = 0x9000, 0x7000
                cpu.mem[cpu.ix+32] = cr
                # Isolate the successful/failed transfer from extent preparation.
                # Both real helper paths have separate emitted-code regressions.
                start = labels['UB_WCORE']
                cpu.mem[start:start+3] = bytes((0x3e,write_status,0xc9))
                start = labels['UB_NEXTEX']
                cpu.mem[start:start+10] = bytes((0x32,0x00,0x72,0x21,0x01,0x72,0x34,0x3e,growth_status,0xc9))
                initial_sp = cpu.sp
                cpu.run(labels['UB_WRITE'], limit=1000)
                expected = write_status==0 and cr==128
                assert bool(cpu.mem[0x7201]) == expected, (cr,write_status,growth_status)
                if expected: assert cpu.mem[0x7200]==128, 'write selector lost'
                assert cpu.a==write_status, 'growth overwrote the completed transfer status'
                assert cpu.sp==initial_sp and cpu.ix==0x7000
                cases += 1
    random_cases = 0
    for entry in ('UB_RWRITE','UB_RZERO'):
        for requested in (0,1,127):
            for status in (0,2):
                cpu = Z80(b'')
                cpu.mem[BASE:BASE+len(image)] = image
                cpu.sp, cpu.ix = 0x9000, 0x7000
                cpu.mem[0x700c],cpu.mem[0x700e] = 3,1
                record = ((1*32+3)*128)+requested
                cpu.setword(0x7021,record)
                # The requested extent is already active; isolate the transfer
                # and observe actual random-entry positioning and return behavior.
                start = labels['UB_RDECODE']
                cpu.mem[start:start+2] = bytes((0xaf,0xc9))
                start = labels['UB_WCORE']
                cpu.mem[start:start+8] = bytes((0x3e,requested+1,0x32,0x20,0x70,0x3e,status,0xc9))
                start = labels['UB_NEXTEX']
                cpu.mem[start:start+5] = bytes((0x21,0x00,0x72,0x34,0xc9))
                initial_sp = cpu.sp
                cpu.run(labels[entry],limit=1000)
                assert not cpu.mem[0x7200], 'random transfer prepared another extent'
                assert cpu.mem[0x7020]==requested and cpu.mem[0x700c]==3 and cpu.mem[0x700e]==1
                assert cpu.a==status and cpu.sp==initial_sp and cpu.ix==0x7000
                random_cases += 1
    print(f'PASS {cases} sequential boundary/status cases; {random_cases} random position/status cases')


if __name__ == '__main__':
    main()
