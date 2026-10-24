#!/usr/bin/env python3
"""Exercise the compiled DASM adaptation with the independent full Z80 core."""
import ctypes as C
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from build_dasm import build
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded


class Dasm(Command):
    def callback(self,kind):
        super().callback(kind)
        if self.exception is not None:
            self.reg['PC'].value=0xffff
            self.mem[0xffff]=0x76
            C.c_int.in_dll(self.lib,'cpu_error').value=1

    def __init__(self,library,image,listing):
        super().__init__(library,image,listing,required_symbols=('D_OLDSP','OLDST','D_START','D_STATE'))
        self.symbols.update(UC_STACK=self.symbols['OLDST']-512,
                            UC_STACK_TOP=self.symbols['OLDST'],UC_INPUT=0x5c)

    def bdos(self,fn,de):
        if fn==10:
            if not self.lines:raise AssertionError(('unexpected command input',self.console[-500:]))
            line=self.lines.pop(0).encode()
            assert len(line)<=self.mem[de]
            self.mem[de+1]=len(line)
            self.mem[de+2:de+2+len(line)]=line
            self.mem[de+2+len(line)]=13
            self.console+='\r\n'+line.decode()+'\r\n'
            return 0
        if fn==2:self.console+=chr(self.reg['E'].value);return 0
        if fn==11:return 0
        if fn==1:return ord(self.responses.pop(0))
        if fn==14:self.drive=self.reg['E'].value+1;return 0
        if fn==32:
            if self.reg['E'].value!=255:self.user=self.reg['E'].value
            return self.user
        if fn==35:
            key=self.fcbkey(de)
            if key not in self.files:return 255
            self.mem[de+33:de+36]=((len(self.files[key])+127)//128).to_bytes(3,'little')
            return 0
        if fn==16 and de in self.opened and self.opened[de][0][2].endswith('.$$$'):
            if self.fail('close_output'):return 255
        value=super().bdos(fn,de)
        if fn==17 and value!=255:
            at=self.dma+value*32
            self.mem[at:at+32]=bytes(32)
            self.mem[at+1:at+12]=bytes(self.mem[de+1:de+12])
        return value

    def execute(self,lines,files=None,*,tpa=0xd000,failures=None,responses=()):
        self.lines=list(lines);self.responses=list(responses)
        self.lib.set_hooks(5,0xfffe,self.hook)
        self.files=dict(files or {});self.original=dict(self.files)
        self.drive,self.user=1,0
        self.failures=failures or {};self.late_existing=None
        self.attempts,self.opened,self.searches={},{},{}
        self.events,self.created,self.deleted,self.renamed=[],[],[],[]
        self.dma,self.console,self.exception=0x80,'',None
        self.mem[:]=bytes(65536)
        self.mem[0x100:0x100+len(self.image)]=self.image
        self.mem[5]=0xc9;self.mem[6:8]=tpa.to_bytes(2,'little')
        guard_start=max(tpa,0x100+len(self.image))
        self.mem[guard_start:0xd800]=bytes([0xa5])*max(0,0xd800-guard_start)
        self.reg['SP'].value=0xe000;self.reg['IY'].value=0xbeef
        result=self.lib.test_run(0x100,30000000)
        assert self.exception is None,self.exception
        assert result>=0,('CPU',result,hex(self.reg['PC'].value),self.console[-500:])
        assert self.reg['SP'].value==0xe000
        assert self.reg['IY'].value==0xbeef
        assert (self.drive,self.user,self.dma)==(1,0,0x80)
        assert bytes(self.mem[guard_start:0xd800])==bytes([0xa5])*max(0,0xd800-guard_start), 'resident-memory canary changed'
        assert not self.lines,self.lines
        self.cases+=1
        return self.console


def main():
    z80pack=Path.home()/'projects/git/z80pack';core=z80pack/'z80core'
    with tempfile.TemporaryDirectory(prefix='dasm-test-') as temporary:
        w=Path(temporary);image=build(Path.home()/'bin/z80asm',w)
        (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):shutil.copyfile(z80pack/'z80sim/srcsim'/name,w/name)
        (w/'shim.c').write_text(SHIM)
        subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(w),'-I'+str(core),str(w/'shim.c'),
                        str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        m=Dasm(C.CDLL(str(w/'core.so')),image,(w/'dasm.lst').read_text())
        tiny=diskkey(1,'TINY.COM');out=diskkey(1,'TINY.ASM')
        text=m.execute(['RTINY.COM','L100,106','G'],{tiny:bytes.fromhex('3e21d30200c9')})
        assert 'LD' in text and 'RET' in text,text
        m.intact()
        text=m.execute(['RTINY.COM','N6','STINY.ASM','P100,106','QL100,106','Z','G'],
                       {tiny:bytes.fromhex('3e21d30200c9')})
        assert out in m.files,(text,m.files)
        assert b'ASEG' in m.files[out] and b'END' in m.files[out],m.files[out]
        m.intact()
        for name in ['TINY.COM','A:TINY.COM','A0:TINY.COM']:
            text=m.execute(['RTINY.COM','S'+name,'G'],{tiny:b'\xc9'})
            assert 'aliases' in text or 'Command Error' in text,(name,text)
            m.intact()
        text=m.execute(['RTINY.COM','N2000','G'],{tiny:bytes(8192)})
        assert 'capacity' not in text and 'outside' not in text,text
        for bad_length in ['N0','N2001']:
            text=m.execute(['RTINY.COM',bad_length,'G'],{tiny:bytes(8192)})
            assert 'outside' in text or 'Command Error' in text,text
        for limit in [0x9800,0x97ff]:
            text=m.execute(['G'] if limit==0x9800 else [],tpa=limit)
            assert ('insufficient' in text)==(limit<0x9800),text
        for data in [b'',bytes(8193)]:
            text=m.execute(['RTINY.COM','G'],{tiny:data})
            assert 'outside' in text or 'capacity' in text,text
        text=m.execute(['RTINY.COM','N1','F1234','G'],{tiny:b'\x00'})
        assert 'outside' in text,text
        for bad in [b'0100 START\x1a0101 BAD',b'0100 9BAD\r\n']:
            text=m.execute(['RTINY.SYM','G'],{diskkey(1,'TINY.SYM'):bad})
            assert 'invalid metadata' in text,text
        text=m.execute(['STINY.ALL','G'])
        assert 'unavailable' in text and not m.created,text
        text=m.execute(['L100','G'])
        assert 'outside' in text,text
        for data in [b'0100 START\r\n',b'0000 ZERO\r\nFFFF LAST\r\n']:
            text=m.execute(['RTEST.SYM','DS','G'],{diskkey(1,'TEST.SYM'):data})
            assert 'START' in text or 'ZERO' in text,text
        text=m.execute(['RTINY.COM','STINY.ASM','P100,106','QL100,106','Z','G'],
                       {tiny:b'\xc9',out:b'KEEP'},responses=['Y'])
        assert any(k[2].endswith('.BAK') and v.startswith(b'KEEP') for k,v in m.files.items()),m.files
        text=m.execute([],tpa=0x2000)
        assert 'insufficient' in text,text
        for operation in ['make','write','close_output','rename']:
            for existing in [False,True]:
                files={tiny:bytes.fromhex('3e21d30200c9')}
                if existing:files[out]=b'KEEP'
                text=m.execute(['RTINY.COM','N6','STINY.ASM','P100,106','QL100,106','Z','G'],
                               files,failures={operation:1},responses=['Y'] if existing else [])
                assert out not in m.files or m.files[out]==b'KEEP',(operation,text)
                assert m.files[tiny]==files[tiny]
                if existing:assert m.files[out]==b'KEEP'
        text=m.execute(['RTINY.COM','N6','STINY.ASM','P100,106','QL100,106','Z','G'],
                       {tiny:bytes.fromhex('3e21d30200c9'),out:b'KEEP'},
                       failures={'rename':2},responses=['Y'])
        assert out not in m.files
        assert any(k[2].endswith('.BAK') and v==b'KEEP' for k,v in m.files.items()),m.files
        for name,payload in corpus().items():
            end=256+len(payload)
            text=m.execute(['RTINY.COM',f'N{len(payload):X}','STINY.ASM',f'P100,{end:X}',
                            f'QL100,{end:X}','Z','G'],{tiny:payload})
            assert 'outside' not in text,(name,text[-400:])
            asm=m.files[out].split(b'\x1a',1)[0]
            path=w/(name+'.asm');path.write_bytes(asm)
            result=subprocess.run([str(Path.home()/'bin/z80asm'),'-e12','-fb',
                                   '-o'+str(w/(name+'.bin')),str(path)],capture_output=True)
            assert result.returncode==0,(name,result.stdout,result.stderr,asm)
            rebuilt=(w/(name+'.bin')).read_bytes()
            assert rebuilt==payload,(name,len(payload),len(rebuilt),
                [(i,a,b) for i,(a,b) in enumerate(zip(payload,rebuilt)) if a!=b][:12])
        print('PASS:',m.cases,'DASM full-core command campaigns')


def corpus():
    """Independent byte enumeration, including aliases and unused prefixes."""
    cases={'BASE':b''.join(bytes([n,0,1,0,0,0]) for n in range(256)),
           'CB':b''.join(bytes([0xcb,n,0,0]) for n in range(256)),
           'ED':b''.join(bytes([0xed,n,0,1,0,0]) for n in range(256)),
           'RAW':bytes(range(256))+b"';\r\n\x1a\x00\xff"}
    for prefix,name in [(0xdd,'DD'),(0xfd,'FD')]:
        cases[name]=b''.join(bytes([prefix,n,0x80,1,0,0]) for n in range(256))
        cases[name+'CB']=b''.join(bytes([prefix,0xcb,0x80,n,0,0]) for n in range(256))
    return cases


if __name__=='__main__':main()
