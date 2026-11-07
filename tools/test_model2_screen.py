#!/usr/bin/env python3
"""Execute the production screen and metadata code against a switchable Model II VRAM window."""
import argparse
import ctypes as C
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

from build_z80pack_image import symbols
from test_usq import SHIM
from run_model2_qualification import SCREEN_CASES


# io_out is the hardware boundary. Swap the top 2 KiB on each FFh transition.
# This catches stack accesses in the overlay as well as writes made on the wrong page.
WINDOW = """
#include <string.h>
BYTE vram[2048], upper[2048];
int mapped, enables, bad_latch;
void io_out(BYTE port, BYTE high, BYTE value) {
    int enable = value == 0x81;
    if (port != 0xff || (value != 1 && !enable) || mapped == enable || IFF)
        ++bad_latch;
    if (enable) {
        memcpy(upper, memory+0xf800, 2048);
        memcpy(memory+0xf800, vram, 2048);
        ++enables;
    } else {
        memcpy(vram, memory+0xf800, 2048);
        memcpy(memory+0xf800, upper, 2048);
    }
    mapped = enable;
}
"""


KEYBOARD = """
BYTE key_pending, key_value;
BYTE io_in(BYTE port, BYTE high) {
    if (port == 0xff) return key_pending ? 0x80 : 0;
    if (port == 0xfc && key_pending) {
        key_pending = 0;
        return key_value;
    }
    return 0;
}
"""


def cpu_library(directory, z80pack, shim):
    core = z80pack/'z80core'
    (directory/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h','simport.h'):
        shutil.copyfile(z80pack/'z80sim/srcsim'/name,directory/name)
    source = directory/'model2.c'
    source.write_text(shim)
    library = directory/'core.so'
    subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{directory}',f'-I{core}',str(source),
                    str(core/'simglb.c'), *map(str,sorted(core.glob('simz80*.c'))),
                    '-o',str(library)],check=True)
    return C.CDLL(str(library))


class Core:
    def __init__(self, directory, z80pack):
        stub = 'void io_out(BYTE l, BYTE h, BYTE d) {}'
        input_stub = 'BYTE io_in(BYTE l, BYTE h) { return 0; }'
        assert SHIM.count(stub) == SHIM.count(input_stub) == 1
        self.lib = cpu_library(directory,z80pack,SHIM.replace(stub,WINDOW).replace(input_stub,KEYBOARD))
        self.lib.test_run.argtypes = [C.c_ushort,C.c_int]
        self.r = {name:C.c_ubyte.in_dll(self.lib,name) for name in ('A','B','C','D','E','H','L','IFF')}
        self.mem = (C.c_ubyte*65536).in_dll(self.lib,'memory')
        self.video = (C.c_ubyte*2048).in_dll(self.lib,'vram')
        self.sp = C.c_ushort.in_dll(self.lib,'SP')
        self.mapped = C.c_int.in_dll(self.lib,'mapped')
        self.faults = C.c_int.in_dll(self.lib,'bad_latch')
        self.enables = C.c_int.in_dll(self.lib,'enables')

    def put(self,addr,data):
        self.mem[addr:addr+len(data)] = data

    def run(self,entry,sp=0x7800,**registers):
        self.sp.value = sp
        for name,value in registers.items():
            self.r[name].value = value
        steps = self.lib.test_run(entry,500000)
        assert steps>=0 and self.sp.value==sp,(hex(entry),steps,hex(self.sp.value))
        return self.r['A'].value

    def load_module(self,image,base):
        offset,size=struct.unpack_from('<HH',image,10)
        count=struct.unpack_from('<H',image,22)[0]
        data=bytearray(image[512:512+size])
        for i in range(count):
            pos=struct.unpack_from('<H',image,48+i*2)[0]
            word=struct.unpack_from('<H',data,pos)[0]
            struct.pack_into('<H',data,pos,(word+base-offset)&65535)
        self.put(base,data)

    def admit(self,stages,entry,image):
        req,facts,scratch,carrier = 0x6000,0x6100,0x6400,0x7000
        self.put(carrier,image)
        self.put(facts,b'\xa5'*26)
        self.put(req+32,image[32:40])
        for idx,(name,request) in enumerate([
            ('R3CARR.RSX',struct.pack('<6HB',carrier,len(image),req+32,scratch,scratch+256,facts,0xcc)),
            ('R3META.RSX',struct.pack('<5HB',carrier,len(image),scratch,scratch+256,facts,0xcc))],1):
            self.put(entry,(stages/name).read_bytes())
            self.put(req,request)
            before=bytes(self.mem[facts:facts+26])
            result=self.run(entry,sp=0x5800,D=req>>8,E=req&255)
            if result:
                assert self.mem[req+len(request)-1]==0xcc and bytes(self.mem[facts:facts+26])==before
                return idx
        return 0


def variant(image,cap=None,public=False,foreign=False):
    data=bytearray(image)
    start=struct.unpack_from('<H',data,30)[0]
    if public or foreign:
        assert data[start+12:start+16]==bytes([4,18,1,1])
        if public:data[start+15:start+32]=bytes(17)
        else:data[start+16]^=1
    if cap is not None:
        pos=data.index(b'SCRN',start)
        struct.pack_into('<H',data,pos+8,cap)
    return bytes(data)


def check(cpu,staged,legacy):
    output=staged/'build'
    data=output/'trs80m2'
    regs=json.loads((output/'profile/context.json').read_text())['symbols']
    bios=symbols(data/'bios.lst')
    m2=(output/'rsx/M2SCRN.RSX').read_bytes()
    m4=(legacy/'rsx/M4SCRN.RSX').read_bytes()
    # The unprofiled carrier tests use the actual legacy BIOS and validator.
    legacy_bios=symbols(legacy/'bios/bios.lst')
    cpu.put(legacy_bios['MONRAW']-69,(legacy/'bios/bios.bin').read_bytes())
    origin=symbols(legacy/'system/r3metadata.lst')['RXM_ENTRY']
    for module,stage in [(m4,0),(variant(m4,cap=4),2),(m2,1)]:
        assert cpu.admit(legacy/'system',origin,module)==stage
    cpu.put(regs['LY_SYS'],(data/'resident.bin').read_bytes())
    cpu.put(1,struct.pack('<H',regs['LY_BIOS']+3))
    accepted=[m2]+[(output/'rsx'/(n+'.RSX')).read_bytes() for n in ('ADM3A','VT52','ANSI')]
    rejected=[(m4,1),(variant(m2,foreign=True),1),(variant(m2,public=True),2)]
    rejected.extend((variant(m2,cap=c),2) for c in (0,1,2,3,5,6,7,0x104))
    for module,stage in [(m,0) for m in accepted]+rejected:
        got=cpu.admit(output/'system',regs['LY_CFG'],module)
        assert got==stage,(bytes(module[32:40]),stage,got)

    expected=bytes(i%253 for i in range(2048))
    for base,sp,iff in [(0x6100,0xfef0,0),(0x9200,0xfef0,3)]:
        cpu.load_module(m2,base)
        offset=m2.index(b'SCRN',struct.unpack_from('<H',m2,30)[0])
        entry=base+struct.unpack_from('<H',m2,offset+6)[0]
        cpu.put(0xf800,expected)
        cpu.video[:]=b' '*2048
        cpu.r['IFF'].value=iff
        def invoke(op,b=0,c=0,hl=0):
            result=cpu.run(entry,sp=sp,A=op,B=b,C=c,H=hl>>8,L=hl&255)
            assert cpu.r['IFF'].value==iff and cpu.mapped.value==0 and cpu.faults.value==0
            return result
        def cell(row,col):return cpu.video[80*row+col]
        invoke(6,23,79);invoke(7,c=0xc1)
        assert cell(23,79)==0xc1
        invoke(6,5,3);invoke(8,c=0xa0)
        assert bytes(cpu.video[400:480])==b' '*3+b'\xa0'*77
        invoke(13,c=32);assert cell(5,3)==32 and cell(6,3)==0xa0
        invoke(14,c=32);assert cell(5,3)==0xa0
        invoke(10,c=32);assert cell(4,3)==0xa0
        invoke(11,c=32);assert cell(5,3)==0xa0
        invoke(6);invoke(9,c=32);assert bytes(cpu.video[:1920])==b' '*1920
        # Operation 20 must read caller RAM even when its pointer is in the overlay.
        attr=bytes([32,0,0,0,0,0,0,0,0])
        cpu.put(0xfa00,attr)
        invoke(20,hl=0xfa00);invoke(21,c=ord('x'))
        assert cell(0,0)==0xf8
        invoke(6,23,0);invoke(24,b=0);assert cell(23,0)==0xa0
        invoke(0,c=7)
        for name,_,address in SCREEN_CASES:
            # Bind the relocated production frontend as the manager would.
            frontend=(output/'rsx'/(name+'.RSX')).read_bytes()
            frontbase=0x4200
            cpu.load_module(frontend,frontbase)
            cpu.put(frontbase+12,struct.pack('<H',entry))
            descriptor=frontend.index(b'MCON',struct.unpack_from('<H',frontend,30)[0])
            dispatch=frontbase+struct.unpack_from('<H',frontend,descriptor+6)[0]
            for c in address+b'M2!':
                cpu.run(dispatch,sp=sp,A=0,C=c)
            assert bytes(v&127 for v in cpu.video[489:492])==b'M2!',name
            cpu.video[489:492]=b'   '
            assert cpu.r['IFF'].value==iff and cpu.mapped.value==0 and cpu.faults.value==0

        ram=bytearray(expected);ram[512:521]=attr
        # The private test caller stack is in the upper RAM. Calls legitimately
        # alter its scratch words; the surrounding RAM and VRAM tail must survive.
        boundary=sp-0xf800
        assert bytes(cpu.mem[0xf800:sp-128])==ram[:boundary-128]
        assert bytes(cpu.mem[sp:0x10000])==ram[boundary:]
        assert bytes(cpu.video[1920:])==b' '*128
        assert cpu.enables.value>0
    print('PASS: production Model II and Model 4 admission, private identity, portable personalities, relocated VRAM operations and upper RAM with interrupts enabled/disabled')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('staged',type=Path,help='Model II prepared source tree')
    p.add_argument('--legacy',type=Path,default=Path(__file__).resolve().parents[1]/'build')
    p.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    args=p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        check(Core(Path(tmp),args.z80pack),args.staged,args.legacy)
