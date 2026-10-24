#!/usr/bin/env python3
"""Execute DSYM on the full Z80 core with hostile BDOS and fault injection."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import tempfile
from build_dsym import build
from dsym_reference import convert, convert_log
from generate_dasm_words import generate
from utility_versions import banner
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


def fixture(raw):
    meaningful,marker,padding=raw.partition(b'\x1a')
    records=[]
    for line in meaningful.splitlines():
        tokens=line.split()
        records.append(b' '.join(tokens[i+1]+b' '+tokens[i] if i+1<len(tokens) else tokens[i]
                                 for i in range(0,len(tokens),2))+b'\r\n')
    return (b'LINK 1.3\n'+b''.join(records)+
        b'ABSOLUTE 0000\r\nCODE SIZE 0000\r\nDATA SIZE 0000\r\nCOMMON SIZE 0000\r\nUSE FACTOR 00\r\nDLINK END\r\n'+
        (b'\x1a'+padding if marker else b''))


class Dsym(Command):
    ro_mask=0
    def callback(self,kind):
        function=self.reg['C'].value
        super().callback(kind)
        if function==29 and self.exception is None:
            self.reg['H'].value=self.ro_mask>>8;self.reg['L'].value=self.ro_mask&255
    def bdos(self, fn, de):
        if fn==29:return self.ro_mask&255
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
        source=diskkey(1,'INPUT.LOG');dest=diskkey(1,'INPUT.DSY')
        def run(data, **kw):return m.run(' INPUT.LOG',{source:fixture(data)},tpa=0xd000,**kw)
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
        text=m.run(' INPUT.LOG',{source:fixture(b'0100 START\n'),dest:b'KEEP'},tpa=0xd000)
        assert 'exists' in text and m.files[dest]==b'KEEP'
        m.intact()
        text=m.run(' INPUT.LOG',{source:fixture(b'0100 START\n')},tpa=0x1000)
        assert 'insufficient' in text and not m.created
        text=m.run('/VER',{},tpa=0xd000)
        assert banner('DSYM') in text and not m.created
        text=run(b'0100 FIRST\r\n0101 SECOND\r\n0100 first\n')
        assert 'imported 2; coalesced 1; rejected 0; complete' in text,text
        text=run(b'0100 FIRST\r\n\r\n0101 9BAD\n')
        assert 'invalid symbols at line 4' in text,text
        report=(b'LINK 1.3 \n\r\r\nSTART    0100   HELLO    0104   \r\n\r\n'
                b'ABSOLUTE     0000\r\nCODE SIZE    0004 (0100-0103)\r\n'
                b'DATA SIZE    0001 (0104-0104)\r\nCOMMON SIZE  0000\r\n'
                b'USE FACTOR     00\r\nDLINK END\r\n')
        log_source=diskkey(1,'INPUT.LOG')
        text=m.run(' INPUT.LOG',{log_source:report},tpa=0xd000)
        assert 'complete' in text and m.files[dest]==padded(convert_log(report)),text
        for bad in (report.replace(b'1.3',b'1.2'),report.replace(b'0100-0103',b'0100-0104'),
                    report.replace(b'START    0100',b'UNDEFINED SYMBOLS: START    0100'),
                    report.replace(b'START    0100',b'MULTIPLE DEFINITION: START    0100'),
                    report.replace(b'DLINK END',b''),report+b'EXTRA',
                    report[:report.index(b'USE FACTOR')],
                    b'0100 START\r\n',report.replace(b'CODE SIZE',b'CODE ERROR')):
            text=m.run(' INPUT.LOG',{log_source:bad},tpa=0xd000)
            assert 'invalid' in text and dest not in m.files,text
            try:convert_log(bad)
            except ValueError:pass
            else:raise AssertionError(('reference accepted malformed report',bad))
        for caller in (0,7,31):
            for srcuser,dstuser in ((0,31),(16,7),(31,0)):
                src=diskkey(2,'INPUT.LOG',srcuser); dst=diskkey(3,'INPUT.DSY',dstuser)
                decoy=diskkey(3,'INPUT.DSY',caller)
                files={src:fixture(b'0100 START\n')}
                if decoy!=dst:files[decoy]=b'KEEP'
                text=m.run(f' B{srcuser}:INPUT.LOG C{dstuser}:',files,user=caller,tpa=0xd000)
                assert 'complete' in text,text
                assert m.files[dst]==padded(b'0100 START\r\n\x1a')
                m.intact()
        for arg in ('B32:INPUT.LOG','[B0,B1]:INPUT.LOG','B0:INPUT.LOG [C0,C1]:',
                    'B0:INPUT.LOG C0:EXTRA','B0:INPUT.LOG C0: EXTRA'):
            text=m.run(' '+arg,{diskkey(2,'INPUT.LOG'):fixture(b'0100 START\n')},tpa=0xd000)
            assert 'Usage:' in text and not m.created,(arg,text)
        for fail in ('open','read','make','write','close_input','close_output','rename'):
            src=diskkey(2,'INPUT.LOG',31)
            text=m.run(' B31:INPUT.LOG C16:',{src:fixture(b'0100 START\n')},user=7,tpa=0xd000,failures={fail:1})
            assert 'complete' not in text and diskkey(3,'INPUT.DSY',16) not in m.files
            m.intact()
        for count in (255,256):
            data=b''.join(f'{i:04X} NAME{i:04X}\n'.encode() for i in range(count))
            text=run(data)
            assert ('complete' in text)==(count==255),text
            if count==255:assert m.files[dest]==padded(convert(data))
            else:assert dest not in m.files
        for query in ('/ver',' /VER  ','X /VER','/VER X','/VER /VER','FILE\t/vEr'):
            text=m.run(query,{},user=31,tpa=0x6000)
            assert banner('DSYM') in text and not m.created,text
        m.ro_mask=4
        text=m.run(' B31:INPUT.LOG C16:',{diskkey(2,'INPUT.LOG',31):fixture(b'0100 START\n')},user=7,tpa=0xd000)
        assert 'destination drive is read-only' in text and not m.created,text
        m.ro_mask=0
        text=m.run(' INPUT.SYM',{diskkey(1,'INPUT.SYM'):b'0100 START\r\n'},tpa=0xd000)
        assert 'cannot prove link success' in text and not m.created,text
        print('PASS:',m.cases,'DSYM full-core cases; validation, aliases, low TPA, failures and original preservation')


if __name__=='__main__':main()
