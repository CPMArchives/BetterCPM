#!/usr/bin/env python3
"""Execute the staged LBR writer with independent bytes and clobbering callbacks."""
import argparse
import binascii
import ctypes as C
import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zlib

from test_usq import Machine, SHIM
from test_lbr import archive, entry, with_crcs

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ('LW_DISCOVER','LW_PLAN','LW_RUN','LW_FIND','LW_HASH_BEGIN','IO_CB','UNUSED_CB')


class Writer(Machine):
    def __init__(self, core, image):
        super().__init__(core,image)
        self.symbols = {n:self.word(256+i*2) for i,n in enumerate(PUBLIC)}
        core.set_hooks(self.symbols['IO_CB'],0xfffe,self.hook)

    def setup(self, original=None, sources=(), flags=0, capacity=None, pattern=b'?'*11):
        self.original = original or b''
        self.sources = [data for _,data,*_ in sources]
        self.output = bytearray()
        self.ctx=0x8000
        self.mem[0x7fff:0xbb20]=bytes(0x3b21)
        self.mem[0x7fff]=self.mem[0x8068]=0xa5
        self.mem[self.ctx]=1
        self.mem[self.ctx+1]=flags | (1 if original is None else 0) | (8 if capacity is not None else 0)
        for field,value in [(2,self.symbols['IO_CB']),(4,len(sources)),(6,0xa000),(8,0x8500),
                            (10,0x8100),(12,0x8200),(14,0x8300),(16,0x8400),(18,0x8440),(20,0xbb00)]:
            self.putword(self.ctx+field,value)
        self.mem[0xbb00:0xbb0b]=pattern
        self.mem[self.ctx+22:self.ctx+25]=(len(self.original)//128).to_bytes(3,'little')
        if capacity is not None:self.mem[self.ctx+29:self.ctx+33]=capacity.to_bytes(4,'little')
        for i,(name,data,*status) in enumerate(sources):
            assert len(data)%128==0
            self.mem[0xa000+i*13:0xa000+(i+1)*13]=bytes([0,0])+name
            plan=struct.pack('<BHHI',status[0] if status else 1,len(data)//128,
                             binascii.crc_hqx(data,0),zlib.crc32(data)^0xffffffff)+bytes(3)
            self.mem[0x8500+i*12:0x8500+(i+1)*12]=plan
        self.regs['IX'].value=self.ctx;self.regs['IY'].value=0xbeef;self.regs['SP'].value=0xf000
        for i,n in enumerate(('A_','B_','C_','D_','E_','H_','L_','F_')):self.regs[n].value=31+i
        self.callback_exception=None;self.io=[];self.failure=None;self.short=False

    def callback(self, kind):
        try:
            op=self.regs['A'].value
            record=int.from_bytes(bytes(self.mem[self.ctx+68:self.ctx+71]),'little')
            at=self.word(self.ctx+71);source=self.word(self.ctx+57)
            self.io.append((op,record,source))
            if self.failure is not None and len(self.io)==self.failure:
                self.regs['A'].value=4;self.regs['F'].value=1;return
            if op==3:
                assert record*128<=len(self.output),'writer created a hole'
                self.output[record*128:record*128+128]=bytes(self.mem[at:at+128])
            else:
                raw=self.original if op==0 else self.sources[source] if op==1 else self.output
                data=raw[record*128:record*128+128]
                assert len(data)==128,(op,record,len(raw))
                self.mem[at:at+128]=data
            self.putword(self.ctx+73,127 if self.short else 128)
            self.regs['A'].value=0xa7;self.regs['F'].value=0
            for i,n in enumerate(('B','C','D','E','H','L')):self.regs[n].value=0xd1+i
        except BaseException as e:
            self.callback_exception=e;self.regs['A'].value=255;self.regs['F'].value=1

    def call(self,name):
        keys=('IX','IY','SP','A_','B_','C_','D_','E_','H_','L_','F_')
        before=[self.regs[n].value for n in keys]
        steps=self.core.test_run(self.symbols[name],20000000)
        assert steps>=0,(name,steps,hex(self.regs['PC'].value))
        assert self.callback_exception is None,self.callback_exception
        assert before==[self.regs[n].value for n in keys],name
        assert self.mem[0x7fff]==self.mem[0x8068]==0xa5,name
        assert bytes(self.mem[256:256+len(self.image)])==self.image
        return self.regs['A'].value if self.regs['F'].value&1 else 0

    def build_verify(self):
        assert self.call('LW_DISCOVER')==0
        assert self.call('LW_PLAN')==0
        assert self.call('LW_RUN')==0
        raw=bytes(self.output)
        self.mem[self.ctx+75]=1
        assert self.call('LW_RUN')==0
        assert bytes(self.output)==raw
        return raw


def members(raw):
    count=struct.unpack_from('<H',raw,14)[0]
    return [raw[at:at+32] for at in range(32,count*128,32) if raw[at]!=255]


def check_crc(raw):
    n=struct.unpack_from('<H',raw,14)[0];d=bytearray(raw[:n*128]);c=struct.unpack_from('<H',d,16)[0];d[16:18]=b'\0\0'
    assert binascii.crc_hqx(d,0)==c
    for e in members(raw):
        if e[0]:continue
        at,size=struct.unpack_from('<HH',e,12)
        assert binascii.crc_hqx(raw[at*128:(at+size)*128],0)==struct.unpack_from('<H',e,16)[0]


def tests(m):
    binary=bytes(range(256))
    m.setup(sources=[(b'BINARY  BIN',binary),(b'EMPTY      ',b'')]);raw=m.build_verify();check_crc(raw)
    assert struct.unpack_from('<H',raw,14)[0]==2 and len(raw)==512
    assert raw[256:]==binary and len(members(raw))==2
    deleted=entry(b'OLD     BIN',0xffff,0xffff,status=254)
    old=with_crcs(archive([entry(b'KEEP    BIN',1,1),deleted],b'A'*128+b'HOLE'*32))
    m.setup(old,[(b'KEEP    BIN',binary)]);raw=m.build_verify();check_crc(raw)
    assert raw[32]==254 and raw[64:96]==old[64:96]
    assert raw[128:len(old)]==old[128:] and raw[len(old):]==binary
    assert members(raw)[-1][1:12]==b'KEEP    BIN'
    m.setup(old,[(b'KEEP    BIN',binary)],flags=2);raw=m.build_verify();check_crc(raw)
    assert len(members(raw))==1 and raw[128:]==binary and len(raw)==384
    m.setup(old,flags=4,pattern=b'KEEP    BIN');raw=m.build_verify();assert raw[32]==254 and raw[128:]==old[128:]
    m.setup(old,flags=6,pattern=b'KEEP    BIN');raw=m.build_verify();check_crc(raw);assert len(raw)==128 and not members(raw)
    # Explicit rounding is physical capacity, never permission beyond C.
    m.setup(sources=[(b'A       BIN',binary)],capacity=1);raw=m.build_verify();assert len(members(raw))==1 and struct.unpack_from('<H',raw,14)[0]==1
    m.setup(sources=[(b'A       BIN',binary),(b'B       BIN',binary)],capacity=1);assert m.call('LW_DISCOVER')==0 and m.call('LW_PLAN')==7 and not m.output
    # Full directory grows/rebuilds and drops undefined deleted references.
    full=with_crcs(archive([entry(b'KEEP    BIN',1,1),deleted,deleted],b'A'*128))
    m.setup(full,[(b'NEW     BIN',binary)]);raw=m.build_verify();check_crc(raw);assert [e[1:12] for e in members(raw)]==[b'KEEP    BIN',b'NEW     BIN']
    # Accepted intermediate sources survive ordinary updates, not rebuilds.
    old=with_crcs(archive([],b'',sectors=2))
    for flags,expected in [(0,[254,0]),(2,[0])]:
        m.setup(old,[(b'SAME    BIN',b'A'*128,2),(b'SAME    BIN',binary,1)],flags=flags);raw=m.build_verify();assert [e[0] for e in members(raw)]==expected
    m.setup(sources=[(b'A       BIN',binary)]);raw=m.build_verify();m.output[-1]^=1;assert m.call('LW_RUN')==8
    m.setup(sources=[(b'A       BIN',binary)]);assert m.call('LW_DISCOVER')==m.call('LW_PLAN')==0;m.sources[0]=b'B'*256;assert m.call('LW_RUN')==8
    m.setup(old);m.short=True;assert m.call('LW_DISCOVER')==3
    m.setup(old);m.failure=1;assert m.call('LW_DISCOVER')==4


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'build/noah-lbr-writes/library');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    w=a.output.resolve();core=Path.home()/'projects/git/z80pack/z80core'
    source=' ORG 100H\n DW '+','.join(PUBLIC)+'\n'
    source+=''.join((ROOT/'src/archive'/n).read_text()+'\n' for n in ['archive.inc','lbr.mac','lbraudit.inc','lbraudit.mac','lbrwrite.inc','lbrwrite.mac'])
    source+=' LBR_CODE\n LBR_AUDIT_CODE\n LBR_WRITE_CODE\nIO_CB: RET\nUNUSED_CB: RET\n END\n'
    (w/'lib.mac').write_text(source);shutil.copy2(ROOT/'src/archive/lbrwrite-render.inc',w)
    subprocess.run([str(Path.home()/'bin/z80asm'),'-e32','-sn','-fb','-olib.bin','-llib.lst','lib.mac'],cwd=w,check=True)
    (w/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for n in ['simmem.h','simport.h']:shutil.copy2(core.parent/'z80sim/srcsim'/n,w)
    (w/'shim.c').write_text(SHIM)
    subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(w),'-I'+str(core),str(w/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(w/'core.so')],check=True)
    m=Writer(C.CDLL(str(w/'core.so')),(w/'lib.bin').read_bytes());tests(m);print('PASS: LBR writer construction, preservation, rebuild, capacity and replay verification')


if __name__=='__main__':main()
