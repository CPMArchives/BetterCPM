#!/usr/bin/env python3
"""ARC method 4 production decoding, tree safety, save resets and oracle parity."""
from pathlib import Path
import struct,subprocess,tempfile
from test_noah_write import machine
from test_ark import member,crc16
from test_usq import squeeze,squeeze_tokens
from test_usq_com import diskkey,padded
ROOT=Path(__file__).resolve().parents[1]

def squeezed(raw,name=b'SQUEEZED.BIN',shuffle=True):
    sq=squeeze(raw,name=b'',shuffle=shuffle)
    return member(sq[5:],4,name,logical=len(raw),crc=crc16(raw))

def tree(nodes,payload=b''):
    return struct.pack('<H',len(nodes))+b''.join(struct.pack('<hh',*n) for n in nodes)+payload

def encoded(body,raw=b'',crc=None,logical=None):
    return member(body,4,logical=len(raw) if logical is None else logical,crc=crc16(raw) if crc is None else crc)+b'\x1a\0'

def fixtures():
    raw=b'A'*600+bytes(range(256))*2+b'\0\x1a\x90'*43+b'Z'*257
    return raw,{'SQUEEZED.ARC':squeezed(raw)+b'\x1a\0',
        'EMPTY.ARC':squeezed(b'',b'EMPTY.BIN')+b'\x1a\0',
        'BADCRC.ARC':encoded(tree([(-66,-257)],b'\x02'),b'A',crc=1),
        'BADLINK.ARC':encoded(tree([(1,-257)],b'\0')),
        'CYCLE.ARC':encoded(tree([(0,-257)],b'\0')),
        'NOEOF.ARC':encoded(tree([(-66,-67)],b'\0')),
        'SHORT.ARC':encoded(b'\x01\0\xff'),
        'BADLEAF.ARC':encoded(tree([(-258,-257)],b'\0')),
        'UNDER.ARC':encoded(tree([(-66,-257)],b'\x02'),b'AA'),
        'LONG.ARC':encoded(tree([(-66,-257)],b'\x02')),
        'TAIL.ARC':encoded(tree([(-66,-257)],b'\x02EXTRA'),b'A')}

def tests(m):
    m.instruction_budget=150000000
    raw,f=fixtures();src=diskkey(1,'SQUEEZED.ARC');out=diskkey(3,'SQUEEZED.BIN',3)
    for ceiling in (0xc501,0xca01):
        for op in ('/TEST','/X /Y'):
            t=m.run(op+' SQUEEZED.ARC'+(' C3:' if '/X' in op else ''),{src:f['SQUEEZED.ARC']},tpa=ceiling)
            assert 'Outcome: success.' in t and 'verified 00000001; unavailable/ambiguous: 00000000' in t,t
            if '/X' in op:assert m.files[out]==padded(raw),t
            assert m.files[src]==f['SQUEEZED.ARC'] and not m.opened,t
    for n,b in f.items():
        if n=='SQUEEZED.ARC':continue
        t=m.run('/X /Y '+n,{diskkey(1,n):b})
        if n=='EMPTY.ARC':assert m.files[diskkey(1,'EMPTY.BIN')]==b'' and 'Outcome: success.' in t,t
        else:assert 'Outcome: failure.' in t and not m.created,t
    malformed=[b'\x01\x01',b'\xff\xff',tree([(1,1),(-66,-257)],b'\0'),
        tree([(-66,-257),(-67,-257)],b'\x02'),tree([(-66,-257)]),b'\0\0extra']
    for body in malformed:
        t=m.run('/X /Y BAD.ARC',{diskkey(1,'BAD.ARC'):encoded(body)})
        assert 'Outcome: failure.' in t and not m.created,t
    # A Huffman EOF cannot silently complete a pending RLE escape.
    sq=squeeze_tokens([0x90],0,name=b'')
    t=m.run('/X /Y BAD.ARC',{diskkey(1,'BAD.ARC'):encoded(sq[5:])})
    assert 'Outcome: failure.' in t and not m.created,t
    # Maximum 256-node tree/depth, arbitrary numbering and zero-valued CRC.
    nodes=[(-1,i+1) for i in range(255)]+[(-1,-257)]
    t=m.run('/TEST DEEP.ARC',{diskkey(1,'DEEP.ARC'):encoded(tree(nodes,b'\xff'*32))})
    assert 'Outcome: success.' in t,t
    t=m.run('/X /Y ZERO.ARC',{diskkey(1,'ZERO.ARC'):squeezed(bytes(255))+b'\x1a\0'})
    assert m.files[diskkey(1,'SQUEEZED.BIN')]==padded(bytes(255)),t
    mix=f['CYCLE.ARC'][:-2]+squeezed(b'good',b'GOOD.BIN')+b'\x1a\0'
    t=m.run('/X /Y MIX.ARC GOOD.BIN',{diskkey(1,'MIX.ARC'):mix})
    assert m.files[diskkey(1,'GOOD.BIN')]==padded(b'good') and 'Outcome: success.' in t,t
    for keys in ('R','S'):
        t=m.run('/X SQUEEZED.ARC C3:',{src:f['SQUEEZED.ARC']},failures={'write':1},keys=keys)
        if keys=='R':assert m.files[out]==padded(raw),t
        else:assert out not in m.files,t
    t=m.run('/X /Y SQUEEZED.ARC C3:',{src:f['SQUEEZED.ARC'],out:b'ORIGINAL'},tamper=True)
    assert m.files[out]==b'ORIGINAL',t
    t=m.run('/X /Y SQUEEZED.ARC',{src:f['SQUEEZED.ARC']},cancel_poll=30)
    assert 'cancel' in t.lower() and not m.created,t
    print(f'PASS: {m.cases} method-4 production transactions; stack {m.max_stack}')

def oracle():
    exe=ROOT/'build/noah-proof/references/deark-c19b47c80a5ff8a7b41eb4f578e1afdda99202a2/deark'
    raw,f=fixtures()
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'input.arc').write_bytes(f['SQUEEZED.ARC'])
        r=subprocess.run([str(exe),'-od',str(p),str(p/'input.arc')],capture_output=True,check=True)
        out=list(p.glob('*SQUEEZED.BIN'))+list(p.glob('*squeezed.bin'))
        assert len(out)==1 and out[0].read_bytes()==raw,(r.stdout,r.stderr,list(p.iterdir()))
    print('PASS: pinned independent Deark method-4 output oracle')

if __name__=='__main__':tests(machine());oracle()
