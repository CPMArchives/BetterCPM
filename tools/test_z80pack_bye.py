#!/usr/bin/env python3
"""Execute BYE's confirmation, queries and shutdown/fallback on the Z80 core."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile

from build_z80pack_bye import build, help_text, version_text
from test_usq import SHIM

ROOT = Path(__file__).resolve().parents[1]


def main():
    z80pack = Path.home() / 'projects/git/z80pack'
    with tempfile.TemporaryDirectory(prefix='bettercpm-bye-') as tmp:
        work = Path(tmp)
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h', 'simport.h'):
            shutil.copy2(z80pack/'z80sim/srcsim'/name, work/name)
        shim = SHIM.replace('void io_out(BYTE l, BYTE h, BYTE d) {}', '''
int ports[16], values[16], writes, stop_on_port;
void io_out(BYTE l, BYTE h, BYTE d) {
 if(writes<16) { ports[writes]=l; values[writes]=d; } writes++;
 if(stop_on_port && l==160 && d==128) { cpu_error=IOHALT; cpu_state=ST_STOPPED; }
}''')
        (work/'shim.c').write_text(shim)
        core = z80pack/'z80core'
        subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',
                        str(work/'shim.c'),str(core/'simglb.c'),
                        *map(str,sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
        lib = C.CDLL(str(work/'core.so'))
        mem = (C.c_ubyte*65536).in_dll(lib,'memory')
        regs = {n:C.c_ubyte.in_dll(lib,n) for n in ('A','B','C','D','E','H','L')}
        words = {n:C.c_ushort.in_dll(lib,n) for n in ('SP','PC','IX','IY')}
        writes = C.c_int.in_dll(lib,'writes')
        stop = C.c_int.in_dll(lib,'stop_on_port')
        ports = (C.c_int*16).in_dll(lib,'ports')
        values = (C.c_int*16).in_dll(lib,'values')
        image = build(output=work/'first')
        assert build(output=work/'second') == image
        state = {}

        @C.CFUNCTYPE(None,C.c_int)
        def hook(kind):
            try:
                assert kind == 0
                fn = regs['C'].value
                de = regs['D'].value*256 + regs['E'].value
                state['calls'].append(fn)
                if fn == 9:
                    p = de
                    while mem[p] != 36:
                        state['text'] += chr(mem[p]); p += 1
                    result = 0
                elif fn == 6:
                    assert de & 255 == 255
                    assert state['keys'], 'unexpected input request'
                    result = state['keys'].pop(0)
                else:
                    raise AssertionError(('unexpected BDOS',fn))
                regs['A'].value = result
                for n in ('B','C','D','E','H','L'):
                    regs[n].value = 0xDD
                words['IX'].value = 0xDEAD
                words['IY'].value = 0xCAFE
            except BaseException as error:
                state['error'] = error
                # Escape a failed read rather than spin forever.
                regs['A'].value = 27

        lib.set_hooks.argtypes = [C.c_ushort,C.c_ushort,C.CFUNCTYPE(None,C.c_int)]
        lib.test_run.argtypes = [C.c_ushort,C.c_int]
        lib.set_hooks(5,0xFFFE,hook)
        count = 0

        def run(tail, keys=(), shutdown=False, expected=None, fallback=False):
            nonlocal count
            C.memset(mem,0,65536)
            mem[256:256+len(image)] = image
            # BDOS hook handles services, RET supplies the real call return.
            mem[5] = 0xC9
            mem[0x80] = len(tail)
            mem[0x81:0x81+len(tail)] = tail.encode('ascii')
            low = bytes(mem[:256])
            words['SP'].value = 0xF000
            words['IX'].value = 0x1234
            words['IY'].value = 0x5678
            writes.value = 0
            stop.value = int(not fallback)
            state.update(text='',calls=[],keys=list(keys),error=None)
            result = lib.test_run(256,100000)
            assert state['error'] is None, state['error']
            assert bytes(mem[:256]) == low, tail
            if shutdown:
                assert result < 0 and result != -1000, (tail,result)
                assert writes.value == 2
                assert list(ports[:2]) == [160,160]
                assert list(values[:2]) == [170,128]
                if fallback:
                    pc = words['PC'].value
                    assert mem[pc-1] == 0x76 and mem[pc-2] == 0xF3
            else:
                assert result >= 0 and writes.value == 0, (tail,result)
                assert words['SP'].value == 0xF000
                assert words['IX'].value == 0x1234 and words['IY'].value == 0x5678
            if expected is not None:
                assert state['text'] == expected, (tail,state['text'],expected)
            count += 1

        prompt = 'Exit cpmsim? [y/N] '
        for tail in ('',' ','\t',' '*127):
            for key in (ord('N'),ord('n'),13,10,27,3):
                run(tail,[key],expected=prompt+'N\r\n')
            for key in (ord('Y'),ord('y')):
                run(tail,[key],shutdown=True,expected=prompt+'Y\r\n')
        run('',[0,0,ord('x'),ord('n')],expected=prompt+'\r\n'+prompt+'N\r\n')
        for tail in ('/Y','/y',' /y\t','/Y /Y','\t/y\t/Y', ' '*125+'/y'):
            run(tail,shutdown=True,expected='')
            assert state['calls'] == []
        run('/Y',shutdown=True,expected='',fallback=True)
        run('',[ord('y')],shutdown=True,expected=prompt+'Y\r\n',fallback=True)
        for query, screen in (('/VER',version_text()),('/HELP',help_text())):
            for tail in (query,query.lower(),'X '+query,query+' /Y',
                         '/Y '+query,'/UNKNOWN\t'+query,query+' '+query,
                         ' '*(127-len(query))+query):
                run(tail,expected=screen)
                assert state['calls'] == [9]
        for tail in ('/Y /VER /HELP','/HELP /Y /VER','/VER /HELP X'):
            run(tail,expected=help_text())
        usage = 'Usage: BYE [/Y]\r\nUse BYE /HELP for help.\r\n'
        for tail in ('/YES','/Yx','X','/Y X','/Y /UNKNOWN','/VERIFY','/HELPER',
                     '/HELP.X','X/HELP','/VER/','\x0fVER','/Y\x01','/','/Y /'):
            run(tail,expected=usage)
        lines = help_text().splitlines()
        assert len(lines) <= 23 and max(map(len,lines)) <= 79
        assert all(line == line.rstrip() for line in lines)
        print(f'PASS: {count} assembled BYE cases; confirmation, bypass, query precedence, '
              'invalid tails, preserved caller state, port exit and DI/HALT fallback.')


if __name__ == '__main__':
    main()
