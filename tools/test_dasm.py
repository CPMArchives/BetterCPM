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
from generate_dasm_words import generate


class Dasm(Command):
    def callback(self,kind):
        super().callback(kind)
        if self.exception is not None:
            self.reg['PC'].value=0xffff
            self.mem[0xffff]=0x76
            C.c_int.in_dll(self.lib,'cpu_error').value=1

    def __init__(self,library,image,listing):
        super().__init__(library,image,listing,required_symbols=('D_OLDSP','OLDST','D_START','D_STATE'))
        boundary=re.search(r'^([0-9a-f]{4}).*\bD_MEM_END\s+EQU',listing,re.M|re.I)
        assert boundary
        self.minimum_tpa=int(boundary[1],16)+256
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
        if fn==11:return 255 if self.break_keys else 0
        if fn==1:return ord((self.break_keys if self.break_keys else self.responses).pop(0))
        if fn==14:self.drive=self.reg['E'].value+1;return 0
        if fn==32:
            if self.reg['E'].value!=255:self.user=self.reg['E'].value
            return self.user
        if fn==35:
            key=self.fcbkey(de)
            if key not in self.files:return 255
            self.mem[de+33:de+36]=((len(self.files[key])+127)//128).to_bytes(3,'little')
            return 0
        if fn in (16,20,21) and de in self.opened:
            assert self.opened[de][0][1]==self.user,('wrong user for open FCB',fn,self.user,self.opened[de])
        if fn==16 and de not in self.opened and de in self.closed_fcb:
            key=self.fcbkey(de)
            if key!=self.closed_fcb[de] and key in self.files:
                self.files[key]=b'CORRUPTED BY STALE FCB CLOSE'
                self.stale_closes.append(key)
                return 0
        closing_key=self.fcbkey(de) if fn==16 else None
        if fn==16 and de in self.opened and self.opened[de][0][2].endswith('.$$$'):
            if self.fail('close_output'):return 255
        value=super().bdos(fn,de)
        if fn==16 and value!=255:self.closed_fcb[de]=closing_key
        if fn==17 and value!=255:
            at=self.dma+value*32
            self.mem[at:at+32]=bytes(32)
            self.mem[at+1:at+12]=bytes(self.mem[de+1:de+12])
            if self.fcbkey(de) in self.readonly:self.mem[at+9]|=0x80
        return value

    def execute(self,lines,files=None,*,tpa=0xd000,failures=None,responses=(),break_keys=(),readonly=(),startup=None):
        self.lines=list(lines);self.responses=list(responses);self.break_keys=list(break_keys)
        self.closed_fcb={};self.stale_closes=[]
        self.readonly=set(readonly)
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
        if startup:
            tail=(' '+startup).encode();self.mem[0x80]=len(tail)
            self.mem[0x81:0x81+len(tail)]=tail
        self.reg['SP'].value=0xe000;self.reg['IY'].value=0xbeef
        result=self.lib.test_run(0x100,30000000)
        assert self.exception is None,self.exception
        assert result>=0,('CPU',result,hex(self.reg['PC'].value),self.console[-500:])
        assert self.reg['SP'].value==0xe000
        assert self.reg['IY'].value==0xbeef
        assert (self.drive,self.user,self.dma)==(1,0,0x80)
        assert bytes(self.mem[guard_start:0xd800])==bytes([0xa5])*max(0,0xd800-guard_start), 'resident-memory canary changed'
        assert not self.stale_closes,self.stale_closes
        assert not self.lines,self.lines
        self.cases+=1
        return self.console


def main():
    generate(check=True)
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
        for limit in [m.minimum_tpa,m.minimum_tpa-1]:
            text=m.execute(['G'] if limit==m.minimum_tpa else [],tpa=limit)
            assert ('insufficient' in text)==(limit<m.minimum_tpa),text
        for data in [b'',bytes(8193)]:
            text=m.execute(['RTINY.COM','G'],{tiny:data})
            assert 'outside' in text or 'capacity' in text,text
        text=m.execute(['RTINY.COM','N1','F1234','G'],{tiny:b'\x00'})
        assert 'outside' in text,text
        for bad in [b'0100 START\x1a0101 BAD',b'0100 9BAD\r\n']:
            text=m.execute(['RTINY.SYM','G'],{diskkey(1,'TINY.SYM'):bad})
            assert 'invalid metadata' in text,text
        text=m.execute(['STINY.ALL','G'])
        assert 'outside loaded input' in text and not m.created,text
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
        text=m.execute(['RTINY.COM','N6','STINY.ASM','P100,106','QL100,106'],
                       {tiny:bytes.fromhex('3e21d30200c9')},break_keys=['\x03','Y'])
        assert 'cancelled' in text and out not in m.files,text
        assert any(k[2].endswith('.$$$') for k in m.files),m.files
        text=m.execute(['RTINY.COM','N6','STINY.ASM','QL100,106'],
                       {tiny:bytes.fromhex('3e21d30200c9')},break_keys=['\x03','Y'],
                       failures={'close_output':1})
        assert 'I/O failed' in text and out not in m.files,text
        text=m.execute(['RTINY.COM','N6','STINY.ASM','X','P100,106','QL100,106','Z','G'],
                       {tiny:bytes.fromhex('3e21d30200c9')})
        assert 'until ASM Closed' in text and out in m.files,text
        sym_in=diskkey(1,'TINY.SYM');sym_out=diskkey(1,'OUT.SYM')
        raw=(b'0101 zed\r\n0100 alpha_long\r\n0100 Alpha\r\n0100 ALPHA\r\n')
        expected=b'0100 ALPHA\r\n0100 ALPHA_LONG\r\n0101 ZED\r\n'
        text=m.execute(['RTINY.SYM','SOUT.SYM','G'],{sym_in:raw})
        assert m.files[sym_out].split(b'\x1a',1)[0]==expected,(text,m.files[sym_out])
        text=m.execute(['RTINY.SYM','E100,.BETA','E100,.ALPHA','E200,.ALPHA','SOUT.SYM','G'],{sym_in:raw})
        assert 'conflicting symbol' in text,text
        assert m.files[sym_out].split(b'\x1a',1)[0]==expected.replace(b'0101 ZED',b'0100 BETA\r\n0101 ZED'),m.files[sym_out]
        for bad in [b'0100 ALPHA\r\n0101 alpha\r\n',b'0100 LD\r\n']:
            text=m.execute(['E100,.KEEP','RTINY.SYM','SOUT.SYM','G'],{sym_in:bad})
            assert m.files[sym_out].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',(text,m.files[sym_out])
        for reserved in ['LD','HL','NZ','OR','MACRO']:
            text=m.execute(['E100,.KEEP','E100,.'+reserved,'SOUT.SYM','G'])
            assert 'reserved ZSM4' in text,text
            assert m.files[sym_out].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',m.files[sym_out]
        text=m.execute(['RTINY.COM','N2','RTINY.SYM','STINY.ASM','P.ALPHA,.ZED','QL.ALPHA,.ZED','Z','G'],
                       {tiny:b'\xc9\x00',sym_in:raw})
        assert b'ORG\t0100H' in m.files[out],(text,m.files[out])
        assert b'0C9H' in m.files[out],m.files[out]
        symbol_file=diskkey(1,'TINY.SYM')
        for bad in [b'0100 REPLACE\r\nINVALID\r\n',
                    b''.join(f'{n:04X} S{n:011d}\r\n'.encode() for n in range(300))]:
            text=m.execute(['E100,.KEEP','RTINY.SYM','SRETAIN.SYM','G'],{symbol_file:bad})
            assert 'KEEP' in text and ('invalid metadata' in text or 'capacity' in text),text
            assert m.files[diskkey(1,'RETAIN.SYM')].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',m.files
            m.intact()
        for suffix,raw,expected in [
            ('CTL',b'0104,H\r\n0100,I\r\n0104,H\r\n',b'0100,I\r\n0104,H\r\n'),
            ('DOC',b'0104 Mixed Case\r\n0100 First\r\n0104 Mixed Case\r\n',b'0100 First\r\n0104 Mixed Case\r\n')]:
            src=diskkey(1,'TINY.'+suffix);dst=diskkey(1,'OUT.'+suffix)
            text=m.execute(['RTINY.'+suffix,'SOUT.'+suffix,'G'],{src:raw})
            assert m.files[dst].split(b'\x1a',1)[0]==expected,(text,m.files[dst])
            m.intact()
        for suffix,raw in [('CTL',b'0100,I\r\n0100,H\r\n'),
                           ('DOC',b'0100 First\r\n0100 Second\r\n')]:
            text=m.execute(['E100,.KEEP','RTINY.'+suffix,'SOUT.SYM','G'],
                           {diskkey(1,'TINY.'+suffix):raw})
            assert 'conflicting metadata' in text,text
            assert m.files[sym_out].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',m.files[sym_out]
        text=m.execute([';100,MiXeD case; literal quotes \"hello\"','SOUT.DOC','G'])
        assert m.files[diskkey(1,'OUT.DOC')].split(b'\x1a',1)[0]==b'0100 MiXeD case; literal quotes \"hello\"\r\n',m.files
        for bad in [';100,*NOP',';100,bad\nINJECT']:
            text=m.execute([';100,Keep Original',bad,'SOUT.DOC','G'])
            assert m.files[diskkey(1,'OUT.DOC')].split(b'\x1a',1)[0]==b'0100 Keep Original\r\n',m.files
        text=m.execute(['e100,._Mixed','K._mixed+bad','SOUT.SYM','G'])
        assert m.files[sym_out].split(b'\x1a',1)[0]==b'0100 _MIXED\r\n',m.files
        text=m.execute(['e100,._Mixed','k._mixed','SOUT.SYM','G'])
        assert m.files[sym_out].split(b'\x1a',1)[0]==b'',m.files
        text=m.execute(['rb:tiny.com','n1','g'],{diskkey(2,'TINY.COM'):b'\xc9'})
        assert 'Command Error' not in text,text
        m.intact()
        for bad in ['C100,Hjunk','C100,X']:
            text=m.execute(['C100,i',bad,'SOUT.CTL','G'])
            assert m.files[diskkey(1,'OUT.CTL')].split(b'\x1a',1)[0]==b'0100,I\r\n',m.files
        text=m.execute(['STINY.ASM','G'],{out:b'\xc9'},startup='TINY.ASM')
        assert 'aliases' in text and m.files[out]==b'\xc9' and not m.created,(text,m.files)
        text=m.execute(['STINY.ASM','G'],{out:b'KEEP'},readonly=[out])
        assert 'read-only' in text and m.files[out]==b'KEEP' and not m.created,(text,m.files)
        text=m.execute(['STINY.ASM','G'],{out:b'KEEP'},responses=['N'])
        assert m.files[out]==b'KEEP' and not m.created,(text,m.files)
        user_out=diskkey(1,'OUT.ASM',7)
        text=m.execute(['RTINY.COM','N6','SA7:OUT.ASM','P100,106','QL100,106','Z','G'],
                       {tiny:bytes.fromhex('3e21d30200c9')})
        assert user_out in m.files and b'ASEG' in m.files[user_out],(text,m.files)
        unrelated=diskkey(1,'DAS00000.$$$')
        text=m.execute(['RTINY.COM','N6','SA7:OUT.ASM','P100,106','L0','Z','G'],
                       {tiny:bytes.fromhex('3e21d30200c9'),unrelated:b'UNRELATED USER ZERO'})
        assert user_out not in m.files and m.files[unrelated]==b'UNRELATED USER ZERO',(text,m.files)
        m.intact()
        text=m.execute(['SA7:OUT.ASM','G'],{user_out:b'KEEP7'},readonly=[user_out])
        assert m.files[user_out]==b'KEEP7' and not m.created,(text,m.files)
        for user in [0,7,15,16,31]:
            source=diskkey(2,'SOURCE.COM',user);destination=diskkey(1,'OUT.ASM',user)
            text=m.execute([f'RB{user}:SOURCE.COM','N1',f'SA{user}:OUT.ASM','P100,101','QL100,101','Z','G'],{source:b'\xc9'})
            assert destination in m.files and b'0C9H' in m.files[destination],(user,text,m.files)
            m.intact()
        for bad in ['RA32:SOURCE.COM','R[A0-A1]:SOURCE.COM','RA1:LONGERTHAN8.COM','SA31:BAD NAME.ASM']:
            text=m.execute([bad,'G'])
            assert 'Command Error' in text and not m.created,(bad,text)
        text=m.execute(['RTINY.COM','N6','SA31:OUT.ASM','L0','Z','G'],{tiny:bytes.fromhex('3e21d30200c9')})
        assert 'A31:DAS00000.$$$' in text,text
        text=m.execute(['E100,.KEEP','E10000,.WRAP','SOUT.SYM','G'])
        assert m.files[sym_out].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',m.files
        startup_source=diskkey(1,'TINY.ASM',31)
        text=m.execute(['SA31:TINY.ASM','G'],{startup_source:b'\xc9'},startup='a31:tiny.asm')
        assert 'aliases' in text and m.files[startup_source]==b'\xc9' and not m.created,(text,m.files)
        text=m.execute(['N1','SA0:TINY.ASM','P100,101','QL100,101','Z','G'],
                       {startup_source:b'\xc9'},startup='a31:tiny.asm')
        assert b'0C9H' in m.files[out] and m.files[startup_source]==b'\xc9',(text,m.files)
        for query in ['/ver',' /VER  ','\t/ver\t']:
            text=m.execute([],startup=query,tpa=0x6000)
            assert 'DASM development' in text and not m.created,text
        text=m.execute(['RTINY.COM','N4','RTINY.SYM','STINY.ASM','P100,104','QL100,104','Z','G'],
                       {tiny:bytes.fromhex('210101c9'),sym_in:b'0100 START\r\n0100 ALIAS\r\n0101 INSIDE\r\n00AF DATAAF\r\nFFFF LAST\r\n'})
        assembly=m.files[out].split(b'\x1a',1)[0]
        assert all(name in assembly for name in [b'START',b'ALIAS',b'INSIDE',b'DATAAF',b'LAST']),assembly
        assert b'00AFH' in assembly and b'0FFFFH' in assembly,assembly
        (w/'symbols.asm').write_bytes(assembly)
        result=subprocess.run([str(Path.home()/'bin/z80asm'),'-e12','-fb','-o'+str(w/'symbols.bin'),str(w/'symbols.asm')],capture_output=True)
        assert result.returncode==0,(result.stdout,assembly)
        assert (w/'symbols.bin').read_bytes()==bytes.fromhex('210101c9')
        text=m.execute(['RTINY.COM','N1','STINY.ASM','P100,ZZ','Z','G'],{tiny:b'\xc9'})
        assert b'ORG' not in m.files[out],(text,m.files[out])
        symbols=b'0100 START\r\nFFFF LAST\r\n'
        for command in ('I100,1','I100,+1','I0,-101','I100,10000','I100,1 X'):
            text=m.execute(['RTINY.SYM',command,'SOUT.SYM','G'],{sym_in:symbols})
            assert m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'FFFF LAST\r\n0100 START\r\n',(command,text,m.files)
        text=m.execute(['RTINY.SYM','I100,-1','SOUT.SYM','G'],{sym_in:symbols})
        assert m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'FFFE LAST\r\n00FF START\r\n',text
        for metadata in (b'\t0100\tstart  \r0101 second\r',
                         b' 0100 start\r\n\r\n0101 second\n',
                         b'0101 second\n0100 start\n0100 START\n'):
            text=m.execute(['RTINY.SYM','SOUT.SYM','G'],{sym_in:metadata})
            assert m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'0101 SECOND\r\n0100 START\r\n',(metadata,text,m.files)
            assert 'imported 2; coalesced' in text,text
        text=m.execute(['RTINY.SYM','G'],{sym_in:b'0100 FIRST\r\n\r\nINVALID\r\n'})
        assert 'invalid metadata at line 3' in text,text
        for key in ('q','\x03'):
            text=m.execute(['RTINY.COM','N1','STINY.ASM','P100,101','QL100,101','Z','G'],
                           {tiny:b'\xc9'},break_keys=[key]+(['N'] if key=='\x03' else []))
            assert out not in m.files and any(k[2].endswith('.$$$') for k in m.files),text
        for origin,payload in ((0,b'\xc9'),(0x1200,bytes.fromhex('210112c9')),
                               (0xfffc,bytes.fromhex('2101ffc9')),(0xffff,b'\xc9')):
            end=origin+len(payload)
            text=m.execute(['RTINY.COM',f'N{len(payload):X}',f'O{origin:X}',
                            'STINY.ASM',f'P{origin:X},{end:X}',f'QL{origin:X},{end:X}','Z','G'],{tiny:payload})
            asm=m.files[out].split(b'\x1a',1)[0]
            assert 'outside loaded input' not in text,(origin,text,asm)
            path=w/'origin.asm';path.write_bytes(asm)
            result=subprocess.run([str(Path.home()/'bin/z80asm'),'-e12','-fb','-o'+str(w/'origin.bin'),str(path)],capture_output=True)
            assert result.returncode==0,(origin,result.stdout,asm)
            assert (w/'origin.bin').read_bytes()==payload,(origin,asm,(w/'origin.bin').read_bytes())
        text=m.execute(['RTINY.COM','N2','OFFFF','STINY.ASM','P100,102','QL100,102','Z','G'],{tiny:b'\0\xc9'})
        assert 'outside loaded input' in text and b'ORG\t0100H' in m.files[out],text
        text=m.execute(['RTINY.COM','N1','OFFFF','STINY.ASM','PFFFF,10000','QLFFFF,10001','Z','G'],{tiny:b'\xc9'})
        assert b'0C9H' not in m.files[out] and 'Command Error' in text,text
        ctl=diskkey(1,'OUT.CTL'); doc=diskkey(1,'OUT.DOC')
        text=m.execute(['CFFFF,H','C100,B','C200,W','C200,K','SOUT.CTL',
                        ';FFFF,Last Byte',';100,First',';200,Middle',';100,Changed',';200,','SOUT.DOC','G'])
        assert m.files[ctl].split(b'\x1a',1)[0]==b'0100,B\r\nFFFF,H\r\n',(text,m.files)
        assert m.files[doc].split(b'\x1a',1)[0]==b'FFFF Last Byte\r\n0100 Changed\r\n',(text,m.files)
        text=m.execute(['ROUT.CTL','ROUT.DOC','SNEW.CTL','SNEW.DOC','G'],
                       {ctl:b'FFFF,H\r\n0100,B\r\n',doc:b'FFFF Last Byte\r\n0100 Changed\r\n'})
        assert m.files[diskkey(1,'NEW.CTL')].split(b'\x1a',1)[0]==b'0100,B\r\nFFFF,H\r\n',text
        assert m.files[diskkey(1,'NEW.DOC')].split(b'\x1a',1)[0]==b'0100 Changed\r\nFFFF Last Byte\r\n',text
        text=m.execute(['RTINY.COM','N1','OFFFF',';FFFF,Last Byte','CFFFF,H','STINY.ASM',
                        'PFFFF,10000','QLFFFF,10000','Z','G'],{tiny:b'\xc9'})
        assert b'Last Byte' in m.files[out] and b'0C9H' in m.files[out],(text,m.files[out])
        comments=[f';{i:04X},'+('x'*74) for i in range(26)]
        text=m.execute(comments+[';0000,'+('y'*74),';001A,'+('z'*74),'SOUT.DOC','G'])
        data=m.files[doc].split(b'\x1a',1)[0]
        assert b'0000 '+b'y'*74 in data and b'001A ' not in data and 'capacity exceeded' in text,text
        session=diskkey(1,'TINY.ALL')
        payload=bytes.fromhex('210112c9')
        text=m.execute(['RTINY.COM','N4','O1200','E1200,.START','EFFFF,.LAST',
                        'C1200,I',';1200,Case Preserved','STINY.ALL','G'],{tiny:payload})
        assert 'session saved' in text,(text,m.files)
        saved=dict(m.files)
        import zlib
        descriptor=saved[session]
        assert len(descriptor)==128 and descriptor[:5]==b'BCDS\x01',descriptor
        assert int.from_bytes(descriptor[124:],'little')==zlib.crc32(descriptor[:124])
        assert int.from_bytes(descriptor[25:29],'little')==zlib.crc32(payload)
        assert descriptor[8:12]==bytes.fromhex('00120400')
        text=m.execute(['RTINY.COM','RTINY.ALL','SOUT.SYM','SOUT.DOC','SOUT.CTL',
                        'STINY.ASM','P1200,1204','QL1200,1204','Z','G'],saved)
        assert 'complete session validated and loaded' in text,(text,m.files)
        assert m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'FFFF LAST\r\n1200 START\r\n',text
        assert m.files[doc].split(b'\x1a',1)[0]==b'1200 Case Preserved\r\n',text
        assert m.files[ctl].split(b'\x1a',1)[0]==b'1200,I\r\n',text
        assert b'ORG\t1200H' in m.files[out],m.files[out]
        # Every failed component/hash/descriptor load retains the prior live table.
        for corruption in ('descriptor','binary','component','version'):
            files=dict(saved)
            if corruption=='binary':files[tiny]=b'BAD!'
            elif corruption=='component':
                component=next(k for k in files if k[2].endswith('.DOC'))
                files[component]=b'1300 Wrong\r\n'
            else:
                bad=bytearray(descriptor);bad[4 if corruption=='version' else 127]^=1
                files[session]=bytes(bad)
            text=m.execute(['RTINY.COM','E100,.KEEP','RTINY.ALL','SOUT.SYM','G'],files)
            assert 'invalid or mismatched session' in text,(corruption,text)
            assert m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',(corruption,text)
        for component_index in range(3):
            files=dict(saved); bad=bytearray(descriptor)
            at=29+19*component_index
            bad[at+12]=32
            bad[124:128]=zlib.crc32(bad[:124]).to_bytes(4,'little')
            files[session]=bytes(bad)
            text=m.execute(['RTINY.COM','E100,.KEEP','RTINY.ALL','SOUT.SYM','G'],files)
            assert 'invalid or mismatched session' in text,text
            assert m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',text
        for operation,limit in (('make',4),('write',4),('close_output',5),('rename',5)):
            for nth in range(1,limit+1):
                text=m.execute(['RTINY.COM','N4','E100,.NEW','STINY.ALL','G'],saved,
                               responses=['Y'],failures={operation:nth})
                assert 'session saved' not in text,(operation,nth,text)
                if operation!='make' or nth!=1:assert 'Recovery files:' in text,text
                assert all(m.files[k]==v for k,v in saved.items() if k!=session),(operation,nth)
                assert m.files.get(session)==descriptor or any(k[2].endswith('.BAK') and v==descriptor for k,v in m.files.items()),(operation,nth,text)
        # Replacing a descriptor never overwrites its old component graph.
        text=m.execute(['RTINY.COM','N4','E100,.NEW','STINY.ALL','G'],saved,responses=['Y'])
        assert 'session saved' in text,text
        assert m.files[session]!=descriptor
        assert all(m.files[k]==v for k,v in saved.items() if k!=session)
        assert any(k[2].endswith('.BAK') and v==descriptor for k,v in m.files.items())
        source31=diskkey(1,'TINY.COM',16); session31=diskkey(2,'STATE.ALL',31)
        text=m.execute(['RA16:TINY.COM','N4','E100,.START','SB31:STATE.ALL','G'],{source31:payload})
        assert 'session saved' in text,text
        user_saved=dict(m.files)
        text=m.execute(['RA16:TINY.COM','RB31:STATE.ALL','SOUT.SYM','G'],user_saved)
        assert 'complete session validated and loaded' in text and b'0100 START' in m.files[diskkey(1,'OUT.SYM')],text
        text=m.execute(['RTINY.DOC','SOUT.DOC','G'],{diskkey(1,'TINY.DOC'):b'0100   Mixed Case  \r\n'})
        assert m.files[doc].split(b'\x1a',1)[0]==b'0100   Mixed Case  \r\n',m.files[doc]
        dense=b''.join(f'{i:04X},H\r\n'.encode() for i in range(511))
        text=m.execute(['RTINY.CTL','CFFFF,H','SOUT.CTL','G'],{diskkey(1,'TINY.CTL'):dense})
        assert m.files[ctl].split(b'\x1a',1)[0]==dense and 'capacity exceeded' in text,text[-800:]
        dense=b''.join(bytes([0xc3,(0x2000+i)&255,(0x2000+i)>>8]) for i in range(520))
        text=m.execute(['RTINY.COM',f'N{len(dense):X}','E100,.KEEP',f'B100,{256+len(dense):X}','SOUT.SYM','G'],{tiny:dense})
        assert 'capacity exceeded' in text and m.files[diskkey(1,'OUT.SYM')].split(b'\x1a',1)[0]==b'0100 KEEP\r\n',text[-1200:]
        dense=(b'ABCDEFGH\0')*300
        text=m.execute(['RTINY.COM',f'N{len(dense):X}','C100,I',f'A100,{256+len(dense):X}','SOUT.CTL','G'],{tiny:dense})
        assert 'capacity exceeded' in text and m.files[ctl].split(b'\x1a',1)[0]==b'0100,I\r\n',text[-1200:]
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
