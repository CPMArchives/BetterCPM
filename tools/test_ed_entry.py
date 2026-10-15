#!/usr/bin/env python3
"""Real startup allocation: gateway ceilings, stack guards and pre-mutation failure."""
from test_ed_buffer import context
from test_bios import Z80, SENTINEL
from test_vt52_foundation import symbols
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ed-development'


def main():
    c,s,call,_,_=context()
    def call(label):
        stack=c.sp;c.run(s[label],limit=100000);assert c.sp==stack
        return c.carry,c.a
    base=s['ED_STACK']
    for ceiling in (base-1,base,base+1,base+1023,base+1024,0x6000,0xd400,0xf000):
        before=tuple(c.word(s[k]) for k in ('EB_FIRST','EB_FRONT','EB_BACK','EB_LIMIT'))
        c.mem[6:8]=ceiling.to_bytes(2,'little')
        bad,_=call('ED_MEMORY')
        assert bad==(ceiling-base<1024),hex(ceiling)
        if bad:
            assert before==tuple(c.word(s[k]) for k in ('EB_FIRST','EB_FRONT','EB_BACK','EB_LIMIT'))
        else:
            assert c.word(s['EB_FIRST'])==base and c.word(s['EB_LIMIT'])==ceiling
            # First and last legal bytes must not touch the stack or resident gateway.
            c.mem[base-1]=0x51;c.mem[ceiling]=0x52
            c.c=65;call('EB_PUT')
            c.mem[s['EB_BACK']:s['EB_BACK']+2]=(ceiling-1).to_bytes(2,'little')
            c.mem[ceiling-1]=66;call('EB_RIGHT')
            assert c.mem[base-1]==0x51 and c.mem[ceiling]==0x52
    for tail,ceiling,want in (('FILE.TXT',base+1023,'NO MEMORY'),('B[-]:X',0xd400,'Invalid filespec.')):
        c=Z80(b'');image=(OUT/'EDDEV.COM').read_bytes();c.mem[256:256+len(image)]=image
        c.mem[:3]=bytes((0xc3,SENTINEL&255,SENTINEL>>8))
        c.mem[5:8]=bytes((0xc3,ceiling&255,ceiling>>8))
        c.mem[ceiling:ceiling+3]=bytes((0xdb,254,0xc9))
        data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        calls=[];output=[]
        def io(port):
            calls.append(c.c)
            if c.c==25:return 0
            if c.c==32:
                assert c.e==255
                return 0
            assert c.c==9,('unexpected mutation',c.c)
            end=c.mem.index(36,c.de);output.append(bytes(c.mem[c.de:end]).decode());return 0
        c.port_read=io;c.run(s['ED_START'],limit=100000)
        assert calls==[25,32,9] and ''.join(output)==want+'\r\n'
    print('PASS: real ED startup, minimum memory, lowered RSX ceilings, buffer/stack bounds and rejection before disk mutation')


if __name__=='__main__':main()
