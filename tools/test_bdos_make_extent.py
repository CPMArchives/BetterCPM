#!/usr/bin/env python3
"""Function 22 must distinguish a new physical extent from a duplicate."""
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
    state = foundation.symbols()
    emitted = foundation.IMAGE.read_bytes()
    end = state['UB_OLDSP'] - foundation.BASE
    # Restore the complete instruction prefix, including public cache invalidation.
    cpu.mem[foundation.BASE:state['UB_OLDSP']] = emitted[:end]
    memory = bytes(cpu.mem)
    initial_sp = cpu.sp
    lowest = [state['UB_STKTOP']]
    push = cpu.push
    def guarded(value):
        push(value)
        if state['UB_STACK']-64 <= cpu.sp < state['UB_STKTOP']:
            lowest[0] = min(lowest[0], cpu.sp)
            assert cpu.sp >= state['UB_STACK'], 'private stack overflow'
    cpu.push = guarded
    def call(fn, arg=0):
        cpu.ix = 0xa55a
        cpu.c, cpu.de = fn, arg
        cpu.run(foundation.BASE, limit=100000)
        assert cpu.sp == initial_sp and cpu.ix == 0xa55a, ('caller frame', fn)
        return cpu.a
    cases = 0
    for bsh, exm, dsm in ((3,0,31),(4,1,31),(4,0,399),(5,1,399),(5,3,31)):
        for user in (0,7,31):
            for old_ex, old_s2 in ((0,0),(31,0),(0,1)):
                for relation in ('same','same-group','next-group','other-s2','other-user'):
                    cpu.mem[:] = memory
                    call(31)
                    dpb = cpu.hl
                    cpu.mem[dpb+2:dpb+5] = bytes((bsh,(1<<bsh)-1,exm))
                    cpu.setword(dpb+5,dsm)
                    cpu.setword(dpb+7,15)
                    cpu.mem[dpb+9:dpb+11] = bytes((0x80,0))
                    directory = bytearray(b'\xe5'*512)
                    entry = bytearray(32)
                    entry[0] = (user+1)%32 if relation=='other-user' else user
                    entry[1:12] = b'OWNER   DAT'
                    entry[12], entry[14], entry[15] = old_ex,old_s2,128
                    blocks = (((old_ex&exm)+1)*16384 + (128<<bsh)-1)//(128<<bsh)
                    width = 2 if dsm>255 else 1
                    for n in range(blocks):
                        entry[16+n*width:16+(n+1)*width] = (n+2).to_bytes(width,'little')
                    directory[:32] = entry
                    cpu.mem[foundation.FIXTURE:foundation.FIXTURE+512] = directory
                    call(32,user)
                    assert call(13)==0
                    fcb = foundation.FCB
                    data = bytearray(36)
                    data[1:12] = b'OWNER   DAT'
                    data[12], data[14] = old_ex, old_s2
                    if relation=='same-group': data[12] ^= exm
                    if relation=='next-group': data[12] ^= exm+1
                    if relation=='other-s2': data[14] ^= 1
                    # Reused FCB scratch must not become a new allocation map.
                    data[15:32] = b'\xa5'*17
                    cpu.mem[fcb:fcb+36] = data
                    status = call(22,fcb)
                    admitted = relation in ('next-group','other-s2','other-user')
                    assert (status!=255)==admitted, (bsh,exm,dsm,user,old_ex,old_s2,relation,status)
                    cached = cpu.word(state['UB_DIRBUF'])
                    assert bytes(cpu.mem[cached:cached+32]) == entry, 'existing extent changed'
                    if admitted:
                        assert status==1
                        assert bytes(cpu.mem[fcb+15:fcb+32])==bytes(17)
                        assert cpu.mem[fcb+12]==data[12] and cpu.mem[fcb+14]==(data[14]|128)
                        new = bytes(cpu.mem[cached+32:cached+64])
                        assert new[:12]==bytes((user,))+b'OWNER   DAT'
                        assert new[12]==data[12] and new[14]==data[14]
                        assert new[15:32]==bytes(17)
                    else:
                        assert bytes(cpu.mem[fcb:fcb+36])==data
                        assert bytes(cpu.mem[cached:cached+128])==directory[:128]
                    cases += 1
    print(f'PASS {cases} Make cases: 8/16-bit maps, EXM groups, S2, users, duplicates and reused FCBs')
    print(f'Private stack high-water: {state["UB_STKTOP"]-lowest[0]} / {state["UB_STKTOP"]-state["UB_STACK"]} bytes')


if __name__ == '__main__':
    main()
