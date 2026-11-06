#!/usr/bin/env python3
"""Run production RSX transactions against a removable, drive/user-aware filesystem."""
import ctypes as C
import re
import shutil
import struct
import subprocess
from pathlib import Path
from system_layout import LAYOUT as L
from test_usq import SHIM
from test_rsx_stage3 import service_offset

ROOT = Path(__file__).resolve().parents[1]


class Machine:
    def __init__(self):
        work = ROOT/'build/rsx-offline-test';work.mkdir(parents=True, exist_ok=True)
        core = Path.home()/'projects/git/z80pack/z80core'
        (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
        for n in ('simmem.h','simport.h'):
            shutil.copy2(core.parent/'z80sim/srcsim'/n, work/n)
        shim = SHIM.replace('if(hook && PC==writepc)',
            'if(hook && PC==readpc+3) hook(2);\n  if(hook && PC==readpc+6) hook(3);\n  if(hook && PC==writepc)')
        (work/'shim.c').write_text(shim)
        subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',str(work/'shim.c'),str(core/'simglb.c'),*map(str, sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
        self.lib=C.CDLL(str(work/'core.so'))
        self.mem=(C.c_ubyte*65536).in_dll(self.lib,'memory')
        self.reg={n:C.c_ubyte.in_dll(self.lib,n) for n in 'AFBCDEHL'}
        self.sp=C.c_ushort.in_dll(self.lib,'SP')
        self.pc=C.c_ushort.in_dll(self.lib,'PC')
        self.hook=C.CFUNCTYPE(None,C.c_int)(self.callback)
        self.lib.set_hooks(L['FILE'],L['BDOS'],self.hook)
        for at in (L['FILE'],L['FILE']+3,L['FILE']+6,L['BDOS']):self.mem[at]=0xC9
        # MONBASE detaches any monitor before movement, without filesystem I/O.
        self.mem[L['BIOS']+72:L['BIOS']+75]=b'\xAF\xC9\0'
        listing=(ROOT/'build/bdos/bdos.lst').read_text()
        self.symbol={n:int(re.search(r'^([0-9a-f]{4}).*\b'+n+':',listing,re.M|re.I)[1],16) for n in ('UB_DMA','UB_DRIVE','UB_USERNO')}
        self.files={}
        self.stream=b'';self.position=0;self.opened=None;self.error=None;self.events=[];self.fail_read=False
        self.word(L['SYSTEM']+0x90,L['TPA']);self.word(6,L['TPA'])
        self.word(L['SYSTEM']+0x92,1)
        self.bootstrap=(ROOT/'build/system/r3entry.bin').read_bytes()
        self.files[0,0,'R3PACK.RSX']=(ROOT/'build/system/R3PACK.RSX').read_bytes()
        self.files[0,0,'R3CACHE.RSX']=(ROOT/'build/system/R3CACHE.RSX').read_bytes()

    def word(self, at, value=None):
        if value is None:return self.mem[at]|self.mem[at+1]<<8
        self.mem[at:at+2]=struct.pack('<H',value)

    def pair(self, name, value=None):
        if value is None:return self.reg[name[0]].value<<8|self.reg[name[1]].value
        self.reg[name[0]].value,self.reg[name[1]].value=value>>8,value&255

    def callback(self, kind):
        try:
            fcb=L['FILE']+109
            if kind==0:
                at=self.pair('HL');stem=bytes(self.mem[at:at+8]).decode().rstrip()
                name=stem+('.CPX' if self.reg['A'].value==0 else '.RSX')
                self.events.append(('runtime-open',0,0,name))
                data=self.files.get((0,0,name))
                value=255 if data is None else 0
                if data is not None:
                    self.stream=data;self.position=0;self.mem[fcb+15]=min(128,(len(data)+127)//128);self.mem[fcb+32]=0
            elif kind==2:
                self.position=self.mem[fcb+32]*128
                data=self.stream[self.position:self.position+512];value=0 if data else 255
                at=self.pair('HL')
                self.mem[L['CONFIG']:L['CONFIG']+1024]=b'\x55'*1024
                self.mem[at:at+512]=data.ljust(512,b'\0')
                self.position+=512;self.mem[fcb+32]=(self.mem[fcb+32]+4)&255
                self.pair('HL',at+512)
            elif kind==3:
                self.position=0;value=0
            else:
                fn=self.reg['C'].value
                drive=self.mem[fcb]-1;user=self.mem[self.symbol['UB_USERNO']]
                raw=bytes(self.mem[fcb+1:fcb+12]);name=raw[:8].decode().rstrip()+'.'+raw[8:].decode().rstrip()
                key=(drive,user,name)
                self.events.append((fn,*key))
                if fn==15:
                    self.opened=key;self.diskpos=0
                    value=3 if key in self.files else 255
                elif fn==20:
                    data=b'' if self.fail_read else self.files[self.opened][self.diskpos:self.diskpos+128]
                    value=0 if data else 1
                    if data:
                        at=self.word(self.symbol['UB_DMA']);self.mem[at:at+128]=data.ljust(128,b'\x1a')
                        self.diskpos+=128
                else:raise AssertionError(fn)
            self.reg['A'].value=value
            self.reg['F'].value=0x40 if value==0 else 0
        except BaseException as e:
            self.error=e;self.reg['A'].value=255;self.reg['F'].value=0

    def run(self, address, budget=3000000):
        self.sp.value=0x3F00
        result=self.lib.test_run(address,budget)
        assert result>=0,(result,hex(self.pc.value))
        assert self.error is None,self.error
        return self.reg['A'].value

    def change(self, op, name, location=None, high=None):
        at=0x300
        req=bytes((2 if location is None else 3,op,0,0))+name.ljust(8,b' ')+bytes(2)+struct.pack('<HH',0x405,high or min(self.word(6),0x7000))
        if location is not None:req+=bytes(location)
        self.mem[at:at+len(req)]=req
        self.mem[L['RSX']:L['RSX']+1024]=self.bootstrap.ljust(1024,b'\0')
        self.pair('DE',at)
        result=self.run(L['RSX'])
        # Model the production extension epilogue's direct-result marker.
        if self.mem[at+3]&0x80:
            result=self.mem[at+3]&1;self.mem[at+3]=0
        return result


def main():
    m=Machine()
    artifacts=ROOT
    stateful=(artifacts/'build/rsx/STATEFUL.RSX').read_bytes()
    hello=(artifacts/'build/rsx/HELLO.RSX').read_bytes()
    m.files[1,3,'STATEFUL.RSX']=stateful
    m.files[2,31,'HELLO.RSX']=hello
    m.mem[m.symbol['UB_DRIVE']]=2
    m.mem[m.symbol['UB_USERNO']]=17
    m.word(m.symbol['UB_DMA'],0x1600)
    def context():
        return m.mem[m.symbol['UB_DRIVE']],m.mem[m.symbol['UB_USERNO']],m.word(m.symbol['UB_DMA'])
    assert m.change(1,b'STATEFUL',(1,3))==0,('first load',m.events)
    assert context()==(2,17,0x1600)
    service=service_offset(stateful)
    def stat(op):
        base=m.word(L['SYSTEM']+0x84)
        for i in range(m.mem[L['RSX_STATE']]):
            if bytes(m.mem[L['RSX_STATE']+1+i*8:L['RSX_STATE']+9+i*8])==b'STATEFUL':
                break
            base=m.word(base)-8
        m.mem[0x3600:0x3610]=bytes((1,16,op))+bytes(13)
        m.pair('DE',0x3600)
        assert m.run(base+service)==(0xA4 if op==2 else 0)
        result=bytearray(m.mem[0x3600:0x3610])
        if op==2:
            for at in (6,8):
                value=struct.unpack_from('<H',result,at)[0]
                struct.pack_into('<H',result,at,value-base)
        return bytes(result)
    stat(0)
    for _ in range(3):stat(1)
    expected=stat(2)
    del m.files[1,3,'STATEFUL.RSX']
    m.events.clear()
    assert m.change(1,b'HELLO',(2,31))==0,m.events
    assert stat(2)==expected
    assert not any(e[0]==15 and e[-1]=='STATEFUL.RSX' for e in m.events)
    del m.files[2,31,'HELLO.RSX']
    m.events.clear()
    assert m.change(3,b'HELLO',(0,0))==1
    assert bytes(m.mem[0x312:0x314])==bytes((2,31))
    assert m.change(0,b'        ',(0,0))==1
    assert bytes(m.mem[0x312:0x314])==bytes((1,3))
    assert not any(e[0]==15 for e in m.events)
    for invalid in ((16,0),(0,32)):
        assert m.change(1,b'BAD',invalid)==255
    # A location does not replace an existing name; idempotence needs no source.
    m.events.clear()
    assert m.change(1,b'HELLO',(15,31))==0
    assert not any(e[0]==15 for e in m.events)
    before=bytes(m.mem[L['RSX_STATE']:L['RSX_STATE']+41])
    low=m.word(L['SYSTEM']+0x88)
    live=bytes(m.mem[low:L['RSX']-1024])
    generation=m.word(L['SYSTEM']+0x92)
    assert m.change(1,b'MISSING',(1,3))==255
    assert context()==(2,17,0x1600)
    assert bytes(m.mem[L['RSX_STATE']:L['RSX_STATE']+41])==before
    assert bytes(m.mem[low:L['RSX']-1024])==live
    assert m.word(L['SYSTEM']+0x92)==generation
    assert stat(2)==expected
    broken=bytearray(hello);broken[32:40]=b'BROKEN  '
    m.files[1,3,'BROKEN.RSX']=bytes(broken)
    m.fail_read=True
    assert m.change(1,b'BROKEN',(1,3))==255
    m.fail_read=False
    assert context()==(2,17,0x1600)
    assert bytes(m.mem[L['RSX_STATE']:L['RSX_STATE']+41])==before
    # STATELESS images retain a pristine template, rather than live mutations.
    hello_base=m.word(m.word(L['SYSTEM']+0x84))-8
    marker=struct.unpack_from('<H',hello,12)[0]-1
    original_byte=m.mem[hello_base+marker]
    m.mem[hello_base+marker]^=255
    extra=bytearray(hello);extra[32:40]=b'EXTRA   '
    m.files[0,0,'EXTRA.RSX']=bytes(extra)
    assert m.change(1,b'EXTRA')==0
    assert m.mem[hello_base+marker]==original_byte
    del m.files[0,0,'EXTRA.RSX']
    assert m.change(2,b'EXTRA')==0
    # Both the removed and retained carriers are now unavailable.
    m.events.clear()
    assert m.change(2,b'STATEFUL')==0,m.events
    assert not any(e[0]==15 for e in m.events),m.events
    assert bytes(m.mem[L['RSX_STATE']+1:L['RSX_STATE']+9])==b'HELLO   '
    hello_base=m.word(L['SYSTEM']+0x84)
    assert hello_base < L['RSX']-1024
    assert m.change(2,b'HELLO',(0,0))==0
    assert m.mem[L['RSX_STATE']]==0 and m.word(L['SYSTEM']+0x84)==0
    assert m.word(6)==L['TPA']
    assert context()==(2,17,0x1600)
    # Legacy v2 callers still resolve only A0, regardless of current DU.
    m.files[0,0,'HELLO.RSX']=hello
    assert m.change(1,b'HELLO')==0
    del m.files[0,0,'HELLO.RSX']
    assert m.change(2,b'HELLO')==0
    # A small first allocation forces overlapping upward STATEFUL movement.
    small=bytearray(hello);struct.pack_into('<H',small,14,256)
    m.files[0,0,'HELLO.RSX']=bytes(small)
    m.files[1,3,'STATEFUL.RSX']=stateful
    assert m.change(1,b'HELLO')==0
    assert m.change(1,b'STATEFUL',(1,3))==0
    stat(0)
    for _ in range(3):stat(1)
    old=m.word(m.word(L['SYSTEM']+0x84))-8
    listing=(ROOT/'build/rsx/stateful.lst').read_text()
    fixed=int(re.search(r'^([0-9a-f]{4}).*\bSR_FIXED:',listing,re.M|re.I)[1],16)-0x8000
    external=old+struct.unpack_from('<H',stateful,14)[0]+2
    m.word(old+fixed,external)
    expected=stat(2)
    del m.files[0,0,'HELLO.RSX'];del m.files[1,3,'STATEFUL.RSX']
    assert m.change(2,b'HELLO')==0
    assert m.word(L['SYSTEM']+0x84)>old
    assert m.word(m.word(L['SYSTEM']+0x84)+fixed)==external
    assert stat(2)==expected
    assert m.change(2,b'STATEFUL')==0
    print('PASS explicit B3/C31 loads, legacy A0, offline retained movement/removal, state, idempotence, rollback, DU/DMA and last-provider reclamation')


if __name__=='__main__':main()
