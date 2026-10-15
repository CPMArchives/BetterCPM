#!/usr/bin/env python3
"""Gap-buffer invariants and initial commands against an independent text model."""
from pathlib import Path
import random
from test_bios import Z80
from test_vt52_foundation import symbols
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ed-development'


def context(capacity=64):
    c=Z80(b'');data=(OUT/'EDDEV.COM').read_bytes();c.mem[256:256+len(data)]=data
    s=symbols(OUT/'ed.lst');base=0x6000;end=base+capacity
    c.mem[base-16:base]=b'G'*16;c.mem[end:end+16]=b'H'*16
    def call(label):
        stack=c.sp;c.run(s[label],limit=200000);assert c.sp==stack
        assert bytes(c.mem[base-16:base])==b'G'*16
        assert bytes(c.mem[end:end+16])==b'H'*16
        return c.carry,c.a
    c.hl=base;c.de=end;assert not call('EB_INIT')[0];call('EC_INIT')
    def text():
        front=c.word(s['EB_FRONT']);back=c.word(s['EB_BACK'])
        assert base<=front<=back<=end
        return bytes(c.mem[base:front]+c.mem[back:end]),front-base
    def command(data):
        c.mem[0x5000:0x5000+len(data)]=data;c.hl=0x5000;c.b=len(data)
        result=call('EC_RUN');return result,text()
    return c,s,call,text,command


def main():
    c,s,call,text,command=context();model=bytearray();cursor=0;rng=random.Random(222)
    for _ in range(5000):
        op=rng.choice(['put','left','right','del','erase','top','end'])
        if op=='put':
            char=rng.randrange(256);c.c=char;bad=call('EB_PUT')[0]
            assert bad==(len(model)==64)
            if not bad:model[cursor:cursor]=bytes([char]);cursor+=1
        elif op=='left':
            bad=call('EB_LEFT')[0];assert bad==(cursor==0)
            if not bad:cursor-=1
        elif op=='right':
            bad=call('EB_RIGHT')[0];assert bad==(cursor==len(model))
            if not bad:cursor+=1
        elif op=='del':
            bad=call('EB_DEL')[0];assert bad==(cursor==len(model))
            if not bad:del model[cursor]
        elif op=='erase':
            bad=call('EB_ERASE')[0];assert bad==(cursor==0)
            if not bad:cursor-=1;del model[cursor]
        elif op=='top':call('EB_TOP');cursor=0
        else:call('EB_END');cursor=len(model)
        assert text()==(bytes(model),cursor),op
    before=tuple(c.word(s[k]) for k in ['EB_FIRST','EB_FRONT','EB_BACK','EB_LIMIT'])
    c.hl=0x6040;c.de=0x6000
    assert call('EB_INIT')[0]
    assert tuple(c.word(s[k]) for k in ['EB_FIRST','EB_FRONT','EB_BACK','EB_LIMIT'])==before
    _,_,_,_,full=context(4)
    assert not full(b'iABCD\x1aB2C')[0][0]
    assert full(b'i!\x1a')==((True,ord('>')),(b'ABCD',2))
    assert full(b'B#C')[1]==(b'ABCD',4)
    assert full(b'B#DiWXYZ\x1a')[1]==(b'WXYZ',4)
    cases=[(b'iHello world\x1aB2C2DiXX\x1a',b'HeXXo world',4),
           (b'IHello\x1aiWorld\x1a',b'HELLOWorld',10),
           (b'UiMixed\x1a-UiCase\x1a',b'MIXEDCase',9),
           (b'iabc',b'abc\r\n',5),(b'iA\x0cB\x1a',b'A\r\nB',4),
           (b'iabc\x1aB#C',b'abc',3),(b'iabc\x1a-#D',b'',0),
           (b'iabc\x1aB65536C',b'abc',0),(b'iabc\x1a0B',b'abc',3),
           (b'iabc\x1aB2C-1D',b'ac',1)]
    for line,want,pos in cases:
        _,_,_,_,run=context();(bad,flag),result=run(line)
        assert not bad and result==(want,pos),(line,flag,result)
    _,_,_,_,run=context(2)
    assert run(b'ixyz\x1a')==((True,ord('>')),(b'xy',2))
    _,_,_,_,run=context()
    assert run(b'2Iabc\x1a')[0]==(True,ord('?'))
    assert run(b'i')[0]==(True,1) # interactive mode is the caller's next stage
    print('PASS: 5000 gap-buffer operations, capacity guards, inline I/B/C/D/U, counts/case, partial overflow and interactive handoff')


if __name__=='__main__':main()
