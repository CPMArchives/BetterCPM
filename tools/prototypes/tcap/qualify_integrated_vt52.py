"""Execute the integrated VT52 against an independent bounded terminal model."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import pyte
from build_ccp import assemble
from build_cpx_module import relocation_offsets
from build_integrated_display import source
from build_z80pack_image import symbols
from test_model2_screen import cpu_library
from test_usq import SHIM


class Terminal:
    def __init__(self):
        self.cells=bytearray(b' '*1920);self.row=self.col=self.state=0;self.pending=0
        self.queue=[];self.keyboard=[]
    def reset(self):self.state=0
    def clear(self):self.reset();self.row=self.col=0;self.cells[:]=b' '*1920
    def lf(self):
        if self.row<23:self.row+=1
        else:self.cells[:]=self.cells[80:]+b' '*80
    def rlf(self):
        if self.row:self.row-=1
        else:self.cells[:]=b' '*80+self.cells[:-80]
    def print(self,c,host=False):
        glyph=c&127
        if host and not 32<=glyph<127:glyph=ord('?')
        self.cells[self.row*80+self.col]=glyph if host else c
        self.col=min(79,self.col+1)
    def output(self,c,host=False):
        if self.state==2:
            self.pending=min(23,(c-32)&255);self.state=3;return
        if self.state==3:
            self.row=self.pending;self.col=min(79,(c-32)&255);self.reset();return
        if self.state==1:
            self.reset()
            if c==ord('Y'):self.state=2
            elif c==ord('Z'):
                if len(self.queue)<=1:self.queue+=list(b'\x1b/K')
            elif c==ord('A'):self.row=max(0,self.row-1)
            elif c==ord('B'):self.row=min(23,self.row+1)
            elif c==ord('C'):self.col=min(79,self.col+1)
            elif c==ord('D'):self.col=max(0,self.col-1)
            elif c==ord('H'):self.row=self.col=0
            elif c==ord('I'):self.rlf()
            elif c==ord('J'):self.cells[self.row*80+self.col:]=b' '*(1920-self.row*80-self.col)
            elif c==ord('K'):self.cells[self.row*80+self.col:(self.row+1)*80]=b' '*(80-self.col)
            return
        c&=127
        if c==27:self.state=1
        elif c==8:self.col=max(0,self.col-1)
        elif c==9:self.col=min(79,self.col+1) if self.col>=72 else (self.col+8)&~7
        elif c==10:self.lf()
        elif c==13:self.col=0
        elif 32<=c<127:self.print(c,host)
    def status(self):
        if not self.queue and self.keyboard:self.queue.append(self.keyboard.pop(0))
        return 255 if self.queue else 0
    def input(self):return self.queue.pop(0) if self.queue else self.keyboard.pop(0)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    native=out/'cpu';native.mkdir()
    shim=SHIM.replace('void io_out(BYTE l, BYTE h, BYTE d) {}',
        'BYTE wire[65536]; unsigned wirelen,badport;\n'
        'void io_out(BYTE l,BYTE h,BYTE d){if(l==1){if(wirelen<65536)wire[wirelen++]=d;}else if(l!=0x90)badport++;}')
    lib=cpu_library(native,Path.home()/'projects/git/z80pack',shim)
    mem=(C.c_ubyte*65536).in_dll(lib,'memory');wire=(C.c_ubyte*65536).in_dll(lib,'wire')
    nwire=C.c_uint.in_dll(lib,'wirelen');sp=C.c_ushort.in_dll(lib,'SP')
    regs={k:C.c_ubyte.in_dll(lib,k) for k in 'ABCDEHL'}
    assembler=Path.home()/'bin/z80asm';count=0;cases=[]
    raw='''        ASEG
        ORG 05500H
        CP 1
        JR Z,STAT
        LD A,(5581H)
        PUSH AF
        XOR A
        LD (5580H),A
        POP AF
        RET
STAT:   LD A,(5580H)
        OR A
        RET Z
        LD A,255
        RET
        END
'''
    rawcode=assemble(assembler,raw,out/'raw.bin',out/'raw.lst',0x5500)
    for backend in ('crt','host'):
        folder=out/backend;folder.mkdir()
        text='M2BANK EQU 0\nCRT_POS EQU 05700H\nCRT_COL EQU 05702H\n'+source('VT52',backend)
        code=assemble(assembler,text,folder/'native.bin',folder/'native.lst',0x8000)
        alt=assemble(assembler,text.replace('08000H','08101H'),folder/'alt.bin',folder/'alt.lst',0x8101)
        labels=symbols(folder/'native.lst');fixes=relocation_offsets(code,alt,0x101)
        for base in (0x6100,0x9200):
            C.memset(C.addressof(mem),0,65536)
            patch=bytearray(code)
            for at in fixes:patch[at:at+2]=(int.from_bytes(patch[at:at+2],'little')+base-0x8000).to_bytes(2,'little')
            mem[base:base+len(code)]=patch;mem[0x5500:0x5500+len(rawcode)]=rawcode
            mem[1:3]=(0x5500-66).to_bytes(2,'little');mem[0x5700:0x5703]=b'\0\xf8\0'
            host=backend=='host';model=Terminal();screen=pyte.Screen(80,24);stream=pyte.Stream(screen)
            def invoke(op,c=0,b=0,portable=False):
                nonlocal count
                regs['A'].value,regs['B'].value,regs['C'].value=op,b,c
                sp.value=0x4000;nwire.value=0
                result=lib.test_run(labels['D_TCAP' if portable else 'D_ENTRY']+base-0x8000,600000)
                assert result>=0 and sp.value==0x4000,(backend,op,c,result)
                assert C.c_uint.in_dll(lib,'badport').value==0
                if host:stream.feed(bytes(wire[:nwire.value]).decode('ascii'))
                count+=1;return regs['A'].value
            def equal(context):
                if host:
                    cells=bytes(ord(screen.buffer[r][c].data)|(128 if screen.buffer[r][c].reverse else 0)
                                for r in range(24) for c in range(80))
                    rc=tuple(mem[labels['H_RC']+base-0x8000:labels['H_RC']+base-0x8000+2])
                    assert rc==(screen.cursor.y,min(79,screen.cursor.x))
                else:
                    cells=bytes(mem[0xf800:0xff80]);pointer=int.from_bytes(bytes(mem[0x5700:0x5702]),'little')
                    rc=divmod(pointer-0xf800,80);assert rc[1]==mem[0x5702]
                assert rc==(model.row,model.col),(context,rc,model.row,model.col)
                assert cells==model.cells,(context,[(i,a,b) for i,(a,b) in enumerate(zip(cells,model.cells)) if a!=b][:8])
            def send(data):
                for c in data:
                    invoke(0,c);model.output(c,host);equal((backend,base,c))
            invoke(4);model.clear();equal('clear')
            for row in range(24):send(bytes((27,89,row+32,32))+bytes((65+row,))*80)
            for row in range(24):
                for col in range(80):send(bytes((27,89,row+32,col+32)))
            for row,col in ((0,0),(0,79),(23,0),(23,79),(11,39)):
                for c in range(256):send(bytes((27,89,row+32,col+32,c)));invoke(5);model.reset()
            rng=random.Random(20261108)
            send(bytes(rng.randrange(256) for _ in range(256)))
            # Real queued input/status entry paths, including whole-reply refusal
            # and a keyboard byte observed before the identification response.
            invoke(5);model.reset();send(b'\x1bZ')
            assert invoke(1)==model.status()==255
            send(b'\x1bZ')
            for _ in range(3):assert invoke(2)==model.input()
            mem[0x5580],mem[0x5581]=1,ord('x');model.keyboard=[ord('x')]
            assert invoke(1)==model.status()==255
            send(b'\x1bZ\x1bZ')
            for _ in range(4):assert invoke(2)==model.input()
            assert invoke(1)==model.status()==0
            for op in (4,5):
                before=bytes(model.cells);assert invoke(op,portable=True)==2;equal(('unsupported',op))
                assert bytes(model.cells)==before
            assert invoke(2,b=4,c=9,portable=True)==0;model.row,model.col=4,9;equal('typed move')
            assert invoke(3,portable=True)==0
            model.cells[329:400]=b' '*71;equal('typed erase')
            for op in (6,7):assert invoke(op,portable=True)==0;model.reset();equal('baseline')
            for op in range(8,256):assert invoke(op,portable=True)==255;equal(('unknown',op))
            for b,c in ((24,0),(0,80),(255,255)):
                assert invoke(2,b=b,c=c,portable=True)==3;equal('bounds')
            cases.append({'backend':backend,'base':base,'payload_bytes':len(code),
                'payload_sha256':hashlib.sha256(code).hexdigest()})
    report={'status':'PASS integrated VT52 protocol, direct operations and ordered input',
        'checks':count,'cases':cases,'reply_queue_bytes':4,
        'contract':'seven-bit VT52; out-of-range address bytes clamp; newest whole reply refused when full',
        'scope':'CPU behavioral qualification; full loader/install/native media are separate gates'}
    (out/'qualification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
