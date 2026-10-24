#!/usr/bin/env python3
"""Execute DSYM on the full Z80 core with hostile BDOS and fault injection."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_dsym import build
from dsym_reference import convert
from generate_dasm_words import generate
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


class Dsym(Command):
    def bdos(self, fn, de):
        if fn==2:self.console+=chr(de & 255);return 0
        if fn==32:
            if de & 255 !=255:self.user=de & 255
            return self.user
        if fn in (16,20,21) and de in self.opened:
            assert self.user==self.opened[de][0][1], ('FCB in wrong user',fn,self.user,self.opened[de])
        return super().bdos(fn,de)

    def run(self,*args,**kw):
        result=super().run(*args,**kw)
        assert self.user==kw.get('user',0)
        return result


def main():
    generate(check=True)
    z80pack=Path.home()/'projects/git/z80pack';core=z80pack/'z80core'
    with tempfile.TemporaryDirectory(prefix='dsym-test-') as temporary:
        w=Path(temporary)
        image=build(Path.home()/'bin/z80asm',w)
        (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):shutil.copyfile(z80pack/'z80sim/srcsim'/name,w/name)
        (w/'shim.c').write_text(SHIM)
        subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(w),'-I'+str(core),str(w/'shim.c'),
                        str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        m=Dsym(C.CDLL(str(w/'core.so')),image,(w/'dsym.lst').read_text(),
                  required_symbols=('UC_OLDSP','UC_STACK','UC_STACK_TOP','UC_INPUT','UC_TEMP'))
        source=diskkey(1,'INPUT.SYM');dest=diskkey(1,'INPUT.DSY')
        def run(data, **kw):return m.run(' INPUT.SYM',{source:data},tpa=0xd000,**kw)
        raw=b'0100 START\t0104 HELLO\t\r\n\x1a'
        assert 'complete' in run(raw),m.console
        assert m.files[dest]==padded(convert(raw)), repr(m.files[dest])
        m.intact()
        for raw in [b'0100 LOWER\n0100 lower\n',b'0000 ZERO\rFFFF LAST',b'1234 ALIAS\t1234 SECOND']:
            assert 'complete' in run(raw),m.console
            assert m.files[dest]==padded(convert(raw)),(raw,m.files[dest])
            m.intact()
        for raw in [b'0100',b'010Z BAD',b'0100 9BAD',b'0100 TOOLONGSYMBOLX',
                    b'0100 SAME\n0101 SAME',b'0100 GOOD\x1a0101 OTHER',b'100 A',b'10000 A',
                    b'0100 GOOD;INJECT',b'0100 GOOD\x80',b'\x00',b'0100 LD',b'0100 HL',b'0100 MACRO']:
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
        text=run(b'0100 FIRST\r\n0101 SECOND\r\n0100 first\n')
        assert 'imported 2; coalesced 1; rejected 0; complete' in text,text
        text=run(b'0100 FIRST\r\n\r\n0101 9BAD\n')
        assert 'invalid symbols at line 3' in text,text
        for caller in (0,7,31):
            for srcuser,dstuser in ((0,31),(16,7),(31,0)):
                src=diskkey(2,'INPUT.SYM',srcuser); dst=diskkey(3,'INPUT.DSY',dstuser)
                decoy=diskkey(3,'INPUT.DSY',caller)
                files={src:b'0100 START\n'}
                if decoy!=dst:files[decoy]=b'KEEP'
                text=m.run(f' B{srcuser}:INPUT.SYM C{dstuser}:',files,user=caller,tpa=0xd000)
                assert 'complete' in text,text
                assert m.files[dst]==padded(b'0100 START\r\n\x1a')
                m.intact()
        for arg in ('B32:INPUT.SYM','[B0,B1]:INPUT.SYM','B0:INPUT.SYM [C0,C1]:',
                    'B0:INPUT.SYM C0:EXTRA','B0:INPUT.SYM C0: EXTRA'):
            text=m.run(' '+arg,{diskkey(2,'INPUT.SYM'):b'0100 START\n'},tpa=0xd000)
            assert 'Usage:' in text and not m.created,(arg,text)
        for fail in ('open','read','make','write','close_input','close_output','rename'):
            src=diskkey(2,'INPUT.SYM',31)
            text=m.run(' B31:INPUT.SYM C16:',{src:b'0100 START\n'},user=7,tpa=0xd000,failures={fail:1})
            assert 'complete' not in text and diskkey(3,'INPUT.DSY',16) not in m.files
            m.intact()
        print('PASS:',m.cases,'DSYM full-core cases; validation, aliases, low TPA, failures and original preservation')


if __name__=='__main__':main()
