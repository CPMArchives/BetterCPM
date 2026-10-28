#!/usr/bin/env python3
"""Run the compiled COMPARE with hostile public-BDOS fixtures and an independent oracle.

These tests verify utility behavior; they do not assert platform acceptance.
"""
from pathlib import Path
import json
import re
from test_bios import Z80
ROOT = Path(__file__).resolve().parents[1]


def execute(a=b'', b=b'', tail='A.BIN B.BIN', *, caller=(2,7), keys=b' ',
            error=None, missing=None, cancel_after=None, lengths=None):
    assert len(a)%128 == len(b)%128 == 0
    c = Z80(b'')
    image=(ROOT/'build/utilities/COMPARE.COM').read_bytes()
    c.mem[0x100:0x100+len(image)] = image
    c.mem[5:8]=b'\xd3\x00\xc9'
    c.mem[0:3]=b'\xc3\xfe\xff'
    data=tail.encode('ascii');assert len(data)<=127
    c.mem[0x80]=len(data);c.mem[0x81:0x81+len(data)]=data
    output=bytearray();services=[];reads=[];opened=[];closed=[];handles={}
    dma=0x80;drive,user=caller;polls=0;keypos=0
    def bdos(port,value):
        nonlocal dma,drive,user,polls,keypos
        fn=c.c;services.append(fn)
        if fn==6:
            if c.e==255:
                if cancel_after is not None:
                    c.a=3 if polls>=cancel_after else 0
                else:
                    c.a=keys[keypos%len(keys)] if keys else 0;keypos+=1
            else:output.append(c.e)
        elif fn==11:
            polls+=1;c.a=255 if cancel_after is not None and polls>=cancel_after else 0
        elif fn==25:c.a=drive
        elif fn==14:drive=c.e;c.a=0
        elif fn==32:
            if c.e!=255:user=c.e
            c.a=user
        elif fn==26:dma=c.de
        elif fn==15:
            name=bytes(c.mem[c.de+1:c.de+12]);du=(c.mem[c.de]-1,user)
            opened.append((du,name));index=0 if len(opened)==1 else 1
            # Comparing a file with itself selects identical contents.
            if len(opened)==2 and opened[0]==opened[1]:index=0
            handles[c.de]=(index,du)
            c.a=255 if missing==index else 0
        elif fn==35:
            index,du=handles[c.de];assert user==du[1]
            n=lengths[index] if lengths else len((a,b)[index])
            c.mem[c.de+33:c.de+36]=(n//128).to_bytes(3,'little');c.a=0
        elif fn==33:
            index,du=handles[c.de];assert user==du[1]
            rec=int.from_bytes(c.mem[c.de+33:c.de+36],'little')
            reads.append((index,rec));payload=(a,b)[index]
            if error and (index,rec)==error:c.a=2
            elif rec*128>=len(payload):c.a=1
            else:c.mem[dma:dma+128]=payload[rec*128:rec*128+128];c.a=0
        elif fn==16:
            index,du=handles[c.de];assert user==du[1];closed.append(index);c.a=0
        else:raise AssertionError(('unexpected BDOS',fn))
        c.bc=0xa5a5;c.de=0x5a5a;c.hl=0x1234
    c.port_write=bdos
    sp=c.sp;c.run(0x100,limit=100000000)
    assert c.sp==sp,'caller stack imbalance'
    assert (drive,user)==caller,('caller DU changed',drive,user)
    assert dma==0x80,'default DMA not restored'
    assert not set(services)&{19,21,22,23,30,34,40},'write service'
    return dict(text=output.decode('ascii'),services=services,reads=reads,opened=opened,closed=closed)


def stats(text):
    return {key:int(value) for key,value in re.findall(r'^([A-Z 12]+): (\d+)\r?$',text,re.M)}


def oracle(a,b,start1=0,start2=0,length=None):
    a=a[start1:];b=b[start2:]
    n=max(len(a),len(b))
    if length is not None:n=min(n,length)
    pairs=min(len(a),len(b),n)
    return {'POSITIONS EXAMINED':n,'BYTE PAIRS COMPARED':pairs,
            'BYTE MISMATCHES':sum(x!=y for x,y in zip(a[:n],b[:n])),
            'ADDITIONAL IN FILE 1':max(0,min(len(a),n)-pairs),
            'ADDITIONAL IN FILE 2':max(0,min(len(b),n)-pairs)}



def side_oracle(a,b,s1,s2,length,width):
    n=oracle(a,b,s1,s2,length)['POSITIONS EXAMINED']
    rows={}
    for k in range(n):
        pos=s1+k;base=pos-pos%width;slot=pos%width
        one,two=rows.setdefault(base,([None]*width,[None]*width))
        one[slot]=a[s1+k] if s1+k<len(a) else None
        two[slot]=b[s2+k] if s2+k<len(b) else None
    exhausted=[False,False];result=[]
    for base,(one,two) in rows.items():
        fields=[]
        for i,values in enumerate((one,two)):
            if all(v is None for v in values) and not exhausted[i]:
                fields.append('EOF'.ljust(8) if width==4 else '---- EOF ----'.ljust(23))
                exhausted[i]=True
            else:
                fields.append(('' if width==4 else ' ').join('  ' if v is None else f'{v:02X}' for v in values))
        marker='<>' if one!=two else '  '
        second=base+s2-s1
        label=f'{second:08X}' if second>=0 else '--------'
        middle=marker if width==4 else ' '+marker+' '
        result.append(f'{base:08X}  {fields[0]}{middle}{label}  {fields[1]}')
    return result


def main():
    count=0
    a=bytes(range(256))*2
    b=bytearray(a);b[0]^=1;b[127]^=1;b[128]^=1;b[-1]^=1;b=bytes(b)
    def run(*args,**kwargs):
        nonlocal count
        count+=1;return execute(*args,**kwargs)
    from component_identity import title
    from utility_versions import identities,display_development
    version,revision=identities()['COMPARE']
    help_result=run(tail='/HELP')['text']
    lines=help_result.splitlines()
    assert lines[:5]==[title('COMPARE',version,revision,development=display_development('utility:COMPARE')),'  - - -',' | Binary File Comparison',' |',' |   Usage: COMPARE [options] file1 file2 [options]']
    assert len(lines)<=23 and max(map(len,lines))<=79
    assert 'BetterCP/M Utilities' not in help_result
    assert lines[-2:]==['     /HELP         Display this help.','     /VER          Display utility identification.']
    for tail in ('/VER','BAD /help /VER','/HELP invalid','/helper /help'):
        r=run(tail=tail);assert not set(r['services'])&{15,25,32},r
    for tail in ('','A.BIN','A.BIN B.BIN C.BIN','*.BIN B.BIN','A[3]:A.BIN B.BIN',
                 '/SIDE /SUM A.BIN B.BIN','/COUNT=0 A.BIN B.BIN',
                 '/COUNT=65536 A.BIN B.BIN','/COUNT=99999999999 A.BIN B.BIN',
                 '/COUNT=1H A.BIN B.BIN','/COUNT=-1 A.BIN B.BIN',
                 '/FROM=100000000 A.BIN B.BIN','/FROM=H A.BIN B.BIN',
                 '/FROM=ZZ A.BIN B.BIN','/LEN=+1 A.BIN B.BIN','/40 A.BIN B.BIN',
                 '/SIDE /ALL A.BIN B.BIN','/SUM /P A.BIN B.BIN',
                 '/COUNT=1 /ALL A.BIN B.BIN','/UNKNOWN A.BIN B.BIN','Q:A.BIN B.BIN'):
        r=run(tail=tail);assert not r['opened'],(tail,r['text'])
    for s1,s2,n in [(0,0,None),(7,0,None),(0,0,0),(127,129,140),(700,900,None),
                    (0,300,128),(0,0,256),(5,8,19),(4,0,1)]:
        for mode in ('/SUMMARY','/LIST','/SIDE','/SIDE /40'):
            tail=f'A.BIN /FROM={s1:X} B.BIN /FROM2={s2:X} {mode}'
            if n is not None:tail+=f' /LEN={n:X}'
            r=run(a,b,tail);actual=stats(r['text']);expected=oracle(a,b,s1,s2,n)
            assert all(actual.get(k)==v for k,v in expected.items()),(tail,actual,expected,r['text'])
            if '/SIDE' in mode:
                rows=[x for x in r['text'].splitlines() if re.match(r'^[0-9A-F]{8}  ',x)]
                assert rows==side_oracle(a,b,s1,s2,n,4 if '/40' in mode else 8),(tail,rows)
    for p,q in [(b'',b''),(a,a),(a,b''),(a,b+b),(b'\x1a'*128,b'\x1a'*128)]:
        r=run(p,q,'A.BIN B.BIN /SUMMARY');actual=stats(r['text'])
        assert all(actual.get(k)==v for k,v in oracle(p,q).items()),r['text']
        assert ('FILES IDENTICAL' in r['text'])==(p==q)
    r=run(a,b,'A.BIN A.BIN /SUMMARY');assert 'FILES IDENTICAL' in r['text']
    r=run(a,b,'A3:A.BIN B7:B.BIN /SUMMARY');assert [x[0] for x in r['opened']]==[(0,3),(1,7)]
    r=run(a,b,'A.BIN B.BIN /SIDE /40 /FROM=7 /FROM2=0 /LEN=5')
    assert '00000004        07<>--------        01' in r['text'],r['text']
    many=bytes([255])*512
    for opt,n in [('',20),('/COUNT=1',1),('/COUNT=65535',512),('/ALL',512)]:
        r=run(bytes(512),many,'A.BIN B.BIN '+opt)
        assert stats(r['text'])['UNDISPLAYED DIFFERENCES']==512-n,r['text']
        assert len(re.findall(r'^[0-9A-F]{8}  ',r['text'],re.M))==n
    for key in (b'\x03',b'Q',b'\x1b',b' ',b'\r'):
        r=run(bytes(512),many,'A.BIN B.BIN /SIDE /40 /P',keys=key)
        assert stats(r['text'])['BYTE MISMATCHES']==512
        assert ('DISPLAY INTERRUPTED' in r['text'])==(key not in (b' ',b'\r'))
    for index in (0,1):
        r=run(a,b,missing=index);assert 'Cannot open' in r['text'] and 'FILES IDENTICAL' not in r['text']
        r=run(a,b,error=(index,1));assert 'COMPARISON INCOMPLETE' in r['text'] and 'SUMMARY:' not in r['text']
    r=run(a,b,cancel_after=3);assert 'COMPARISON INCOMPLETE' in r['text'] and 'SUMMARY:' not in r['text']
    big=bytes(range(256))*257
    changed=bytearray(big);changed[65535]^=1;changed[65536]^=1
    r=run(big,bytes(changed),'A.BIN B.BIN /FROM=FFFE /LEN=4')
    assert stats(r['text'])['BYTE MISMATCHES']==2 and '00010000' in r['text']
    r=run(big,bytes(changed),'A.BIN B.BIN /SUMMARY')
    assert stats(r['text'])['POSITIONS EXAMINED']==len(big) and stats(r['text'])['BYTE MISMATCHES']==2
    r=run(tail='A.BIN B.BIN /LEN=0',lengths=(0x7FFFFF80,0x7FFFFF80))
    assert 'FILE 1 LENGTH: 2147483520' in r['text']
    r=run(a,b,'A.BIN B.BIN /FROM=FFFFFFFF /FROM2=0 /SUMMARY')
    assert 'address overflow' in r['text'] and not r['reads']
    report={'status':'PASS','cases':count,'scope':'Compiled COM under hostile public-BDOS fixture; not live platform qualification'}
    (ROOT/'build/utilities/compare-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print(f'PASS {count} compiled COMPARE cases')


if __name__=='__main__':main()
