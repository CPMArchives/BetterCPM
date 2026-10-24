#!/usr/bin/env python3
"""Execute DLINK and the unchanged pinned LINK on the independent Z80 core."""
import ctypes as C
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from build_dlink import build, ROOT
from dsym_reference import convert_log
from utility_versions import banner
from test_usq import SHIM
from test_usq_com import Command, diskkey, padded

class Launcher(Command):
    def __init__(self,library,image,listing):
        super().__init__(library,image,listing,required_symbols=('DL_OLDSP','DL_LOG_FCB',
            'DL_MAIN_STACK','DL_MAIN_TOP','DL_CHILD_STACK','DL_CHILD_TOP','DL_CHAIN','D_CRC','DL_PACKED','DL_RES_END','DL_LINK_FCB'))
    def callback(self,kind):
        try:
            assert len(self.console)<10000,('unbounded console',self.console[-500:])
            assert kind==0 and self.reg['PC'].value==0xff00
            sp=self.reg['SP'].value
            assert 0x100<=sp<0xa000 or self.symbols['DL_MAIN_STACK']<=sp<self.symbols['DL_CHILD_TOP'] or 0xdff0<=sp<0xe000,hex(sp)
            fn=self.reg['C'].value;de=self.reg['D'].value<<8|self.reg['E'].value
            value=self.bdos(fn,de)
            self.reg['A'].value=value
            self.reg['F'].value=0x55
            for i,name in enumerate(('B','C','D','E','H','L')):self.reg[name].value=0xd1+i
            if fn==29:self.reg['H'].value=self.ro_mask>>8;self.reg['L'].value=self.ro_mask&255
        except BaseException as error:
            self.exception=error
            self.reg['PC'].value=0xffff;self.mem[0xffff]=0x76
            C.c_int.in_dll(self.lib,'cpu_error').value=1
    def bdos(self,fn,de):
        if fn==29:return self.ro_mask&255
        if fn==11:return 255 if self.cancel else 0
        if fn==12:return 0x22
        if fn==2:self.console+=chr(de&255);return 0
        if fn==6:
            if de&255==255:
                if self.cancel:self.cancel=False;return 3
                return 0
            self.console+=chr(de&255)
            return 0
        if fn==32:
            if de&255!=255:self.user=de&255
            return self.user
        if fn==14:self.drive=(de&255)+1;return 0
        if fn in (16,20,21) and de in self.opened:
            assert self.opened[de][0][1]==self.user,('wrong FCB user',fn,self.user,self.opened[de])
        # Shared model classifies the launcher log as output, all other closes
        # use the default close_output failure counter in these tests.
        return super().bdos(fn,de)
    def run(self,command,files,*,user=0,drive=1,failures=None,tpa=0xd000,late_existing=None,ro_mask=0,cancel=False):
        self.ro_mask=ro_mask;self.cancel=cancel
        self.lib.set_hooks(0xff00,0xfffe,self.hook)
        self.files=dict(files);self.original=dict(files);self.user=user;self.drive=drive
        self.failures=failures or {};self.late_existing=late_existing
        self.attempts,self.opened,self.searches={},{},{}
        self.events,self.created,self.deleted,self.renamed=[],[],[],[]
        self.dma,self.console,self.exception=0x80,'',None
        self.mem[:]=bytes(65536)
        self.mem[0x100:0x100+len(self.image)]=self.image
        self.mem[5]=0xc3;self.mem[6:8]=tpa.to_bytes(2,'little')
        self.mem[tpa:tpa+3]=b'\xc3\x00\xff';self.mem[0xff00]=0xc9
        guard=tpa+3
        self.mem[guard:0xd800]=bytes([0xa5])*(0xd800-guard)
        tail=(' '+command).encode();self.mem[0x80]=len(tail)
        self.mem[0x81:0x81+len(tail)]=tail
        self.reg['SP'].value=0xe000;self.reg['IY'].value=0xbeef
        result=self.lib.test_run(0x100,30000000)
        assert self.exception is None,self.exception
        assert result>=0,('CPU/budget',result,hex(self.reg['PC'].value),self.console[-500:])
        assert self.reg['SP'].value==0xe000 and self.reg['IY'].value==0xbeef
        assert (self.drive,self.user,self.dma)==(drive,user,0x80)
        assert self.word(6)==tpa and self.mem[5]==0xc3
        assert bytes(self.mem[guard:0xd800])==bytes([0xa5])*(0xd800-guard)
        if self.mem[0xa000]==0xc3:
            size=self.symbols['DL_LINK_FCB']-0xa000
            packed=self.symbols['DL_PACKED']-0x100
            expected=bytearray(self.image[packed:packed+size])
            actual=bytearray(self.mem[0xa000:0xa000+size])
            for start,count in ((self.symbols['DL_CHAIN']+1,2),(self.symbols['D_CRC'],4)):
                at=start-0xa000;expected[at:at+count]=actual[at:at+count]
            assert expected==actual,'resident instructions changed'
        self.cases+=1
        return self.console

def main():
    z80pack=Path.home()/'projects/git/z80pack';core=z80pack/'z80core'
    with tempfile.TemporaryDirectory(prefix='dlink-test-') as temporary:
        w=Path(temporary);image=build(Path.home()/'bin/z80asm',w)
        (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for name in ('simmem.h','simport.h'):shutil.copyfile(z80pack/'z80sim/srcsim'/name,w/name)
        (w/'shim.c').write_text(SHIM)
        subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(w),'-I'+str(core),str(w/'shim.c'),
                        str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
        m=Launcher(C.CDLL(str(w/'core.so')),image,(w/'dlink.lst').read_text())
        m.symbols['UC_INPUT']=0 # classify loader/log closes as outputs
        link=(ROOT/'third_party/dri-link/LINK.COM').read_bytes()
        rel=(ROOT/'tests/fixtures/dasm/link13/SYMTEST.REL').read_bytes()
        source=diskkey(1,'FIXTURE.REL');tool=diskkey(2,'LINK.COM')
        text=m.run('FIXTURE',{source:rel,tool:link})
        assert 'report captured' in text,(text,m.files.keys())
        report=m.files[diskkey(1,'FIXTURE.LOG')]
        assert convert_log(report)==b'0104 HELLO\r\n0100 START\r\n\x1a',report
        assert m.files[diskkey(1,'FIXTURE.COM')]==padded(bytes.fromhex('110401c900'))
        m.intact()
        baseline_attempts=dict(m.attempts)
        text=m.run('OTHER FIXTURE',{source:rel,tool:link})
        assert 'report captured' in text and convert_log(m.files[diskkey(1,'OTHER.LOG')])==b'0104 HELLO\r\n0100 START\r\n\x1a',text
        for suffix in ('COM','SYM','LOG'):
            existing=diskkey(1,'FIXTURE.'+suffix)
            text=m.run('FIXTURE',{source:rel,tool:link,existing:b'KEEP'})
            assert 'exists' in text and not m.created and m.files[existing]==b'KEEP',text
            m.intact()
        for caller,outuser in ((0,31),(7,16),(31,0)):
            src=diskkey(3,'FIXTURE.REL',outuser)
            text=m.run(f'C{outuser}:FIXTURE',{src:rel,tool:link},user=caller)
            assert 'report captured' in text,text
            assert convert_log(m.files[diskkey(3,'FIXTURE.LOG',outuser)])==b'0104 HELLO\r\n0100 START\r\n\x1a'
            m.intact()
        for command in ('','[A0,A1]:OUT','OUT B31:FIXTURE','OUT.COM','OUT NOFILE.BAD'):
            text=m.run(command,{source:rel,tool:link})
            assert ('Usage:' in text or 'same user' in text) and not m.created,(command,text)
        text=m.run('FIXTURE',{source:rel,tool:bytes([link[0]^1])+link[1:]})
        assert 'pinned' in text and not m.created,text
        for operation in ('make','write','close_output','rename'):
            for nth in range(1,baseline_attempts.get(operation,0)+1):
                text=m.run('FIXTURE',{source:rel,tool:link},failures={operation:nth})
                assert diskkey(1,'FIXTURE.LOG') not in m.files,(operation,nth,text)
                m.intact()
        for ceiling in (m.symbols['DL_RES_END']+256,m.symbols['DL_RES_END']+255):
            text=m.run('FIXTURE',{source:rel,tool:link},tpa=ceiling)
            assert ('insufficient' in text)==(ceiling==m.symbols['DL_RES_END']+255),text
            if 'insufficient' in text:assert not m.created
        for query in ('/VER',' /ver  ','X /VER','/VER X','/VER /VER','FILE\t/vEr'):
            text=m.run(query,{},user=31,tpa=0x6000)
            assert banner('DLINK') in text and not m.created,text
        collision=diskkey(1,'DLG00000.$$$')
        text=m.run('FIXTURE',{source:rel,tool:link,collision:b'KEEP'})
        assert 'report captured' in text and m.files[collision]==b'KEEP'
        assert m.created[0]==diskkey(1,'DLG00001.$$$')
        late=diskkey(1,'FIXTURE.COM')
        text=m.run('FIXTURE',{source:rel,tool:link},late_existing=(late,b'LATE KEEP'))
        assert m.files[late]==b'LATE KEEP' and diskkey(1,'FIXTURE.LOG') not in m.files,text
        text=m.run('C31:FIXTURE',{diskkey(3,'FIXTURE.REL',31):rel,tool:link},ro_mask=4)
        assert 'destination drive is read-only' in text and not m.created,text
        text=m.run('FIXTURE',{source:rel,tool:link},cancel=True)
        assert 'cancelled; report not published' in text and diskkey(1,'FIXTURE.LOG') not in m.files,text
        m.intact()
        for nth in (1,124):
            text=m.run('FIXTURE',{source:rel,tool:link},failures={'read':nth})
            assert diskkey(1,'FIXTURE.LOG') not in m.files,(nth,text)
            m.intact()
        print('PASS:',m.cases,'DLINK/pinned LINK full-core cases')
if __name__=='__main__':main()
