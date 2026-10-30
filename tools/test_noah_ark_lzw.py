#!/usr/bin/env python3
"""ARC 5-9 independent vectors, production Z80 and pinned host oracles."""
from pathlib import Path
import hashlib,json,random,struct,subprocess,tempfile
from test_noah_write import machine
from test_ark import member,crc16
from test_noah_ark_packed import packed
from test_usq_com import diskkey,padded
ROOT=Path(__file__).resolve().parents[1]

def rle(raw):return packed(raw)[29:]

def static_codes(data,method):
    prefix=[None]*4096;chain=[0]*4096;phrase={}
    def add(parent,value):
        key=(parent+value)&65535
        h=(key*15073)&4095 if method==7 else (((key|2048)**2)>>6)&4095
        if prefix[h] is not None:
            while chain[h]:h=chain[h]
            tail=h;h=(h+101)&4095
            while prefix[h] is not None:h=(h+1)&4095
            chain[tail]=h
        prefix[h]=parent;chain[h]=0
        return h
    for v in range(256):phrase[bytes([v])]=add(65535,v)
    count=256;codes=[];w=b''
    for v in data:
        c=bytes([v])
        if w+c in phrase:w+=c;continue
        codes.append(phrase[w])
        if count<4096:
            phrase[w+c]=add(phrase[w],v);count+=1
        w=c
    if w:codes.append(phrase[w])
    bits=''.join(f'{c:012b}' for c in codes)
    bits+='0'*(-len(bits)%8)
    return bytes(int(bits[i:i+8],2) for i in range(0,len(bits),8))

def dynamic_codes(data,maxbits,clear_at=None):
    segments=[data] if clear_at is None else [data[:clear_at],data[clear_at:]]
    codes=[]
    for si,segment in enumerate(segments):
        if si:codes.append(256)
        table={bytes([i]):i for i in range(256)};n=257;w=b''
        for v in segment:
            c=bytes([v])
            if w+c in table:w+=c;continue
            codes.append(table[w])
            if n<(1<<maxbits):table[w+c]=n;n+=1
            w=c
        if w:codes.append(table[w])
    width=9;n=257;have=False;group=[];out=bytearray()
    def flush(full):
        if not group:return
        value=sum(c<<(i*width) for i,c in enumerate(group))
        out.extend(value.to_bytes(width if full else (len(group)*width+7)//8,'little'));group.clear()
    for c in codes:
        group.append(c)
        if len(group)==8:flush(True)
        if c==256:
            flush(True);width=9;n=257;have=False
        elif not have:have=True
        elif n<(1<<maxbits):
            n+=1
            if n==(1<<width) and width<maxbits:flush(True);width+=1
    flush(False)
    return bytes(out)

def lzw(raw,method,name=None,clear_at=None):
    tokens=rle(raw) if method in (6,7,8) else raw
    if method<8:body=static_codes(tokens,method)
    else:body=dynamic_codes(tokens,12 if method==8 else 13,clear_at=clear_at)
    if method==8:body=b'\x0c'+body
    return member(body,method,name or f'M{method}.BIN'.encode(),logical=len(raw),crc=crc16(raw))

def fixtures():
    raw=b'ABABABA'*20+bytes(range(256))+b'\0\x1a\x90'*9+b'Z'*300
    return raw,{f'LZW{i}.ARC':lzw(raw,i)+b'\x1a\0' for i in range(5,10)}

def tests(m):
    m.instruction_budget=450000000
    raw,f=fixtures()
    for method in range(5,10):
        n=f'LZW{method}.ARC';src=diskkey(1,n)
        t=m.run('/TEST '+n,{src:f[n]},tpa=0xc501)
        assert m.result==1 and m.count32('NA_CRC_CHECKED')==1 and m.count32('NA_CRC_UNCHECKED')==0,t
        t=m.run('/X /Y '+n+' C3:',{src:f[n]},tpa=0xca01)
        assert m.files[diskkey(3,f'M{method}.BIN',3)]==padded(raw),t
        assert m.files[src]==f[n] and not m.opened,t
    rng=random.Random(517);large=bytes(rng.randrange(256) for _ in range(20000))
    for method in range(5,10):
        t=m.run('/X /Y FULL.ARC',{diskkey(1,'FULL.ARC'):lzw(large,method)+b'\x1a\0'},tpa=0xc501)
        assert m.files[diskkey(1,f'M{method}.BIN')]==padded(large),t
    for method in (8,9):
        t=m.run('/X /Y CLEAR.ARC',{diskkey(1,'CLEAR.ARC'):lzw(large,method,clear_at=719)+b'\x1a\0'})
        assert m.files[diskkey(1,f'M{method}.BIN')]==padded(large),t
    for method in (5,9):
        long=b'A'*20000
        t=m.run('/X /Y LONG.ARC',{diskkey(1,'LONG.ARC'):lzw(long,method)+b'\x1a\0'})
        assert m.files[diskkey(1,f'M{method}.BIN')]==padded(long),t
    for method in range(5,10):
        src=diskkey(1,'BAD.ARC');bad=bytearray(f[f'LZW{method}.ARC']);bad[23]^=1
        t=m.run('/X /Y BAD.ARC',{src:bytes(bad)})
        assert 'Archive/read error 08' in t and not m.created,t
    for method,body in ((5,b'\xff'),(7,b'\xff'),(8,b'\x0c\x2c\x01'),(9,b'\x2c\x01'),(8,b'\x0d')):
        wire=member(body,method,logical=1,crc=crc16(b'A'))+b'\x1a\0'
        t=m.run('/X /Y BAD.ARC',{diskkey(1,'BAD.ARC'):wire})
        assert 'Outcome: failure.' in t and not m.created,t
    for method in (8,9):
        t=m.run('/X /Y EMPTY.ARC',{diskkey(1,'EMPTY.ARC'):lzw(b'',method)+b'\x1a\0'})
        assert m.files[diskkey(1,f'M{method}.BIN')]==b'',t
    src=diskkey(2,'ONE.ARC',7);target=diskkey(3,'M9.BIN',3)
    for failure,keys in (({'write':1},'R'),({'write':1},'S'),({'write':2},'R')):
        t=m.run('/X B7:ONE.ARC C3:',{src:f['LZW9.ARC']},failures=failure,keys=keys)
        if keys=='R':assert m.files[target]==padded(raw),t
        else:assert target not in m.files,t
    t=m.run('/X /Y B7:ONE.ARC C3:',{src:f['LZW9.ARC'],target:b'ORIGINAL'},tamper=True)
    assert m.files[target]==b'ORIGINAL',t
    t=m.run('/X /Y B7:ONE.ARC C3:',{src:f['LZW9.ARC']},failures={'source_close':1})
    assert 'Outcome: failure.' in t and target not in m.files,t
    t=m.run('/X /Y B7:ONE.ARC C3:',{src:f['LZW9.ARC']},overlay_change_at=4)
    assert 'operation stopped' in t and target not in m.files,t
    print(f'PASS: {m.cases} LZW production transactions; stack {m.max_stack}')

def oracles():
    raw,f=fixtures()
    arc=ROOT/'build/noah-proof/references/arc-325047b2dc60fad5f6c8238d8cb5294b9a5ada38/arc'
    deark=ROOT/'build/noah-proof/references/deark-c19b47c80a5ff8a7b41eb4f578e1afdda99202a2/deark'
    rng=random.Random(517);large=bytes(rng.randrange(256) for _ in range(20000))
    vectors=[(i,f[f'LZW{i}.ARC'],raw) for i in range(5,10)]
    vectors += [(i,lzw(large,i)+b'\x1a\0',large) for i in range(5,10)]
    vectors += [(i,lzw(large,i,clear_at=719)+b'\x1a\0',large) for i in (8,9)]
    for method,wire,expected in vectors:
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'input.arc').write_bytes(wire)
            r=subprocess.run([str(arc),'x','input.arc'],cwd=p,capture_output=True)
            output=p/f'M{method}.BIN'
            assert r.returncode==0 and output.read_bytes()==expected,(method,r.stdout,r.stderr)
            if method!=7:
                q=p/'deark';q.mkdir()
                r=subprocess.run([str(deark),'-od',str(q),str(p/'input.arc')],capture_output=True,check=True)
                outs=list(q.glob(f'*M{method}.BIN'))
                assert len(outs)==1 and outs[0].read_bytes()==expected,(method,r.stdout,r.stderr)
    print('PASS: original ARC methods 5-9 and Deark 5/6/8/9 independent output oracles')

def historical(m):
    m.instruction_budget=700000000
    pins=json.loads((ROOT/'tests/fixtures/noah/references.json').read_text())['artifacts']
    for name in ('crc32a.arc','de-lbr.arc','nulu15.arc'):
        raw=(ROOT/'build/noah-proof/references'/name).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==pins[name]['sha256']
        src=diskkey(1,'HIST.ARC')
        t=m.run('/X /Y HIST.ARC',{src:raw},tpa=0xca01)
        assert 'failed 0000; unprocessed 0000' in t and 'unsupported' not in t,t
        folder=ROOT/'build/noah-proof/references'/('decoded-'+name)
        for p in folder.iterdir():
            dest='.'.join(p.name.split('.')[2:])
            assert m.files[diskkey(1,dest)]==padded(p.read_bytes()),(name,dest,t)
        assert m.files[src]==raw and not m.opened,t
        print('PASS: historical LZW extraction',name)

if __name__=='__main__':
    oracles();m=machine();tests(m);historical(m)
