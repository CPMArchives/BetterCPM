#!/usr/bin/env python3
"""Exercise original Z80 ARC framing/stored CRC code with independent fixtures."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
from test_lbr import Reader
from noah_overlays import assemble

ROOT=Path(__file__).resolve().parents[1]
ENTRIES=('ARK_OPEN','ARK_NEXT','ARK_RAW','ARK_CLOSE','READ_CB','WRITE_CB','ARK_TEST_STORED','ARK_BUILD_HEADER','ARK_WRITE_MEMBER','ARK_WRITE_END','ARK_COPY_MEMBER')


def crc16(data):
    crc=0
    for v in data:
        crc^=v
        for _ in range(8):crc=(crc>>1)^(0xa001 if crc&1 else 0)
    return crc


def member(data=b'',method=2,name=b'FILE.BIN',logical=None,crc=None):
    head=bytes([26,method])+name.ljust(13,b'\0')
    head+=struct.pack('<IHHH',len(data),0,0,crc16(data) if crc is None else crc)
    if method!=1:head+=struct.pack('<I',len(data) if logical is None else logical)
    return head+data


class ArkReader(Reader):
    instruction_budget=30000000
    def __init__(self,core,image):
        super().__init__(core,image)
        self.symbols={n:self.word(0x100+2*i) for i,n in enumerate(ENTRIES)}
        core.set_hooks(self.symbols['READ_CB'],self.symbols['WRITE_CB'],self.hook)
    def configure(self,*args,**kwargs):
        self.cancel_offsets=set()
        self.output=bytearray()
        self.write_error=None
        return super().configure(*args,**kwargs)
    def callback(self,kind):
        try:
            if kind==1:
                offset=int.from_bytes(bytes(self.mem[self.ctx+16:self.ctx+20]),'little')
                count=self.word(self.ctx+22)
                buffer=self.word(self.ctx+20)
                if self.write_error==offset:
                    self.regs['A'].value=255;self.regs['F'].value=1
                    return
                assert offset==len(self.output),(offset,len(self.output))
                self.output.extend(bytes(self.mem[buffer:buffer+count]))
                self.putword(self.ctx+24,count)
                self.regs['A'].value=0;self.regs['F'].value=0
                return
            offset=int.from_bytes(bytes(self.mem[self.ctx+16:self.ctx+20]),'little')
            count=self.word(self.ctx+22)
            assert offset+count<=int.from_bytes(bytes(self.mem[self.ctx+6:self.ctx+10]),'little'),(offset,count)
            super().callback(kind)
            if offset in self.cancel_offsets:
                self.regs['A'].value=11;self.regs['F'].value=1
        except BaseException as error:
            self.callback_exception=error
            self.regs['A'].value=255;self.regs['F'].value=1



def build(out):
    out.mkdir(parents=True,exist_ok=True)
    source=' ORG 100H\n'+''.join((ROOT/'src/archive'/n).read_text()+'\n' for n in ('archive.inc','ark.inc','ark.mac','arkwrite.inc','arkwrite.mac'))
    source+=''.join(' DW '+name+'\n' for name in ENTRIES)+' ARK_CODE\n ARK_WRITE_CODE\nREAD_CB: RET\nWRITE_CB: RET\n END\n'
    raw,_=assemble(Path.home()/'bin/z80asm',out,'ARKTEST',source)
    core=Path.home()/'projects/git/z80pack/z80core'
    (out/'sim.h').write_text('#define DEF_CPU Z80\n#define EXCLUDE_I8080\n')
    for n in ('simmem.h','simport.h'):shutil.copy2(core.parent/'z80sim/srcsim'/n,out/n)
    from test_usq import SHIM
    (out/'shim.c').write_text(SHIM)
    subprocess.run(['cc','-shared','-fPIC','-O2','-I'+str(out),'-I'+str(core),str(out/'shim.c'),str(core/'simglb.c'),*map(str,sorted(core.glob('simz80*.c'))),'-o',str(out/'core.so')],check=True)
    return ArkReader(C.CDLL(str(out/'core.so')),raw)


def tests(m):
    assert crc16(b'123456789')==0xbb3d
    m.configure(b'\x1a\0');assert m.call('ARK_OPEN')==0 and m.call('ARK_NEXT')==1
    before=m.reads;assert m.call('ARK_NEXT')==1 and m.reads==before
    assert m.call('ARK_CLOSE')==0 and m.call('ARK_NEXT')==6
    for method,data in ((1,b''),(1,bytes(range(256))),(2,b'123456789'),(2,b'\0'*129),(2,bytes(range(256))*257)):
        m.configure(member(data,method=method)+b'\x1a\0')
        assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
        meta=m.member();assert meta[:11]==b'FILE    BIN' and meta[11]==3
        assert int.from_bytes(meta[20:24],'little')==len(data)==int.from_bytes(meta[24:28],'little')
        assert meta[41]==1 and meta[30:32]==struct.pack('<H',crc16(data))
        before=m.reads;assert m.call('ARK_RAW',0)==0 and m.reads==before
        assert m.call('ARK_TEST_STORED')==0
        assert m.call('ARK_NEXT')==1
    for method in range(3,10):
        m.configure(member(b'opaque',method=method,logical=123)+member(b'next',name=b'NEXT')+b'\x1a\0')
        assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
        assert m.member()[28]==method and int.from_bytes(m.member()[24:28],'little')==123
        assert m.call('ARK_RAW',3)==0 and bytes(m.mem[0x6001:0x6004])==b'opa'
        assert m.call('ARK_NEXT')==0 and m.member()[:11]==b'NEXT       '
        assert m.call('ARK_TEST_STORED')==0 and m.call('ARK_NEXT')==1
    for suffix,flag in ((b'',0),(b'\x1a\0'*100,1),(b'\x1a'*3+b'opaque',2)):
        m.configure(member(b'abc')+b'\x1a\0'+suffix)
        assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
        assert m.call('ARK_NEXT')==1 and m.mem[m.ctx+15]==flag
        assert int.from_bytes(bytes(m.mem[m.ctx+26:m.ctx+30]),'little')==34
    for name in (b'foo.txt',b'README',b'EIGHT888.123'):
        m.configure(member(b'abc',name=name)+b'\x1a\0')
        assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0,name
    for name in (b'',b'../A',b'A:B',b'FILE..TXT',b'LONGNAME9',b'A.LONG',b'A B',b'FILE\xff',b'NO-NULL-12345'):
        m.configure(member(name=name)+b'\x1a\0')
        assert m.call('ARK_OPEN')==0 and m.call('ARK_NEXT')==2,name
    for malformed in (b'',b'\x1a',b'junk',b'\x1a\x0a',b'\x1a\x80'):
        m.configure(malformed);status=m.call('ARK_OPEN');assert status in (2,3,13),(malformed,status)
        assert m.call('ARK_NEXT')==status
    good=member(b'abc')+b'\x1a\0'
    for cut in (2,15,24,28,29,31,32,33):
        m.configure(good[:cut]);assert m.call('ARK_OPEN')==0
        status=m.call('ARK_NEXT')
        if cut>=32:assert status==0 and m.call('ARK_NEXT')==3,cut
        else:assert status==3,cut
    m.configure(member(b'abc',logical=4)+b'\x1a\0');assert m.call('ARK_OPEN')==0 and m.call('ARK_NEXT')==2
    m.configure(member(b'abc',crc=0)+b'\x1a\0');assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    assert m.call('ARK_TEST_STORED')==8 and m.call('ARK_NEXT')==8
    m.configure(member(b'abc',method=8)+b'\x1a\0');assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    assert m.call('ARK_TEST_STORED')==13 and m.call('ARK_NEXT')==13
    for failure,expected in (('read_error',4),('short',3)):
        m.configure(good);assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
        setattr(m,failure,29);assert m.call('ARK_TEST_STORED')==expected
        assert m.call('ARK_RAW',1)==expected and m.call('ARK_NEXT')==expected
    m.configure(good);m.mem[m.ctx]=2;before=bytes(m.mem[m.ctx:m.ctx+138]);assert m.call('ARK_OPEN')==5
    assert bytes(m.mem[m.ctx:m.ctx+138])==before
    # Full 32-bit extent arithmetic rejects overflow before a source callback.
    raw=bytearray(member(b'abc'));raw[15:19]=b'\xff'*4;raw[25:29]=b'\xff'*4
    m.configure(bytes(raw)+b'\x1a\0');assert m.call('ARK_OPEN')==0 and m.call('ARK_NEXT')==7
    m.configure(good);assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    before=m.reads;assert m.call('ARK_RAW',2,0xffff)==7 and m.reads==before
    m.configure(good);assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    m.cancel_offsets={29};assert m.call('ARK_TEST_STORED')==11 and m.call('ARK_NEXT')==11
    m.configure(good+b'\x1a'*50);assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    m.read_error=len(good);assert m.call('ARK_NEXT')==4 and m.call('ARK_NEXT')==4
    # Two caller-owned contexts can be interleaved without hidden iterator state.
    m.configure(good,address=0x8003);assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    assert m.call('ARK_RAW',1)==0
    m.configure(good,address=0x9003);assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    assert m.call('ARK_RAW',2)==0
    m.ctx=0x8003;m.regs['IX'].value=m.ctx
    assert m.call('ARK_RAW',2)==0 and bytes(m.mem[0x6001:0x6003])==b'bc'
    m.ctx=0x9003;m.regs['IX'].value=m.ctx
    assert m.call('ARK_RAW',2)==0 and bytes(m.mem[0x6001:0x6002])==b'c'
    print(f'PASS: {m.cases} ARC reader cases; {len(m.image)-16} library bytes; 138-byte context')


def writer_headers(m):
    def canonical(name):
        base, dot, ext = name.partition('.')
        return (base.upper().ljust(8) + (ext.upper().ljust(3) if dot else '   ')).encode('ascii')

    for method, name, logical, crc, dates, payload in (
            (2, 'README.TXT', 28, 0xBEEF, b'\x34\x12\x78\x56', b'A'*28),
            (4, 'NOEXT', 0, 0, bytes(4), b''),
            (8, 'LONGNAME.DAT', 0x01020304, 0, b'\x00\x80\xFF\x7F', b'encoded-body')):
        m.configure(b'\x1a\x00')
        c=m.ctx
        stored=len(payload)
        m.mem[c+74:c+85]=canonical(name)
        m.mem[c+102]=method
        m.mem[c+94:c+98]=stored.to_bytes(4,'little')
        m.mem[c+98:c+102]=logical.to_bytes(4,'little')
        m.mem[c+104:c+106]=crc.to_bytes(2,'little')
        m.mem[c+106:c+110]=dates
        before=(m.regs['IX'].value,m.regs['IY'].value,m.regs['SP'].value)
        steps=m.core.test_run(m.symbols['ARK_BUILD_HEADER'],1_000_000)
        assert steps>=0 and not m.callback_exception, (name,steps,m.callback_exception)
        assert before==(m.regs['IX'].value,m.regs['IY'].value,m.regs['SP'].value)
        assert m.regs['A'].value==29 and (m.regs['F'].value&1)==0
        # The serializer's five-byte non-reentrant scratch is statically
        # allocated with the linked library and is intentionally writable.
        m.image=bytes(m.mem[0x100:0x100+len(m.image)])
        header=bytes(m.mem[c+42:c+71])
        dotted=name.upper().encode('ascii')
        name_field=dotted.ljust(13,b'\0')
        expected=(bytes((26,method))+name_field+struct.pack('<IHHH',stored,*struct.unpack('<HH',dates),crc)+struct.pack('<I',logical))
        assert header==expected,(name,header.hex(),expected.hex())
        # The production reader must consume the serialized member and return
        # the exact stored name/method/length/CRC/date fields.
        m.configure(header+payload+b'\x1a\0')
        assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0,name
        meta=m.member()
        normalized=canonical(name)
        assert meta[:11]==normalized and meta[28]==method,(name,meta[:32].hex())
        assert meta[20:24]==stored.to_bytes(4,'little')
        assert meta[24:28]==logical.to_bytes(4,'little')
        assert meta[30:32]==crc.to_bytes(2,'little') and meta[32:36]==dates

    for method, rawname, status in ((1,b'FILE    BIN',13),(2,b'BAD NAME',2),
                                    (2,b'NAME    B D',2),(2,b'BAD?    TXT',2),
                                    (4,b'        TXT',2)):
        m.configure(b'\x1a\x00')
        c=m.ctx
        m.mem[c+42:c+71]=b'\xE5'*29
        m.mem[c+74:c+85]=rawname.ljust(11,b' ')
        m.mem[c+102]=method
        before=bytes(m.mem[c+42:c+71])
        m.core.test_run(m.symbols['ARK_BUILD_HEADER'],1_000_000)
        m.image=bytes(m.mem[0x100:0x100+len(m.image)])
        assert m.regs['F'].value&1,(method,rawname)
        assert m.regs['A'].value==status,(method,rawname,m.regs['A'].value)
        assert bytes(m.mem[c+42:c+71])==before,(method,rawname)
    m.configure(b'\x1a\0')
    c=m.ctx
    m.mem[c+74:c+85]=canonical('WIDE.DAT')
    m.mem[c+102]=8
    m.mem[c+94:c+98]=(0xF1234567).to_bytes(4,'little')
    m.mem[c+98:c+102]=(0x89ABCDEF).to_bytes(4,'little')
    m.mem[c+104:c+106]=b'\xCD\xAB'
    m.mem[c+106:c+110]=b'\x11\x22\x33\x44'
    m.core.test_run(m.symbols['ARK_BUILD_HEADER'],1_000_000)
    m.image=bytes(m.mem[0x100:0x100+len(m.image)])
    header=bytes(m.mem[c+42:c+71])
    assert header[15:19]==bytes.fromhex('674523f1')
    assert header[19:23]==b'\x11\x22\x33\x44'
    assert header[23:25]==b'\xCD\xAB'
    assert header[25:29]==bytes.fromhex('efcdab89')
    print('PASS: ARC writer serializes method-2/4/8 headers and production reader round-trips metadata; rejects malformed names/methods')


def writer_stream(m):
    def raw_call(name):
        steps=m.core.test_run(m.symbols[name],30_000_000)
        assert steps>=0,(name,steps,hex(m.regs['PC'].value))
        assert not m.callback_exception,m.callback_exception
        m.image=bytes(m.mem[0x100:0x100+len(m.image)])
        return m.regs['A'].value if m.regs['F'].value&1 else 0

    def call(name):
        result=raw_call(name)
        assert result==0,(name,result)
        return result

    def configure_member(source,payload,prefix):
        m.configure(source)
        c=m.ctx
        m.putword(c+20,0x7000)
        m.mem[c+74:c+85]=b'STREAM  BIN'
        m.mem[c+74+16:c+74+20]=len(prefix).to_bytes(4,'little')
        m.mem[c+74+20:c+74+24]=len(payload).to_bytes(4,'little')
        m.mem[c+74+24:c+74+28]=len(payload).to_bytes(4,'little')
        m.mem[c+74+28]=2
        m.mem[c+74+30:c+74+32]=crc16(payload).to_bytes(2,'little')
        m.putword(c+74+36,m.symbols['WRITE_CB'])
        m.mem[c+74+42:c+74+46]=bytes(4)
        return c

    payload=bytes(range(256))*2+b'last bytes'
    prefix=b'ignored-prefix'
    c=configure_member(prefix+payload+b'ignored-suffix',payload,prefix)
    before=(m.regs['IX'].value,m.regs['IY'].value,m.regs['SP'].value)
    assert call('ARK_WRITE_MEMBER')==0
    assert before==(m.regs['IX'].value,m.regs['IY'].value,m.regs['SP'].value)
    expected=member(payload,name=b'STREAM.BIN')
    assert bytes(m.output)==expected
    assert int.from_bytes(bytes(m.mem[c+74+42:c+74+46]),'little')==len(expected)
    assert call('ARK_WRITE_END')==0
    assert bytes(m.output)==expected+b'\x1a\0'
    assert int.from_bytes(bytes(m.mem[c+74+42:c+74+46]),'little')==len(expected)+2
    emitted=bytes(m.output)
    m.configure(emitted)
    assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    assert m.call('ARK_TEST_STORED')==0 and m.call('ARK_NEXT')==1

    # Empty input still emits a valid header and terminator without reading.
    m.configure(b'')
    c=m.ctx
    m.putword(c+20,0x7000)
    m.mem[c+74:c+74+11]=b'EMPTY   TXT'
    m.mem[c+74+20:c+74+28]=bytes(8)
    m.mem[c+74+28]=2
    m.putword(c+74+36,m.symbols['WRITE_CB'])
    assert call('ARK_WRITE_MEMBER')==0
    expected=member(b'',name=b'EMPTY.TXT')
    assert bytes(m.output)==expected
    assert call('ARK_WRITE_END')==0 and bytes(m.output)==expected+b'\x1a\0'

    # A read failure or short transfer leaves only an unpublishable header.
    c=configure_member(prefix+payload,payload,prefix)
    m.read_error=len(prefix)
    assert raw_call('ARK_WRITE_MEMBER')==4
    assert len(m.output)==29
    assert int.from_bytes(bytes(m.mem[c+74+42:c+74+46]),'little')==29
    c=configure_member(prefix+payload,payload,prefix)
    m.short=len(prefix)
    assert raw_call('ARK_WRITE_MEMBER')==3
    assert len(m.output)==29
    # A body write failure reports AS_OUTPUT and does not advance the output
    # cursor or remaining-byte count for that chunk.
    c=configure_member(prefix+payload,payload,prefix)
    m.write_error=29
    assert raw_call('ARK_WRITE_MEMBER')==12
    assert len(m.output)==29
    assert int.from_bytes(bytes(m.mem[c+74+42:c+74+46]),'little')==29
    assert int.from_bytes(bytes(m.mem[c+74+46:c+74+50]),'little')==len(payload)

    # Updates can retain members whose codec is opaque to this writer. Copy
    # the original header and stored stream exactly, including legacy method 1.
    for method in (1,2,4,5,8,9):
        stored=bytes(range(251))*3+b'opaque-tail'
        original=member(stored,method=method,name=b'RETAIN.DAT',logical=len(stored) if method==2 else 777)
        m.configure(original+b'\x1a\0')
        c=m.ctx
        opened=m.call('ARK_OPEN');selected=m.call('ARK_NEXT')
        assert opened==selected==0,(method,opened,selected,original[:29])
        m.putword(c+20,0x7000)
        m.putword(c+74+36,m.symbols['WRITE_CB'])
        m.mem[c+74+42:c+74+46]=bytes(4)
        assert call('ARK_COPY_MEMBER')==0
        assert bytes(m.output)==original
        assert int.from_bytes(bytes(m.mem[c+74+42:c+74+46]),'little')==len(original)
        assert call('ARK_WRITE_END')==0
        assert bytes(m.output)==original+b'\x1a\0'

    # A reader failure after copying the header leaves only an unpublished
    # partial file; a destination failure does not advance the write cursor.
    retained=member(payload,method=8,name=b'RETAIN.DAT',logical=999)
    m.configure(retained+b'\x1a\0');c=m.ctx
    assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    m.putword(c+20,0x7000);m.putword(c+74+36,m.symbols['WRITE_CB'])
    m.read_error=29
    assert raw_call('ARK_COPY_MEMBER')==4 and len(m.output)==29
    m.configure(retained+b'\x1a\0');c=m.ctx
    assert m.call('ARK_OPEN')==m.call('ARK_NEXT')==0
    m.putword(c+20,0x7000);m.putword(c+74+36,m.symbols['WRITE_CB'])
    m.write_error=29
    assert raw_call('ARK_COPY_MEMBER')==12 and len(m.output)==29
    assert int.from_bytes(bytes(m.mem[c+74+42:c+74+46]),'little')==29
    print('PASS: ARC writer streams new members and preserves opaque retained member bytes exactly; errors prevent cursor advancement')


def historical(m,out):
    pins=json.loads((ROOT/'tests/fixtures/noah/references.json').read_text())['artifacts']
    from noah_compatibility import inventory
    result={}
    for name in ('crc32a.arc','de-lbr.arc','nulu15.arc'):
        raw=(ROOT/'build/noah-proof/references'/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==pins[name]['sha256']
        oracle=inventory(raw);m.configure(raw);assert m.call('ARK_OPEN')==0
        found=[]
        while True:
            status=m.call('ARK_NEXT')
            if status:assert status==1,(name,status);break
            meta=m.member();found.append((meta[:11],meta[28],int.from_bytes(meta[20:24],'little'),int.from_bytes(meta[24:28],'little')))
        expected=[]
        for e in oracle['members']:
            base,_,ext=e['name'].upper().partition('.')
            expected.append((base.encode().ljust(8)+ext.encode().ljust(3),e['method'],e['stored_bytes'],e['decoded_bytes']))
        assert found==expected,(name,found,expected)
        flag=m.mem[m.ctx+15]
        result[name]={'sha256':pins[name]['sha256'],'members':len(found),'methods':sorted(set(x[1] for x in found)),'trailer_flag':flag,'decoded_by_reader':False}
    (out/'historical.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: three pinned historical ARC inventories; opaque trailer reported')

if __name__=='__main__':
    out=ROOT/'build/ark-reader/host';m=build(out);tests(m);writer_headers(m);writer_stream(m);historical(m,out)
