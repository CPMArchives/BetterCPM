#!/usr/bin/env python3
"""Original method-3 streaming decode: full production Z80 and independent oracle."""
from pathlib import Path
import hashlib,json,subprocess,tempfile
from test_noah_write import machine
from test_ark import member,crc16
from test_usq_com import diskkey,padded
ROOT=Path(__file__).resolve().parents[1]

def packed(raw,name=b'PACKED.BIN'):
    wire=bytearray();i=0
    while i<len(raw):
        b=raw[i];j=i+1
        while j<len(raw) and raw[j]==b and j-i<255:j+=1
        n=j-i
        if b==0x90:wire.extend(b'\x90\0'*n)
        elif n>=3:wire.extend((b,0x90,n))
        else:wire.extend(bytes([b])*n)
        i=j
    return member(bytes(wire),3,name,logical=len(raw),crc=crc16(raw))

def fixtures():
    raw=b'A'*600+bytes(range(256))*2+b'\0\x1a\x90'*43+b'Z'*257
    return raw,{'PACKED.ARC':packed(raw)+b'\x1a\0',
        'EMPTY.ARC':packed(b'',b'EMPTY.BIN')+b'\x1a\0',
        'BADCRC.ARC':member(b'A\x90\x05',3,logical=5,crc=1)+b'\x1a\0',
        'SHORT.ARC':member(b'A\x90',3,logical=5,crc=0)+b'\x1a\0',
        'LONG.ARC':member(b'A\x90\x05',3,logical=4,crc=crc16(b'A'*5))+b'\x1a\0',
        'UNDER.ARC':member(b'A',3,logical=5,crc=0)+b'\x1a\0',
        'ORPHAN.ARC':member(b'\x90\x05',3,logical=4,crc=0)+b'\x1a\0'}

def tests(m):
    m.instruction_budget=150000000
    raw,f=fixtures();src=diskkey(1,'PACKED.ARC');out=diskkey(3,'PACKED.BIN',3)
    for ceiling in (0xc501,0xca01):
        for op in ('/TEST','/X /Y'):
            t=m.run(op+' PACKED.ARC'+(' C3:' if '/X' in op else ''),{src:f['PACKED.ARC']},tpa=ceiling)
            assert m.result==1 and m.count32('NA_CRC_CHECKED')==1 and m.count32('NA_CRC_UNCHECKED')==0,t
            if '/X' in op:assert m.files[out]==padded(raw),t
            assert m.files[src]==f['PACKED.ARC'] and not m.opened,t
    for n in f:
        if n=='PACKED.ARC':continue
        t=m.run('/X /Y '+n,{diskkey(1,n):f[n]})
        if n=='EMPTY.ARC':assert m.files[diskkey(1,'EMPTY.BIN')]==b'' and m.result==1,t
        else:assert 'Outcome: failure.' in t and not m.created,t
    # A filtered corrupt member is not decoded; later framing is still checked.
    mix=f['BADCRC.ARC'][:-2]+packed(b'good',b'GOOD.BIN')+b'\x1a\0'
    t=m.run('/X /Y MIX.ARC GOOD.BIN',{diskkey(1,'MIX.ARC'):mix})
    assert m.files[diskkey(1,'GOOD.BIN')]==padded(b'good') and m.result==1,t
    # Discarded candidate stages restart decoder state, not the raw cursor alone.
    for keys in ('R','S'):
        t=m.run('/X PACKED.ARC C3:',{src:f['PACKED.ARC']},failures={'write':1},keys=keys)
        if keys=='R':assert m.files[out]==padded(raw),t
        else:assert out not in m.files,t
    t=m.run('/X /Y PACKED.ARC C3:',{src:f['PACKED.ARC'],out:b'ORIGINAL'},tamper=True)
    assert m.files[out]==b'ORIGINAL',t
    # Long literals cross stored input records, output records and 16-bit counts.
    large=bytes(range(256))*257
    t=m.run('/X /Y BIG.ARC',{diskkey(1,'BIG.ARC'):packed(large)+b'\x1a\0'})
    assert m.files[diskkey(1,'PACKED.BIN')]==padded(large),t
    # Zero CRC is present, and runs/count-one/escaped marker state are explicit.
    for wire,data in ((b'\0\x90\xff',bytes(255)),(b'A\x90\x01B',b'AB'),(b'\x90\0\x90\x03',b'\x90'*3)):
        t=m.run('/X /Y ONE.ARC',{diskkey(1,'ONE.ARC'):member(wire,3,logical=len(data),crc=crc16(data))+b'\x1a\0'})
        assert m.files[diskkey(1,'FILE.BIN')]==padded(data),t
    print(f'PASS: {m.cases} method-3 production transactions; stack {m.max_stack}')

def oracle():
    exe=ROOT/'build/noah-proof/references/deark-c19b47c80a5ff8a7b41eb4f578e1afdda99202a2/deark'
    raw,f=fixtures()
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'input.arc').write_bytes(f['PACKED.ARC'])
        r=subprocess.run([str(exe),'-od',str(p),str(p/'input.arc')],capture_output=True,check=True)
        outputs=list(p.glob('*PACKED.BIN'))+list(p.glob('*packed.bin'))
        assert len(outputs)==1 and outputs[0].read_bytes()==raw,(r.stdout,r.stderr,list(p.iterdir()))
    print('PASS: pinned independent Deark method-3 output oracle')

if __name__=='__main__':tests(machine());oracle()
