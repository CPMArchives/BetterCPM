#!/usr/bin/env python3
"""Directory-full rollover must return 1 without advancing the caller FCB.

Execute production instructions with a private DPB/directory provider. Separate
real-emulator DRI comparisons qualify the public status (sequential 1/random 5).
"""
import contextlib
import io
import test_unified_bdos as foundation


def main():
    captured = []
    original = foundation.Z80
    def capture(*args, **kwargs):
        cpu = original(*args, **kwargs)
        captured.append(cpu)
        return cpu
    foundation.Z80 = capture
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            foundation.main()
    finally:
        foundation.Z80 = original
    cpu, = captured
    labels = foundation.symbols()
    emitted = foundation.IMAGE.read_bytes()
    # Undo the foundation's legacy cache fixture before testing public rollover.
    end = labels['UB_OLDSP'] - foundation.BASE
    cpu.mem[foundation.BASE:labels['UB_OLDSP']] = emitted[:end]
    assert bytes(cpu.mem[foundation.BASE:labels['UB_OLDSP']]) == emitted[:end]
    memory = bytes(cpu.mem)
    sp = cpu.sp
    low = [labels['UB_STKTOP']]
    push = cpu.push
    def guarded_push(value):
        push(value)
        if labels['UB_STACK'] - 64 <= cpu.sp < labels['UB_STKTOP']:
            low[0] = min(low[0],cpu.sp)
            assert cpu.sp >= labels['UB_STACK'], 'private stack overflow'
    cpu.push = guarded_push
    def call(fn, arg=0):
        cpu.ix = 0xA55A
        cpu.c, cpu.de = fn, arg
        cpu.run(foundation.BASE, limit=100000)
        assert cpu.sp == sp and cpu.ix == 0xA55A, ('caller frame', fn)
        return cpu.a
    cases = 0
    for bsh, exm in ((3,0),(4,1)):
        for extent, s2 in ((exm,0),(31,0),(31,63)):
            for clean in (False,True):
                cpu.mem[:] = memory
                call(31)
                dpb = cpu.hl
                cpu.mem[dpb+2:dpb+5] = bytes((bsh,(1<<bsh)-1,exm))
                cpu.setword(dpb+5,31)
                cpu.setword(dpb+7,15)
                cpu.mem[dpb+9:dpb+11] = bytes((0x80,0))
                directory = bytearray(512)
                for n in range(16):
                    offset = n*32
                    directory[offset+1:offset+12] = b'OWNER   DAT' if not n else (f'F{n:07d}'+'DAT').encode()
                directory[12], directory[14], directory[15] = extent,s2,128
                directory[16:32] = bytes(range(1,17))
                cpu.mem[foundation.FIXTURE:foundation.FIXTURE+512] = directory
                call(32,0)
                assert call(13) == 0
                fcb = foundation.FCB
                cpu.mem[fcb:fcb+36] = bytes(36)
                cpu.mem[fcb+1:fcb+12] = b'OWNER   DAT'
                cpu.mem[fcb+12], cpu.mem[fcb+14] = extent,s2
                assert call(15,fcb) != 255
                cpu.mem[fcb+32] = 128
                if not clean:
                    cpu.mem[fcb+14] &= 0x7F
                before = bytes(cpu.mem[fcb:fcb+36])
                assert call(21,fcb) == 1, (bsh,extent,s2,clean)
                assert bytes(cpu.mem[fcb:fcb+36]) == before, 'failed rollover changed FCB'
                assert bytes(cpu.mem[foundation.FIXTURE:foundation.FIXTURE+512]) == directory, 'failed rollover changed directory'
                cases += 1
    print(f'PASS {cases} directory-full/EX-wrap/S2-limit clean and dirty FCB cases')
    print(f'Private stack high-water: {labels["UB_STKTOP"]-low[0]} / {labels["UB_STKTOP"]-labels["UB_STACK"]} bytes')


if __name__ == '__main__':
    main()
