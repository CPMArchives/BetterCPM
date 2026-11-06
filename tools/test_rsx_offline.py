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
        req=bytes((2 if location is None else 3,op,0,0))+name.ljust(8,b' ')+bytes(2)+struct.pack('<HH',getattr(self,'workspace_low',0x405),high or min(self.word(6),0x7000))
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
    from test_rsx_disk_cache import main as disk_cache_checks
    disk_cache_checks()


if __name__=='__main__':main()
