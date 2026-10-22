#!/usr/bin/env python3
"""Execute DDT's compiled shared-input binding with hostile BDOS callbacks."""
from pathlib import Path
import json,re,sys
from functools import lru_cache
from build_ddt import ROOT,BUILD
# The repository's existing CPU fixture is not part of the distributed utility.
from test_bios import Z80
from test_utility_versions import address


class Input:
    def __init__(self,keys,prefix='-'):
        self.c=Z80(b'');image=(BUILD/'payload-0000.bin').read_bytes();self.c.mem[:len(image)]=image
        self.listing=(BUILD/'payload-0000.lst').read_text();self.keys=list(keys)
        self.raw=bytearray();self.row=list(prefix);self.col=len(prefix);self.prefix=prefix
        self.c.sp=0x8000;self.c.port_read=self.service
        self.c.mem[0x9000:0x9003]=bytes([0xDB,113,0xC9])
        self.c.setword(self.at('TRAPJMP')+1,0x9000)
        self.c.mem[self.at('START'):self.at('START')+3]=bytes.fromhex('c3ffff')
        # Warm boot is a nonreturning sentinel in this bounded fixture.
        self.c.mem[:3]=bytes.fromhex('c3ffff')
        self.canary=bytes(self.c.mem[self.at('PLOC')-10:self.at('STACK')])
        self.stack_bottom=self.at('DU_TOP')-256
        self.c.mem[self.stack_bottom:self.at('DU_TOP')]=b'\xa5'*256
    @lru_cache(None)
    def at(self,label):
        m=re.search(r'^([0-9a-f]{4})\s+=.*?\b'+re.escape(label)+r'\s+EQU\b',self.listing,re.M|re.I)
        return int(m[1],16) if m else address(self.listing,label)
    def draw(self,v):
        self.raw.append(v)
        if v==8:self.col=max(0,self.col-1)
        elif v==13:self.col=0
        elif v==10:self.row=[];self.col=0
        elif 32<=v<127:
            while len(self.row)<=self.col:self.row.append(' ')
            self.row[self.col]=chr(v);self.col+=1
    def service(self,port):
        c=self.c;assert c.c==6,c.c
        if c.e==255:
            assert self.keys,'input exhausted'
            length=c.mem[self.at('EDITLEN')];start=c.mem[self.at('EDITSTART')];cursor=c.mem[self.at('EDITCUR')]
            assert self.col==len(self.prefix)+cursor-start
            assert ''.join(self.row[:len(self.prefix)])==self.prefix
            text=bytes(c.mem[self.at('COMBUF'):self.at('COMBUF')+length]).decode()
            window=(text[start:]+(' ' * 24))[:24]
            if cursor==length and 0<=cursor-start<24:window=window[:cursor-start]+'_'+window[cursor-start+1:]
            assert ''.join(self.row[len(self.prefix):len(self.prefix)+24])==window
            result=self.keys.pop(0)
        else:self.draw(c.e);result=0x77
        c.bc=0xbcbc;c.de=0xdede;c.hl=0xeeee
        return result
    def run(self):
        self.c.run(self.at('GETBUFF'),limit=500000)
        assert bytes(self.c.mem[self.at('PLOC')-10:self.at('STACK')])==self.canary
        assert bytes(self.c.mem[self.stack_bottom:self.stack_bottom+64])==b'\xa5'*64
        n=self.c.mem[self.at('CURLEN')]
        return bytes(self.c.mem[self.at('COMBUF'):self.at('COMBUF')+n])


def main():
    cases=[(b'H100,20\r',b'H100,20'),(b'\r',b''),(b'h100,2X\x7f0\r',b'h100,20'),
           (b'H100,20\x13\x13\x07\r',b'H100,0'),
           (b'old\x15H100,20\r',b'H100,20'),(b'old\x18H100,20\r',b'H100,20'),
           (b'old\x19H100,20\r',b'H100,20'),(b'A'*32+b'B\r',b'A'*32),
           (b'A'*32+b'\x08B\r',b'A'*31+b'B'),(b'A'*32+b'\x01Z\r',b'A'*32),
           (b'A B\x01X\x06Y\r',b'A XBY'),(b'.\r',b'.'),(b'\tH100,20\r',b'H100,20')]
    for keys,want in cases:
        f=Input(keys,prefix='0300 00 ');actual=f.run();assert actual==want,(keys,actual,want)
        assert f.c.sp==0x8000
        assert ''.join(f.row).startswith('0300 00 '+want.decode())
        assert f.c.word(f.at('NEXTCOM'))==f.at('COMBUF')
    f=Input(b'partial\x1b');f.run();assert f.c.sp==f.at('STACK')-12
    assert ''.join(f.row).strip()=='-'
    f=Input(b'\x03');f.run()
    f=Input(b'ONE\rTWO\r');assert f.run()==b'ONE' and bytes(f.keys)==b'TWO\r'
    # Repeated editor entry restores the caller stack and leaves no stale caret.
    for i in range(100):
        f.keys=list(b'H1,2\r');f.col=1;f.row=['-'];assert f.run()==b'H1,2';assert f.c.sp==0x8000
    result={'status':'PASS','cases':len(cases)+4,'repeated_entries':100,
            'scope':'Compiled consumer, hostile BDOS clobbers, renderer prefix/caret, edit bounds, cancellation, direct output, typeahead and balanced private stack.'}
    (BUILD/'input-report.json').write_text(json.dumps(result,indent=2)+'\n');print(result)


if __name__=='__main__':main()
