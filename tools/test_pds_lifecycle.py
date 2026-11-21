#!/usr/bin/env python3
"""Execute the real cold/warm PDS worker against controlled BIOS records."""
from pathlib import Path
from pds_layout import header, layout
from startup_record import build, choices
from system_layout import LAYOUT as L
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]


def machine(record):
    cpu = Z80(b'')
    cpu.mem[:] = b'\xa5'*65536
    worker = (ROOT/'build/pds/worker.bin').read_bytes()
    cpu.mem[0x1700:0x1700+len(worker)] = worker
    cpu.mem[L['SYSTEM']+0x95] = 0
    cpu.mem[L['RSX_STATE']] = 0
    cpu.sp = 0x1000
    cpu.mem[L['BDOS']:L['BDOS']+3] = b'\xd3\x00\xc9'
    for offset in (27, 30, 33, 36, 39):
        cpu.mem[L['BIOS']+offset:L['BIOS']+offset+3] = bytes((0xd3, offset, 0xc9))
    io = dict(sector=0, dma=0, reads=0, messages=[])

    def bios(port, _value):
        port &= 255
        if port == 0:
            assert cpu.c in (9, 13)
            if cpu.c == 9:
                io['messages'].append(bytes(cpu.mem[cpu.de:cpu.mem.index(36,cpu.de)]))
            cpu.a = 0
        elif port == 27:
            cpu.hl = 1
        elif port == 33:
            io['sector'] = cpu.bc
        elif port == 36:
            io['dma'] = cpu.bc
        elif port == 39:
            at = (io['sector']-1)*128
            cpu.mem[io['dma']:io['dma']+128] = record[at:at+128]
            io['reads'] += 1
            cpu.a = 0
        else:
            assert port == 30
    cpu.port_write = bios
    return cpu, io


def main():
    for h, m, v in ((2,0,0),(0,0,0),(1,0,0),(3,0,0),(2,1,1),(3,1,3)):
        record = build('DIR', system_base=L['SYSTEM'], history=h, mcl=m, variables=v)
        assert choices(record, system_base=L['SYSTEM']) == (h,m,v)
        cpu, io = machine(record)
        bootstrap=bytes(cpu.mem[0x100:0x500])
        cpu.run(0x1700, limit=100000)
        assert bytes(cpu.mem[0x100:0x500])==bootstrap, 'cold record read overwrote the reloader'
        expected = header(h,m,v)
        actual = bytes(cpu.mem[L['SYSTEM']-12:L['SYSTEM']])
        assert actual == expected, (h,m,v,actual.hex(),expected.hex())
        plan = layout(actual, L['SYSTEM'])
        assert cpu.word(6) == plan['low']-3
        payload=bytearray(plan['total']-12)
        if h:payload[:6]=b'BH\x01\x00\x00\x00'
        assert bytes(cpu.mem[plan['low']:L['SYSTEM']-12])==payload
        assert cpu.mem[L['SYSTEM']+0x95] == 2
        assert io['reads'] == 2 and not io['messages']
        # A warm pass must not consult saved settings or reset owner payload.
        cpu.mem[plan['low']:L['SYSTEM']-12] = b'\x5a'*(plan['total']-12)
        if h:
            at=plan['low']
            cpu.mem[at:at+6]=b'BH\x01\x01\x04\x00'
            cpu.mem[at+10:at+14]=b'\x03DIR'
        before = bytes(cpu.mem[plan['low']:L['SYSTEM']])
        cpu.run(0x1700, limit=100000)
        assert cpu.z and io['reads'] == 2
        assert bytes(cpu.mem[plan['low']:L['SYSTEM']]) == before
        if h:
            # Damaged packed HISTORY resets only that owner's control block.
            outside=bytes(cpu.mem[plan['low']+plan['owners']['HISTORY'][1]:L['SYSTEM']])
            cpu.mem[plan['low']+10]=128
            cpu.run(0x1700, limit=100000)
            assert cpu.z and bytes(cpu.mem[plan['low']:plan['low']+6])==b'BH\x01\x00\x00\x00'
            assert bytes(cpu.mem[plan['low']+plan['owners']['HISTORY'][1]:L['SYSTEM']])==outside
            assert io['messages'][-1]==b'History reset.\r\n'
        # Corrupt live metadata fails closed; it cannot silently recompose.
        cpu.mem[L['SYSTEM']-2] ^= 1
        cpu.run(0x1700, limit=100000)
        assert not cpu.z and io['reads'] == 2
        assert b'cold boot required' in io['messages'][-1]
    legacy = build('DIR', system_base=L['SYSTEM'], version=1)
    cpu, io = machine(legacy)
    cpu.run(0x1700, limit=100000)
    assert bytes(cpu.mem[L['SYSTEM']-12:L['SYSTEM']]) == header()
    bad = bytearray(legacy); bad[12] ^= 1
    cpu, io = machine(bytes(bad))
    cpu.run(0x1700, limit=100000)
    assert bytes(cpu.mem[L['SYSTEM']-12:L['SYSTEM']]) == header()
    assert b'defaults' in io['messages'][0]
    print('PASS PDS cold composition, exact owner bounds, zero-owner case, warm preservation, corrupt-live rejection, BCST1 and saved fallback')


if __name__ == '__main__':
    main()
