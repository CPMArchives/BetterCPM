#!/usr/bin/env python3
"""Execute compiled enhanced DUMP against hostile BDOS and independent cell screen.

These fixtures qualify code behavior, not native emulator/terminal integration.
No OS code or tested program is patched to bypass its production paths.
"""
from pathlib import Path
import hashlib,json
from test_bios import Z80
from test_vt52_foundation import symbols
from build_dump import version_text
ROOT = Path(__file__).resolve().parents[1]


def execute(payload=b'', tail='TEST.BIN', keys=b'Q', backend=True, width=80,
            height=24, opened=True, error=None, caller=(0,0), stream_keys=b'',
            cancel_after=None, pending_bare=None):
    c = Z80(b'')
    image=(ROOT/'build/utilities/DUMP.COM').read_bytes()
    c.mem[0x100:0x100+len(image)]=image
    c.mem[5:8]=b'\xd3\x00\xc9'
    c.mem[0:3]=b'\xc3\xfe\xff'
    c.mem[0xf000:0xf003]=b'\xd3\x01\xc9'
    c.mem[0xf100:0xf109]=b'SCR\x01\x00'+bytes([height,width])+b'\xff\xff'
    # Exit's routed clear/home dispatch uses public WBOOT+63.
    c.setword(1,0xf200);c.mem[0xf23f:0xf242]=b'\xd3\x02\xc9'
    data=tail.encode();assert len(data)<=127
    c.mem[0x80]=len(data);c.mem[0x81:0x81+len(data)]=data
    output=bytearray();services=[];reads=[];names=[];snapshots=[]
    screen=[bytearray(b' '*width) for _ in range(height)]
    x=y=0;dma=0x80;user=caller[1];drive=caller[0];seq=0
    queue=list(keys);stream=list(stream_keys);polls=0;cancel_sent=False
    syms=symbols(ROOT/'build/utilities/dump.lst')
    def bdos(port,value):
        nonlocal x,y,dma,user,drive,seq,polls,cancel_sent
        port &= 255
        if port==2:
            return
        if port==1:
            op=c.a
            if op==12:c.hl=0xf100;return
            if op==6:y,x=c.b,c.c;assert y<height and x<width,(y,x);return
            if op==7:
                screen[y][x]=c.c;x=min(width-1,x+1);return
            if op==8:screen[y][x:]=bytes([c.c])*(width-x);return
            raise AssertionError(('screen operation',op))
        fn=c.c;services.append(fn)
        if fn==2:output.append(c.e)
        elif fn==9:
            end=c.mem.index(36,c.de);output.extend(c.mem[c.de:end])
        elif fn==25:c.a=drive
        elif fn==14:drive=c.e;c.a=0
        elif fn==32:
            if c.e!=255:user=c.e
            c.a=user
        elif fn==26:dma=c.de
        elif fn==15:
            names.append((c.mem[c.de],user,bytes(c.mem[c.de+1:c.de+12])))
            seq=0;c.a=0 if opened else 255
        elif fn==35:
            c.mem[c.de+33:c.de+36]=(len(payload)//128).to_bytes(3,'little');c.a=0
        elif fn in (20,33):
            rec=seq if fn==20 else int.from_bytes(c.mem[c.de+33:c.de+36],'little')
            reads.append(rec)
            if error and error(rec,len(reads)):c.a=2
            elif rec*128>=len(payload):c.a=1
            else:
                block=payload[rec*128:(rec+1)*128];assert len(block)==128
                c.mem[dma:dma+128]=block;c.a=0;seq+=1
        elif fn==182:
            c.a=0 if backend else 255;c.setword(c.de+12,0xf000 if backend else 0)
        elif fn==1:
            snapshots.append(tuple(bytes(row) for row in screen))
            if not queue:raise AssertionError(('unexpected input',bytes(output),snapshots[-1][-1]))
            c.a=queue.pop(0)
        elif fn==11:
            polls+=1
            a=bool(stream)
            if pending_bare is not None:a=polls>=pending_bare
            if cancel_after and polls>=cancel_after and not cancel_sent:a=True
            c.a=255 if a else 0
        elif fn==6:
            caller_pc=c.word(c.sp+8)
            if syms['WAITKEY'] <= caller_pc < syms['WKEND']:
                snapshots.append(tuple(bytes(row) for row in screen))
                if not queue:raise AssertionError(('unexpected raw input',snapshots[-1][-1]))
                c.a=queue.pop(0)
            elif stream:c.a=stream.pop(0)
            elif cancel_after and not cancel_sent:c.a=27;cancel_sent=True
            else:c.a=0
        else:raise AssertionError(('BDOS',fn))
        # Public return A only. Deliberately clobber all general registers.
        c.bc=0xa5a5;c.de=0x5a5a;c.hl=0x1234
    c.port_write=bdos
    sp=c.sp;c.run(0x100,limit=50000000)
    assert c.sp==sp,'unbalanced caller stack'
    assert (drive,user)==caller,('caller DU changed',drive,user,caller)
    assert not any(fn in (16,19,21,22,23,30,34,40) for fn in services),'write/close mutation'
    return dict(output=bytes(output),services=services,reads=reads,names=names,
                snapshots=snapshots,cpu=c,syms=syms)


def row(payload,pos=0,compact=False,lower=0,end=None):
    n=8 if compact else 16
    end=len(payload) if end is None else min(end,len(payload))
    cells=[payload[i] if lower<=i<end else None for i in range(pos,pos+n)]
    hx=[f'{v:02X}' if v is not None else '  ' for v in cells]
    text=(''.join(hx[:4])+' '+''.join(hx[4:])) if compact else (
        ' '.join(hx[:8])+'  '+' '.join(hx[8:]))
    return f'{pos:08X}  {text}  '+''.join(' ' if v is None else chr(v) if 32<=v<127 else '.' for v in cells)


def main():
    count=0
    def check(*a,**kw):
        nonlocal count
        count+=1;return execute(*a,**kw)
    payload=bytes(range(256))*4
    for compact in [False,True]:
        r=check(payload,tail='TEST.BIN'+(' /40' if compact else ''))
        n=8 if compact else 16
        assert r['output']==(''.join(row(payload,i,compact)+'\r\n' for i in range(0,len(payload),n))+'\r\n').encode()
    for tail in ['/P TEST.BIN','TEST.BIN /P /P']:
        r=check(payload,tail=tail);assert r['snapshots'][0][0].decode().startswith(row(payload))
    for tail in ['TEST.BIN /40 /P','/40 /P TEST.BIN']:
        r=check(payload,tail=tail,width=40);assert r['snapshots'][0][0].decode().startswith(row(payload,compact=True))
    for tail in ['','TEST.BIN X.BIN','/NO TEST.BIN','TEST.BIN /FROM=Z',
                 'TEST.BIN /FROM=0 /FROM=Z','TEST.BIN /FROM=Z /FROM=0',
                 'TEST.BIN /BARE /40','TEST.BIN /BARE /P','TEST.BIN /BARE /FROM=0',
                 'TEST.BIN /LEN=','TEST.BIN /FIND=AA','B[1,2]:TEST.BIN','*.BIN',
                 'B7:TEST.BIN /BARE','TEST.BIN /FROM=100000000']:
        r=check(payload,tail=tail);assert not r['names'],tail
        assert b'DUMP:' in r['output'],(tail,r['output'])
    r=check(payload,tail='B7:TEST.BIN',caller=(2,3));assert r['names']==[(2,7,b'TEST    BIN')]
    for tail in ['B:TEST.BIN','TEST.BIN']:
        r=check(payload,tail=tail,caller=(2,3));assert r['names'][0][1]==3
    for off in ['123','123H','00000123','1h']:
        r=check(payload,tail=f'TEST.BIN /FROM={off}');exact=int(off.rstrip('hH'),16);v=exact&~15
        assert r['output'].startswith(row(payload,v,lower=exact).encode())
    r=check(payload,tail='TEST.BIN /FROM=80 /FROM=100');assert r['output'].startswith(b'00000100')
    for data,tail in [(b'','TEST.BIN'),(b'','TEST.BIN /P')]:
        r=check(data,tail=tail);assert r['output']==b'Empty file\r\n'
    for data,tail in [(b'','TEST.BIN /FROM=0'),(payload,'TEST.BIN /FROM=400')]:
        r=check(data,tail=tail);assert b'out of range' in r['output']
    r=check(payload,tail='TEST.BIN /P',backend=False);assert b'requires' in r['output']
    r=check(payload,tail='TEST.BIN /P',width=40);assert b'76 columns' in r['output']
    r=check(payload,tail='TEST.BIN /P',height=1);assert b'2 rows' in r['output']
    r=check(payload,tail='TEST.BIN /P',keys=b'\x03\x12Q');assert r['snapshots'][1][0].startswith(b'00000170');assert r['snapshots'][2][0].startswith(b'00000000')
    r=check(payload,tail='TEST.BIN /P /FROM=20',keys=b'\x12Q');assert r['snapshots'][1][0].startswith(b'00000000')
    r=check(payload,tail='TEST.BIN /P',keys=b'G123\rQ');assert r['snapshots'][-1][0].startswith(b'00000120')
    r=check(payload,tail='TEST.BIN /P',keys=b'G\rQ');assert r['snapshots'][-1][0].startswith(b'00000000')
    r=check(payload,tail='TEST.BIN /P',keys=b'Gzz\r\x08\x0810\rQ');assert r['snapshots'][-1][0].startswith(b'00000010')
    r=check(payload,tail='TEST.BIN /P',keys=b'G20\x13\x071\rQ');assert r['snapshots'][-1][0].startswith(b'00000020')
    pattern=b'ABABA'+b'x'*123
    r=check(pattern,tail='TEST.BIN /P',keys=b'FABA\rA.,Q')
    statuses=[s[-1].rstrip() for s in r['snapshots']]
    assert b'Match at 00000000' in statuses and b'Match at 00000002' in statuses,statuses
    r=check(payload,tail='TEST.BIN /P',keys=b'F7F 80 81\rHQ');assert r['snapshots'][-1][-1].startswith(b'Match at 0000007F')
    r=check(payload,tail='TEST.BIN /P',keys=b'Ffoo\rA.Q');assert r['snapshots'][-2][-1].startswith(b'Pattern not found');assert r['snapshots'][-1][-1].startswith(b'No further matches')
    r=check(pattern,tail='TEST.BIN /P',keys=b'FABA\rAFxxx\x1b.Q');assert r['snapshots'][-1][-1].startswith(b'Match at 00000002')
    r=check(payload,tail='TEST.BIN /P',error=lambda rec,n:rec==1);assert b'Read error at 00000080' in r['output']
    r=check(payload,tail='TEST.BIN',error=lambda rec,n:rec==1);assert b'Read error at 00000080' in r['output']
    r=check(payload,tail='TEST.BIN /P',keys=b'\x03Q',error=lambda rec,n:rec==3)
    assert r['snapshots'][-1][0].startswith(b'00000000') and r['snapshots'][-1][-1].startswith(b'Read error')
    r=check(payload,stream_keys=b'\x03');assert not r['reads']
    r=check(tail='/VER');assert r['output']==version_text().encode() and r['services']==[9]

    # Actual page geometry, row/record crossing, long editor and state edges.
    r=check(payload,tail='TEST.BIN /P',height=40,keys=b'\x03Q')
    assert r['snapshots'][1][0].startswith(b'00000270')
    r=check(payload,tail='TEST.BIN /P /40',width=37,keys=b'Q')
    assert len(r['snapshots'][0][-1])==37
    r=check(payload,tail='TEST.BIN /P /FROM=3F0',keys=b'\x03Q')
    assert r['snapshots'][-1][-1].startswith(b'End of file')
    r=check(payload,tail='TEST.BIN /P',keys=b'\x12?Q')
    assert r['snapshots'][-1][-1].startswith(b'Beginning of file')
    for value in ['-1','+1','H','0x10','123456789','1 2']:
        r=check(payload,tail='TEST.BIN /FROM='+value);assert b'DUMP:' in r['output']
    r=check(payload,tail='TEST.BIN /FROM=FFFF /FROM=0');assert b'out of range' in r['output']
    large=bytes(range(256))*258
    r=check(large,tail='TEST.BIN /FROM=10003');assert r['output'].startswith(row(large,65536,lower=65539).encode())
    r=check(payload,tail='TEST.BIN /P',keys=b'F\rQ');assert not any(b'Match at' in s[-1] for s in r['snapshots'])
    r=check(payload,tail='TEST.BIN /P',keys=b'F   \rHQ');assert r['snapshots'][-1][-1].startswith(b'^R Up')
    spaces=b' '*128
    r=check(spaces,tail='TEST.BIN /P',keys=b'F   \rAQ');assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    r=check(pattern,tail='TEST.BIN /P',keys=b'FABA\rXAQ');assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    r=check(pattern,tail='TEST.BIN /P',keys=b'FABA\rAFZZ\r\x1b.Q');assert r['snapshots'][-1][-1].startswith(b'Match at 00000002')
    # All four WordStar edit keys: insert B into AA, advance, delete, backspace.
    r=check(pattern,tail='TEST.BIN /P',keys=b'FAA\x13B\x04\x08A\rAQ')
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    raw=b' '.join([b'41']*32)
    assert len(raw)==95
    r=check(b'A'*128,tail='TEST.BIN /P /40',width=40,keys=b'F'+raw+b'\rHQ')
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    r=check(b'A'*128,tail='TEST.BIN /P',keys=b'F'+b'A'*33+b'\rA\x08\rAQ')
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    r=check(b'A'*128,tail='TEST.BIN /P /40',width=40,keys=b'F'+raw+b'0\rHQ')
    assert any(s[-1].startswith(b'Input limit reached') for s in r['snapshots'])
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    r=check(pattern,tail='TEST.BIN /P',keys=b'FABA\rA,Q')
    assert r['snapshots'][-1][-1].startswith(b'No further matches')
    r=check(pattern,tail='TEST.BIN /P',keys=b'FABA\rAG1\r.Q')
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    case_data=b'Hello'+b'x'*123
    r=check(case_data,tail='TEST.BIN /P',keys=b'FHello\rAQ')
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000000')
    r=check(case_data,tail='TEST.BIN /P',keys=b'FHELLO\rAQ')
    assert r['snapshots'][-1][-1].startswith(b'Pattern not found')
    crossing=b'x'*367+b'NEEDLE'+b'x'*139
    r=check(crossing,tail='TEST.BIN /P',keys=b'FNEEDLE\rAQ')
    assert r['snapshots'][-1][-1].startswith(b'Match at 0000016F')
    assert r['snapshots'][-1][0].startswith(b'00000160')
    r=check(pattern,tail='TEST.BIN /P',keys=b'FA\x13\x1bQ')
    assert r['snapshots'][1][-1][6]==(ord('_')|128)
    assert r['snapshots'][3][-1][6]==(ord('A')|128)
    # Search beyond an existing page can fail without losing page or old pattern.
    r=check(payload,tail='TEST.BIN /P',keys=b'F00\rHFZZ\rA.Q',error=lambda rec,n:rec>=3)
    assert any(s[-1].startswith(b'Read error') for s in r['snapshots'])
    assert r['cpu'].mem[r['syms']['PATTERN']]==0 and r['cpu'].mem[r['syms']['PATLEN']]==1
    assert r['snapshots'][-1][0].startswith(b'00000000')
    r=check(payload,tail='TEST.BIN /P',keys=b'FZZ\rAQ',cancel_after=1)
    assert r['snapshots'][-1][-1].startswith(b'^R Up')
    # Independent full-string and screen-cell assertions for exact range edges.
    for compact in (False,True):
        n=8 if compact else 16
        for start,size in [(0,0),(0,1),(1,1),(7,2),(7,10),(15,2),(16,16),
                           (127,2),(255,1),(255,2),(1001,23),(1023,1),
                           (1023,0xffffffff)]:
            end=min(len(payload),start+size)
            options=f'TEST.BIN /FROM={start:X} /LEN={size:X}'+(' /40' if compact else '')
            expected=[row(payload,i,compact,lower=start,end=end) for i in range(start//n*n,end,n)] if size else []
            r=check(payload,tail=options)
            assert r['output']==(('\r\n'.join(expected)+'\r\n\r\n').encode() if expected else b''),(options,r['output'])
            r=check(payload,tail=options+' /P',width=40 if compact else 80)
            if not size:
                assert not r['snapshots'] and not r['reads']
            else:
                snap=r['snapshots'][0]
                for i,line in enumerate(expected[:23]):assert snap[i].decode().startswith(line),(options,snap[i],line)
                for line in snap[len(expected):23]:assert not line.strip(),(options,line)
    for suffix in ['a','aH','Ah','0000000A']:
        r=check(payload,tail='TEST.BIN /LEN='+suffix)
        assert r['output']==(row(payload,end=10)+'\r\n\r\n').encode()
    for value in ['','H','-1','+1','0x10','Z','1HH','100000000']:
        for opts in [f'/LEN={value}',f'/LEN={value} /LEN=1']:
            r=check(payload,tail='TEST.BIN '+opts)
            assert not r['names'] and b'DUMP:' in r['output'],opts
    for opts in ['/BARE /LEN=0','/LEN=1 /BARE','/FROM=400 /LEN=0',
                 '/FROM=FFFF /FROM=0 /LEN=1']:
        r=check(payload,tail='TEST.BIN '+opts)
        assert b'DUMP:' in r['output'] and not r['reads'],opts
    r=check(payload,tail='TEST.BIN /LEN=1 /LEN=2')
    assert r['output']==(row(payload,end=2)+'\r\n\r\n').encode()
    r=check(b'',tail='TEST.BIN /LEN=0 /P');assert r['output']==b'Empty file\r\n'
    r=check(b'',tail='TEST.BIN /FROM=0 /LEN=0');assert b'out of range' in r['output']
    r=check(payload,tail='TEST.BIN /FROM=7 /LEN=1 /P',keys=b'\x12\x03G8\r\x087\rQ')
    assert r['snapshots'][1][-1].startswith(b'Beginning of file')
    assert r['snapshots'][2][-1].startswith(b'End of file')
    assert any(s[-1].startswith(b'Invalid input') for s in r['snapshots'])
    assert r['snapshots'][-1][0].decode().startswith(row(payload,lower=7,end=8))
    for compact in (False,True):
        n=8 if compact else 16;cap=23*n
        opts='TEST.BIN /FROM=7 /LEN=190 /P'+(' /40' if compact else '')
        r=check(payload,tail=opts,keys=b'\x03\x12G8\rQ')
        assert r['snapshots'][1][0].decode().startswith(row(payload,cap,compact,lower=7,end=407))
        assert r['snapshots'][2][0].decode().startswith(row(payload,0,compact,lower=7,end=407))
        assert r['snapshots'][-1][0].decode().startswith(row(payload,8//n*n,compact,lower=7,end=407))
    r=check(payload,tail='TEST.BIN /FROM=7 /P',keys=b'\x12Q')
    assert r['snapshots'][0][0].decode().startswith(row(payload,lower=7))
    assert r['snapshots'][-1][-1].startswith(b'Beginning of file')
    r=check(payload,tail='TEST.BIN /FROM=17 /P',keys=b'\x12Q')
    assert r['snapshots'][-1][0].decode().startswith(row(payload))
    # Search cannot match masked prefix/suffix bytes, even across a boundary.
    r=check(payload,tail='TEST.BIN /FROM=7 /LEN=3 /P',keys=b'F06\rHF090A\rHQ')
    assert r['snapshots'][-1][-1].startswith(b'Pattern not found')
    r=check(payload,tail='TEST.BIN /FROM=7 /LEN=3 /P',keys=b'F07\rH,Q')
    assert any(s[-1].startswith(b'Match at 00000007') for s in r['snapshots'])
    assert r['snapshots'][-1][-1].startswith(b'No further matches')
    # A partial end at a record boundary must never request the following record.
    for paged in (False,True):
        r=check(payload,tail='TEST.BIN /FROM=7F /LEN=1'+(' /P' if paged else ''),error=lambda rec,n:rec==1)
        assert r['reads']==[0] and b'Read error' not in r['output']
    r=check(payload,tail='TEST.BIN /FROM=7 /LEN=300 /P',keys=b'\x03Q',error=lambda rec,n:rec==3)
    assert r['snapshots'][-1][0].decode().startswith(row(payload,lower=7,end=775))
    assert r['snapshots'][-1][-1].startswith(b'Read error')
    r=check(large,tail='TEST.BIN /FROM=10003 /LEN=10')
    assert r['output']==(row(large,0x10000,lower=0x10003,end=0x10013)+'\r\n'+row(large,0x10010,lower=0x10003,end=0x10013)+'\r\n\r\n').encode()
    r=check(payload,tail='/LEN=1h /FROM=7 /40 /P TEST.BIN',keys=b'G6\r\x087\rQ')
    assert any(s[-1].startswith(b'Invalid input') for s in r['snapshots'])
    assert r['snapshots'][-1][0].decode().startswith(row(payload,0,True,lower=7,end=8))
    r=check(payload,tail='TEST.BIN /FROM=7 /P',keys=b'G0\rQ')
    assert r['snapshots'][-1][0].decode().startswith(row(payload))
    r=check(payload,tail='TEST.BIN /FROM=7 /P',keys=b'F00\rHQ')
    assert r['snapshots'][-1][-1].startswith(b'Match at 00000100')
    r=check(payload,tail='TEST.BIN /LEN=1 /BARE /VER')
    assert r['output']==version_text().encode() and r['services']==[9]
    (ROOT/'build/utilities/dump-enhanced-tests.json').write_text(json.dumps({'status':'PASS','cases':count,'program_sha256':hashlib.sha256((ROOT/'build/utilities/DUMP.COM').read_bytes()).hexdigest(),'scope':'Compiled Z80 with hostile public BDOS fixture and independent typed-cell screen; not native platform evidence.'},indent=2)+'\n')
    print(f'PASS: {count} compiled enhanced DUMP output/parser/DU/viewer/editor/search/failure cases')

if __name__=='__main__':main()
