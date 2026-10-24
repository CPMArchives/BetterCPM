#!/usr/bin/env python3
"""Execute DSYM on the full Z80 core with hostile BDOS and fault injection."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_dsym import build
from dsym_reference import convert
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


def main():
    z80pack=Path.home()/'projects/git/z80pack';core=z80pack/'z80core'
    with tempfile.TemporaryDirectory(prefix='dsym-test-') as temporary:
        w=Path(temporary)
        image=build(Path.home()/'bin/z80asm',w)
        (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):shutil.copyfile(z80pack/'z80sim/srcsim'/name,w/name)
        (w/'shim.c').write_text(SHIM)
        subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(w),'-I'+str(core),str(w/'shim.c'),
                        str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        m=Command(C.CDLL(str(w/'core.so')),image,(w/'dsym.lst').read_text(),
                  required_symbols=('UC_OLDSP','UC_STACK','UC_STACK_TOP','UC_INPUT','UC_TEMP'))
        source=diskkey(1,'INPUT.SYM');dest=diskkey(1,'INPUT.DSY')
        def run(data, **kw):return m.run(' INPUT.SYM',{source:data},tpa=0xd000,**kw)
        raw=b'0100 START\t0104 HELLO\t\r\n\x1a'
        assert 'complete' in run(raw),m.console
        assert m.files[dest]==padded(convert(raw)), repr(m.files[dest])
        m.intact()
        for raw in [b'0100 LOWER\n0100 lower\n',b'0000 ZERO\rFFFF LAST',b'1234 A\t1234 B']:
            assert 'complete' in run(raw),m.console
            m.intact()
        for raw in [b'0100',b'010Z BAD',b'0100 9BAD',b'0100 TOOLONGSYMBOLX',
                    b'0100 SAME\n0101 SAME',b'0100 A\x1a0101 B',b'100 A',b'10000 A',
                    b'0100 A;INJECT',b'0100 A\x80',b'\x00']:
            assert 'invalid' in run(raw),m.console
            assert dest not in m.files
            m.intact()
        for fail in ['open','read','make','write','close_input','close_output','rename']:
            assert 'complete' not in run(b'0100 START\n',failures={fail:1}),fail
            assert dest not in m.files,(fail,m.files)
            m.intact()
        text=m.run(' INPUT.SYM',{source:b'0100 START\n',dest:b'KEEP'},tpa=0xd000)
        assert 'exists' in text and m.files[dest]==b'KEEP'
        m.intact()
        text=m.run(' INPUT.SYM',{source:b'0100 START\n'},tpa=0x1000)
        assert 'insufficient' in text and not m.created
        text=m.run('/VER',{},tpa=0xd000)
        assert 'DSYM development' in text and not m.created
        print('PASS:',m.cases,'DSYM full-core cases; validation, aliases, low TPA, failures and original preservation')


if __name__=='__main__':main()
