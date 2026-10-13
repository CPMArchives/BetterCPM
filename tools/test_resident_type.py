#!/usr/bin/env python3
"""Execute relocated resident TYPE with read-only BDOS fixtures."""
import re, struct
from pathlib import Path
from test_bios import Z80, SENTINEL
ROOT = Path(__file__).resolve().parents[1]

def execute(tail, files, responses='', base=0x8000, open_fail=(), read_fail=(), transient=False, observe=None):
    carrier = (ROOT/'build/cpx/RCP.CPX').read_bytes()
    linked, size = struct.unpack_from('<HH', carrier, 10)
    count, _, payload, table = struct.unpack_from('<4H', carrier, 22)
    image = bytearray(carrier[payload:payload+size])
    for i in range(count):
        off = struct.unpack_from('<H', carrier, table+2*i)[0]
        struct.pack_into('<H', image, off, (struct.unpack_from('<H', image, off)[0]+base-linked)&65535)
    listing = (ROOT/'build/cpx/rcp.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':', listing, re.M|re.I)[1],16)-linked+base
    c = Z80(b''); c.mem[base:base+size] = image
    c.mem[5:8] = bytes((0xDB,254,0xC9))
    c.mem[0x2000:0x2000+len(tail)] = tail.encode()
    c.hl=0x2000; c.b=len(tail)
    if transient:
        binary = (ROOT/'build/utilities/TYPE.COM').read_bytes()
        c.mem[0x100:0x100+len(binary)] = binary
        c.mem[0:3] = bytes((0xC3,SENTINEL&255,SENTINEL>>8))
        c.mem[0x80] = len(tail)
        c.mem[0x81:0x81+len(tail)] = tail.encode()
    state = dict(drive=0,user=2,dma=0x80,rows=[],index=0,reads=0)
    output=[]; actions=[]; keys=iter(responses)
    def io(port):
        assert port&255==254
        f=c.c; actions.append(f)
        if observe is not None:observe(c, f)
        if f==25:return state['drive']
        if f==32:
            if c.e!=255:state['user']=c.e
            return state['user']
        if f==14:state['drive']=c.e;return 0
        if f==26:state['dma']=c.de;return 0
        if f==2:output.append(chr(c.e));return c.e
        if f==9:
            p=c.de
            while c.mem[p]!=36:output.append(chr(c.mem[p]));p+=1
            return 0
        if f==6:return ord(next(keys))
        if f in (17,18):
            if f==17:
                pat=bytes(c.mem[c.de+1:c.de+12])
                state['rows']=[(k,attr) for k,(data,attr) in files.items()
                    for _ in range(max(1,(len(data)+16383)//16384))
                    if k[:2]==(state['drive'],state['user']) and all(a==63 or a==b for a,b in zip(pat,k[2]))]
                state['index']=0
            if state['index']==len(state['rows']):return 255
            k,attr=state['rows'][state['index']];state['index']+=1
            row=bytearray(32);row[0]=k[1];row[1:12]=k[2]
            for bit in range(3):row[9+bit]|=((attr>>bit)&1)<<7
            c.mem[state['dma']:state['dma']+32]=row;return 0
        if f in (15,16,20):
            key=(state['drive'],state['user'],bytes(c.mem[c.de+1:c.de+12]))
            if f==15:
                state['reads']=0;return 255 if key in open_fail else 0
            if f==16:return 0
            if key in read_fail:return 2
            data=files[key][0];start=128*state['reads'];state['reads']+=1
            if start>=len(data):return 1
            c.mem[state['dma']:state['dma']+128]=data[start:start+128].ljust(128,b'\x1a');return 0
        raise AssertionError(('unexpected/mutating BDOS call',f))
    c.port_read=io;c.run(0x100 if transient else addr('BC_TYPE'),limit=3000000)
    assert (state['drive'],state['user'])==(0,2),'caller DU not restored'
    return ''.join(output), actions

def main():
    a=(1,3,b'A       TXT');b=(1,3,b'B       TXT');d=(2,5,b'D       TXT')
    files={b:(b'BETA\r\n\x1aHIDDEN',2),a:(b'ALPHA $\r\n',1),d:(b'DELTA\r\n',4)}
    for base in (0x4000,0x8101,0xA000):
        out,calls=execute('[B3,C5]:*.TXT',files,base=base)
        assert out.index('ALPHA $')<out.index('BETA')<out.index('DELTA')
        assert out.count('--------------------')==2 and 'HIDDEN' not in out
        out,_=execute('[B3,C5]:*.TXT[$ARC]',files,base=base)
        assert 'DELTA' in out and 'ALPHA' not in out and 'BETA' not in out
        for tail in ('', 'B3:F*A.TXT', '[B3,E0]:*.TXT', 'B3:*.TXT /7', 'B3:*.TXT OTHER.TXT'):
            out,calls=execute(tail,files,base=base)
            assert not any(f in calls for f in (15,17,20)),(tail,out)
        out,_=execute('B3:*.TXT',files,base=base,open_fail=(a,))
        assert 'Cannot open.' in out and 'BETA' in out
        out,_=execute('B3:*.TXT',files,base=base,read_fail=(a,))
        assert 'READ ERROR' in out and 'BETA' in out
    long={a:(b'LINE\r\n'*30,0)}
    for tail in ('B3:A.TXT /P','/P B3:A.TXT','/P B3:A.TXT /P'):
        for key in (' ','.'):
            out,_=execute(tail,long,key);assert out.count('LINE')==30 and out.count('--More--')==1
        out,_=execute(tail,long,'\x03');assert out.count('LINE')==23
    out,_=execute('B3:A.TXT',{a:(b'\x9aAFTER\x1aHIDDEN',0)})
    assert '\x9aAFTER' in out and 'HIDDEN' not in out
    out,_=execute('B3:*.TXT',{a:(b'',0),b:(b'BETA',0)})
    assert 'BETA' in out and out.count('--------------------')==1
    out,_=execute('B3:A.TXT',{a:(b'A'*17000+b'\x1a',0)})
    assert out.count('A')==17000,'duplicate extent display'
    print('PASS: resident TYPE relocated selectors, protection-independent display, unique extents, EOF, paging, abort, errors and DU restoration')
if __name__=='__main__':main()
