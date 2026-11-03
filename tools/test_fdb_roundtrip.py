#!/usr/bin/env python3
"""Execute FDB.COM on the independent full Z80 core with record-level BDOS."""
import ctypes as C
from pathlib import Path
import re
import json
import hashlib
from dataclasses import replace
import shutil
import subprocess
from build_fdb import build, ROOT
from build_fdf_catalog import catalogue_payload
from fdfdecomp import decompile
from fdf_v1 import parse, serialize, crc16
from test_usq import SHIM
from test_usq_com import Command, diskkey

class FDBCommand(Command):
    def bdos(self, fn, de):
        if fn==6:
            self.polls+=1
            return 3 if self.polls==self.cancel_at else 0
        if fn==2:
            self.console+=chr(de&255);return 0
        return super().bdos(fn,de)

    def run(self, command, files, failures=None, tpa=0xd501, cancel_at=-1):
        self.polls=0;self.cancel_at=cancel_at
        self.files=dict(files);self.original=dict(files)
        self.drive,self.user=1,0
        self.failures=failures or {};self.late_existing=None
        self.attempts,self.opened,self.searches={},{},{}
        self.events,self.created,self.deleted,self.renamed=[],[],[],[]
        self.dma,self.console,self.exception=0x80,'',None
        self.mem[:]=bytes(65536)
        self.mem[0x100:0x100+len(self.image)]=self.image
        # CLI conversion never relocates the editor/viewer. Its high-memory
        # cleanup word is arbitrary real-machine RAM, not initialized data.
        cleanup=self.viewer_cleanup
        self.mem[cleanup:cleanup+2]=b'\xff\xff'
        self.mem[5]=0xc9;self.mem[6:8]=tpa.to_bytes(2,'little')
        for at in (0x5c, 0x6c):
            self.mem[at+1:at+12] = b' ' * 11
        for at,name in zip((0x5c,0x6c),command.split()):
            drive=0
            if ':' in name: drive=ord(name[0])-64;name=name[2:]
            stem,ext=name.split('.')
            self.mem[at:at+12]=bytes([drive])+stem.ljust(8).encode()+ext.ljust(3).encode()
        self.reg['SP'].value=0xd3fe
        result=self.lib.test_run(0x100,100_000_000)
        assert result>=0,('CPU budget',result,hex(self.reg['PC'].value),self.console)
        assert self.exception is None,(repr(self.exception),self.console,self.symbols,hex(self.reg["SP"].value),self.events[-8:])
        assert self.reg['SP'].value==0xd3fe
        assert self.dma==0x80
        column=peak=0
        for ch in self.console:
            if ch in '\r\n':column=0
            elif ch=='\b':column=max(0,column-1)
            elif ' '<=ch<='~':column+=1;peak=max(peak,column)
        assert peak<=80,('console exceeds80columns',peak,self.console)
        self.max_console_width=max(getattr(self,'max_console_width',0),peak)
        low=C.c_uint.in_dll(self.lib,'minimum_sp').value
        self.stack_used=max(getattr(self,'stack_used',0),self.symbols['UC_STACK_TOP']-low)
        self.cases+=1
        return self.console

def machine(work, command_class=FDBCommand):
    image=build(destination=work)
    z80pack=Path.home()/'projects/git/z80pack';core=z80pack/'z80core'
    (work/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for name in ('simmem.h','simport.h'):shutil.copy2(z80pack/'z80sim/srcsim'/name,work/name)
    (work/'shim.c').write_text(SHIM.replace('static WORD readpc, writepc;', 'static WORD readpc, writepc; unsigned int minimum_sp;').replace('PC=address; SP-=2;', 'minimum_sp=65535; PC=address; SP-=2;').replace('if(PC==65535) return i;', 'if(SP<minimum_sp) minimum_sp=SP; if(PC==65535) return i;'))
    subprocess.run(['cc','-shared','-fPIC','-O2',f'-I{work}',f'-I{core}',str(work/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(work/'core.so')],check=True)
    listing=(work/'fdb.lst').read_text()
    # Reuse the fault-injecting codec BDOS harness under its expected aliases.
    for old,new in [('UC_OLDSP','OLDSP'),('UC_STACK_TOP','STACKTOP'),('UC_STACK','STACK'),('UC_INPUT','INPUT'),('UC_TEMP','OUTPUT'),('UC_CONTEXT','MODE')]:
        match=re.search(rf'^([0-9a-f]{{4}}).*\b{new}:',listing,re.M|re.I)
        listing+=f'\n{match[1]} {old}: '

    result=command_class(C.CDLL(str(work/'core.so')),image,listing)
    result.viewer_cleanup=int(re.search(r'^([0-9a-f]{4}).*\bVIEWCLEANUP:',listing,re.M|re.I)[1],16)
    return result

def main():
    work=ROOT/'build/fdb-test';work.mkdir(parents=True,exist_ok=True)
    m=machine(work);stock=catalogue_payload()
    source=diskkey(1,'DISK.FDB');textkey=diskkey(1,'ROUND.FDF');out=diskkey(1,'ROUND.FDB')
    print(m.run('DISK.FDB ROUND.FDF',{source:stock}))
    text=m.files[textkey].split(b'\x1a',1)[0].decode()
    (work/'ROUND.FDF').write_text(text)
    assert serialize(parse(text))==stock
    print(m.run('ROUND.FDF ROUND.FDB',{textkey:m.files[textkey]}))
    assert m.files[out]==stock
    print(m.run('ROUND.FDF ROUND.FDB',{textkey:decompile(stock).encode()}))
    assert m.files[out]==stock
    # The first milestone refuses lossy encodings before creating an output.
    def repaired(raw):
        raw=bytearray(raw);raw[14:16]=bytes(2);raw[14:16]=crc16(raw).to_bytes(2,'little');return bytes(raw)
    for offset,value in ((5,1),(128+8,34)):
        bad=bytearray(stock);bad[offset]=value
        assert 'losslessly' in m.run('DISK.FDB ROUND.FDF',{source:repaired(bad)})
        assert not m.created
    bad=bytearray(stock);bad[-1]^=1
    assert 'invalid catalogue' in m.run('DISK.FDB ROUND.FDF',{source:bytes(bad)})
    assert not m.created
    # Canonical extension bytes absent from FDF are never silently discarded.
    one=bytearray(serialize(parse(decompile(stock))[:1]))
    end=128+64+one[128+55]
    one[128+58]|=128;one[128+62:128+64]=end.to_bytes(2,'little')
    one[end:end+5]=bytes((3,1,77,0,0))
    assert 'losslessly' in m.run('DISK.FDB ROUND.FDF',{source:repaired(one)})
    one[end]=0x83
    assert 'losslessly' in m.run('DISK.FDB ROUND.FDF',{source:repaired(one)})
    # Collision and failure paths preserve source/existing destination bytes.
    assert 'exists' in m.run('DISK.FDB ROUND.FDF',{source:stock,textkey:b'KEEP'})
    m.intact();assert not m.created
    for mode,data,key,destination in [('DISK.FDB ROUND.FDF',stock,source,textkey),
                                      ('ROUND.FDF ROUND.FDB',decompile(stock).encode(),textkey,out)]:
        for operation in ('open','read','make','write','close_input','close_output'):
            result=m.run(mode,{key:data},failures={operation:1})
            assert 'failed' in result,(operation,result)
            m.intact();assert destination not in m.files,(operation,result)
    text=decompile(stock)
    mutations=[text.replace('SPT 36','SPT 35',1),text.replace('BSH 4','BSH 2',1),
               text.replace('AL0 192','AL0 0',1),text.replace('OFF 2','OFF 65535',1),
               text.replace('FORMAT\n','FORMAT\nBOGUS 1\n',1),text.replace('SPT 36','SPT 65536',1),
               text.replace('SPT 36','SPT 36\nSPT 36',1)]
    for bad in mutations:
        assert bad!=text
        assert 'complete' not in m.run('ROUND.FDF ROUND.FDB',{textkey:bad.encode()})
        assert not m.created
    # Repeated identity and impossible topology are rejected too.
    items=parse(text)
    for fixture in ((items[0],items[0]),(replace(items[0],sides=1,side_order='SIDE_MAJOR'),)):
        assert 'complete' not in m.run('DISK.FDB ROUND.FDF',{source:serialize(fixture)})
        assert not m.created
    assert 'insufficient' in m.run('DISK.FDB ROUND.FDF',{source:stock},tpa=0xc7ff)
    assert not m.created
    assert 'complete' in m.run('ROUND.FDF ROUND.FDB',{textkey:text.lower().replace('description "','DESCRIPTION "').encode()})
    for command,key,data,destination in [('DISK.FDB ROUND.FDF',source,stock,textkey),
                                         ('ROUND.FDF ROUND.FDB',textkey,text.encode(),out)]:
        assert 'cancelled' in m.run(command,{key:data},cancel_at=5)
        assert destination not in m.files
        m.intact()
    assert 'cleanup failed' in m.run('DISK.FDB ROUND.FDF',{source:stock},failures={'write':1,'delete':1})
    assert textkey in m.files
    # Both semantic TLVs in one object and maximum sector-list line lengths.
    mixed=replace(items[0],psectors=255,sector_ids=tuple(range(255)),
                  secsize=1024,sector_sizes=(128,)+(1024,)*254,
                  sides=2,logical_track='CYLINDER',spt=(1+8*254)*2,
                  bsh=7,blm=127,exm=15,dsm=100,al0=128)
    fixture=serialize((mixed,))
    expected=decompile(fixture)
    assert 'complete' in m.run('ROUND.FDF ROUND.FDB',{textkey:expected.encode()})
    assert m.files[out]==fixture
    assert 'complete' in m.run('DISK.FDB ROUND.FDF',{source:fixture})
    assert serialize(parse(m.files[textkey].split(b'\x1a')[0].decode()))==fixture
    # Line endings and header whitespace accepted by the host parser.
    alternate = decompile(stock).replace('VERSION 1', 'VERSION   1').replace('\n', '\r')
    assert 'complete' in m.run('ROUND.FDF ROUND.FDB', {textkey: alternate.encode()})
    assert m.files[out] == stock
    for invalid in (text.replace('FORMAT\n', 'FORMAT\0ignored\n', 1),
                    text.replace('DESCRIPTION "', 'DESCRIPTION "\t', 1)):
        assert 'invalid' in m.run('ROUND.FDF ROUND.FDB', {textkey: invalid.encode()})
        assert not m.created
    # Capture exact resource claims from this binary rather than source estimates.
    report={'cases':m.cases,'com_bytes':len(m.image),'stock_bytes':len(stock),
            'stock_sha256':hashlib.sha256(stock).hexdigest(),'stack_bytes':m.stack_used,
            'workspace_start':0x8000,'workspace_end_exclusive':0xc800,
            'address_span_bytes':0xc800-0x100,'standard_tpa_bytes':53*1024,
            'standard_tpa_margin_bytes':53*1024-(0xc800-0x100)}
    (work/'evidence.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',report)
if __name__=='__main__':main()
