"""Compare the integrated host ADM3A with the independent portable stack.

Checks rendered cells, cursor position and visibility after each protocol byte;
wire encodings may differ. Uses disposable binaries and a real assembled CPU.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import pyte
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_rsx_module import make_module
from build_z80pack_image import symbols
from test_bios import Z80
from test_screen_backends import fixture,load
from test_usq import SHIM
from integrated_source import display_source
from tcap_test_support import sha


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--bios',type=Path,default=ROOT/'build/z80pack')
    p.add_argument('--reference-workspace',type=Path,default=ROOT)
    a=p.parse_args();reference=a.reference_workspace.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    import test_screen_backends
    test_screen_backends.OUT=reference/'build/screen-backends'
    assembler=Path.home()/'bin/z80asm'
    source='M2BANK EQU 0\n'+display_source(backend='host')
    code=assemble(assembler,source,out/'native.bin',out/'native.lst',0x8000)
    alt=assemble(assembler,source.replace('08000H','08101H'),out/'alternate.bin',out/'alternate.lst',0x8101)
    labels=symbols(out/'native.lst')
    carrier=make_module(name='XTADM',version=(0,1),services=[],linked_base=0x8000,
        code=code,relocations=relocation_offsets(code,alt,0x101),reconstruction_class='STATEFUL',
        callable_services=[(b'MCON',1,0,labels['D_ENTRY']-0x8000,2),
                           (b'TCAP',2,0,labels['D_TCAP']-0x8000,0)])
    (out/'NATIVE.RSX').write_bytes(carrier)
    helper=assemble(assembler,'        ASEG\n        ORG 0100H\n'+
        (ROOT/'src/utilities/common/tcap2.inc').read_text()+'\n        END\n',
        out/'client.bin',out/'client.lst',0x100)
    total=int.from_bytes(carrier[14:16],'little')+256+len(helper)+64
    assert total<=1280,total
    core=Path.home()/'projects/git/z80pack/z80core'
    cpuout=out/'cpu';cpuout.mkdir()
    (cpuout/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h','simport.h'):
        shutil.copy2(core.parent/'z80sim/srcsim'/name,cpuout/name)
    shim=SHIM.replace('void io_out(BYTE l, BYTE h, BYTE d) {}',
        'unsigned wirelen, badport; BYTE wire[65536];\n'
        'void io_out(BYTE l, BYTE h, BYTE d) { if(l!=1)badport++; '
        'if(wirelen<65536)wire[wirelen++]=d; }')
    (cpuout/'shim.c').write_text(shim)
    subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{cpuout}',f'-I{core}',str(cpuout/'shim.c'),
        str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(cpuout/'core.so')],check=True)
    lib=C.CDLL(str(cpuout/'core.so'))
    class Native:
        def __init__(self):
            self.mem=(C.c_ubyte*65536).in_dll(lib,'memory')
            self.regs={name:C.c_ubyte.in_dll(lib,name) for name in 'ABC'}
            self.stack=C.c_ushort.in_dll(lib,'SP')
            self.wire=(C.c_ubyte*65536).in_dll(lib,'wire')
            self.length=C.c_uint.in_dll(lib,'wirelen')
        def __getattr__(self,name):
            if name=='sp':return self.stack.value
            return self.regs[name.upper()].value
        def __setattr__(self,name,value):
            if name=='sp':self.stack.value=value
            elif name in ('a','b','c'):self.regs[name.upper()].value=value
            else:object.__setattr__(self,name,value)
        def run(self,entry,limit):
            self.length.value=0
            result=lib.test_run(entry,limit)
            assert result>=0,result
            assert C.c_uint.in_dll(lib,'badport').value==0
            stream.feed(bytes(self.wire[:self.length.value]).decode('ascii'))
    checks=0
    for base,terminal_size in ((0x5000,(80,24)),(0x8101,(80,24)),(0x5000,(100,30))):
        old,_,oldcells,_=fixture('ANSISCRN',0x6000,cpmsim_bios=a.bios,terminal_size=terminal_size)
        oldlabels=load(old,reference/'build/monitor-development','adm3a',0x7000)
        old.setword(0x700c,old.backend_entry)
        oldentry=oldlabels['AM_ENTRY']-0x8000+0x7000
        new=Native();new.sp=0x4000
        patch=bytearray(code)
        for offset in relocation_offsets(code,alt,0x101):
            patch[offset:offset+2]=(int.from_bytes(patch[offset:offset+2],'little')+base-0x8000).to_bytes(2,'little')
        new.mem[base:base+len(patch)]=patch
        screen=pyte.Screen(*terminal_size);stream=pyte.Stream(screen)
        def newcells():
            return bytes(ord(screen.buffer[r][c].data)|(128 if screen.buffer[r][c].reverse else 0)
                         for r in range(24) for c in range(80))
        def command(op,char=0):
            nonlocal checks
            results=[]
            for cpu,entry in ((old,oldentry),(new,labels['D_ENTRY']-0x8000+base)):
                cpu.a,cpu.c=op,char;before=cpu.sp
                cpu.run(entry,limit=400000)
                assert cpu.sp==before
                results.append(cpu.a)
            x,y=oldcells(),newcells()
            assert x==y,(base,op,char,[(i,a,b) for i,(a,b) in enumerate(zip(x,y)) if a!=b][:8])
            if terminal_size!=(80,24):
                for row in range(terminal_size[1]):
                    for col in range(80 if row<24 else 0,terminal_size[0]):
                        assert screen.buffer[row][col]==old.terminal_screen.buffer[row][col],(op,char,row,col)
            rc=tuple(old.mem[oldlabels[k]-0x8000+0x7000] for k in ('AM_ROWPOS','AM_COLPOS'))
            nc=(new.mem[labels['H_RC']-0x8000+base],new.mem[labels['H_RC']-0x8000+base+1])
            assert rc==nc==(screen.cursor.y,min(79,screen.cursor.x)),(op,char,rc,nc,screen.cursor)
            if op==3:assert results[0]==results[1]
            checks+=1
        def send(data):
            for char in data:command(0,char)
        def position(r,c):send(bytes((27,61,r+32,c+32)))
        command(4)
        for row in range(24):
            position(row,0);send(bytes((65+row,))*80)
        for row,col in ((0,0),(0,79),(23,0),(23,79),(11,39)):
            for mode in (14,15):
                for char in range(32,256):
                    position(row,col);send(bytes((mode,char)))
        for row in range(24):
            for col in (0,39,79):
                for mode in (14,15):
                    for op in (21,23,26,28,29):
                        position(row,col);send(bytes((mode,op)))
        for hidden in (48,49):
            send(bytes((27,hidden)));command(3);command(3,ord('X'))
        rng=random.Random(20261108)
        send(bytes(rng.randrange(256) for _ in range(1000)))
        command(5)
        # Direct portable operations must preserve their success/bounds contract.
        for op in (6,1,4,3,5,7):
            new.a=op;new.run(labels['D_TCAP']-0x8000+base,limit=400000)
            assert new.a==0,(op,new.a)
        new.a,new.b,new.c=2,24,0
        before=newcells();new.run(labels['D_TCAP']-0x8000+base,limit=400000)
        assert new.a==3 and newcells()==before
    report={'status':'PASS integrated host ADM3A differential rendering','checks':checks,
        'payload_bytes':len(code),'resident_profile_bytes':int.from_bytes(carrier[14:16],'little')+256,
        'application_helper_bytes':len(helper),'shared_bios_state_bytes':0,
        'call_site_allowance_bytes':32,'stack_allowance_bytes':32,
        'full_budgeted_path_bytes':total,'payload_sha256':sha(out/'native.bin'),
        'terminal_sizes':[[80,24],[100,30]],
        'scope':'CPU differential rendering; real boot/loader/install qualification is separate'}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
