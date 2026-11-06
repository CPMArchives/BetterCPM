#!/usr/bin/env python3
"""Execute carrier capsule allocation, snapshots and offline streams on Z80."""
from pathlib import Path
import struct
from build_rsx_runtime_overlays import build, ROOT
from build_rsx_module import make_module
from system_layout import LAYOUT
from test_bios import Z80


def main():
    assembler = Path.home()/'bin/z80asm'
    base = LAYOUT['RSX']-1024
    helper = build(assembler, 'r3cache', 'r3cache.mac', 'CBBASE', base)
    snapshot = build(assembler, 'r3snapshot', 'r3snap.mac', 'RNBASE', LAYOUT['CONFIG'])
    assert len(helper) <= 1024
    for nreloc in (0, 1, 128, 232):
        code = bytearray(max(32, 8+2*nreloc))
        relocations = list(range(8, 8+2*nreloc, 2))
        for at in relocations:
            struct.pack_into('<H', code, at, 0x8008)
        carrier = make_module(name='OFFLINE', version=(1, 0), services=[198],
                              linked_base=0x8000, code=bytes(code), relocations=relocations)
        cpu = Z80(b'')
        cpu.mem[base:base+len(helper)] = helper
        cpu.mem[LAYOUT['CONFIG']:LAYOUT['CONFIG']+len(snapshot)] = snapshot
        source, facts, request, output = 0x2000, 0x3000, 0x3100, 0x5000
        cpu.mem[source:source+len(carrier)] = carrier
        old_allocation = struct.unpack_from('<H', carrier, 14)[0]
        cpu.setword(facts+4, old_allocation)
        cpu.hl, cpu.de, cpu.sp = source, facts, 0x4000
        cpu.run(base+9, 50000)
        assert cpu.a == 0
        allocation = cpu.word(facts+4)
        compact = 48+2*nreloc+len(carrier)-512
        assert allocation == old_allocation+((compact+28+255)&~255)
        patched = bytes(cpu.mem[source:source+len(carrier)])
        assert cpu.word(source+14) == old_allocation
        patched = bytearray(patched)
        struct.pack_into('<H', patched, 14, allocation)
        patched = bytes(patched)
        req = struct.pack('<HHHHHHHHBBHHBBB', source+512, len(code), allocation,
                          0x8000, output, source+48, nreloc, 0, 0, 2,
                          output, 8, 0xCC, 1, 3)
        assert len(req) == 25
        cpu.mem[request:request+25] = req
        cpu.de = request
        cpu.run(LAYOUT['CONFIG'], 100000)
        assert cpu.a == 0 and cpu.mem[request+22] == 1
        footer = output+allocation-8
        assert cpu.mem[footer+6:footer+8] == b'RC'
        assert cpu.mem[footer+4:footer+6] == bytes((1, 3))
        assert cpu.word(footer+2) == compact
        # Publish a live profile and destroy its original carrier in RAM.
        cpu.setword(LAYOUT['SYSTEM']+0x84, output)
        cpu.mem[LAYOUT['RSX_STATE']] = 1
        cpu.mem[LAYOUT['RSX_STATE']+1:LAYOUT['RSX_STATE']+9] = b'OFFLINE '
        cpu.mem[source:source+len(carrier)] = bytes(len(carrier))
        cpu.mem[0x1800:0x1808] = b'OFFLINE '
        cpu.hl, cpu.a = 0x1800, 1
        cpu.run(base, 10000)
        assert cpu.a == 0
        cpu.run(base+15, 1000)
        assert cpu.bc == 0x0301
        recovered = bytearray()
        for offset in range(0, len(patched), 512):
            cpu.hl = 0x6000
            cpu.run(base+3, 100000)
            assert cpu.a == 0 and cpu.hl == 0x6200
            recovered.extend(cpu.mem[0x6000:0x6200])
        assert recovered[:len(patched)] == patched, nreloc
        # The provider's original allocation is the pointer ownership bound;
        # a fixed external value in the loader-owned capsule stays external.
        for offset in (0, old_allocation-1, old_allocation, allocation-1):
            cpu.hl, cpu.bc = offset, output
            cpu.run(base+18, 1000)
            assert cpu.carry == (offset < old_allocation), offset
        cpu.hl = 0x6000
        cpu.run(base+3, 10000)
        assert cpu.a == 255
        cpu.run(base+6, 1000)
        cpu.hl = 0x6000
        cpu.run(base+3, 100000)
        assert cpu.mem[0x6000:0x6200] == patched[:512]
    print('PASS offline capsule streams, relative offsets, source DU, page boundaries, EOF/reset and pristine relocation templates')


if __name__ == '__main__':
    main()
