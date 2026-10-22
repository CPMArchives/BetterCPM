#!/usr/bin/env python3
"""Run the complete example consumer with an independent cell backend."""
import json
from build_shared_ui_fixtures import BUILD
from test_bios import Z80


def execute(keys,width=80,tail=b'',backend=True):
    c=Z80(b'');image=(BUILD/'UIEX.COM').read_bytes();c.mem[256:256+len(image)]=image
    c.mem[5:8]=b'\xd3\x00\xc9';c.mem[0xf000:0xf003]=b'\xd3\x01\xc9'
    c.mem[0xf100:0xf109]=b'SCR\x01\0'+bytes([24,width,255,255])
    c.mem[0x80]=len(tail);c.mem[0x81:0x81+len(tail)]=tail
    screen=[bytearray(b'S'*width) for _ in range(24)];x=y=0;queue=list(keys);frames=[]
    def io(port,value):
        nonlocal x,y
        if port&255==0:
            if c.c==182:
                if backend:c.setword(c.de+12,0xf000);c.a=0
                else:c.a=255
            elif c.c==6:
                assert c.e==255
                frames.append([bytes(v).decode('latin1') for v in screen]);assert queue,'input exhausted'
                c.a=queue.pop(0)
            elif c.c==9:
                message=bytes(c.mem[c.de:c.mem.index(36,c.de)])
                assert not backend and message.startswith(b'UIEX requires callable SCRN')
            else:raise AssertionError(('BDOS',c.c))
        else:
            op=c.a
            if op==12:c.hl=0xf100
            elif op==6:y,x=c.b,c.c;assert y<24 and x<width
            elif op==7:
                assert x<width;screen[y][x]=c.c;x+=1
            elif op==8:screen[y][x:]=bytes([c.c])*(width-x)
            elif op==9:
                screen[y][x:]=bytes([c.c])*(width-x)
                for row in range(y+1,24):screen[row][:]=bytes([c.c])*width
            else:raise AssertionError(('SCRN',op))
    c.port_write=io;c.run(0x100,limit=1000000);assert not queue
    return [[s.translate(str.maketrans({chr(i):chr(i&127) for i in range(128,256)})) for s in frame] for frame in frames]


def check(frames):
    for frame in frames:
        assert frame[0].startswith('Shared UI developer example')
        assert frame[2].startswith('Body sentinel: unchanged by prompts.')


def main():
    assert execute(b'',backend=False)==[]
    reports=[]
    for tail in (b'',b'/40'):
        frames=execute(b'\rYNQ',tail=tail);check(frames)
        assert frames[0][23].startswith('Value: [DEFAULT] _')
        assert frames[1][1].startswith('DEFAULT') and frames[1][23].startswith('Accept? (Y/N) [N]')
        assert frames[2][23].startswith('Accept? (Y/N) [N] Demo rejects Y;')
        if tail:assert frames[2][23][38]=='~' and not frames[2][23][39:].strip()
        assert frames[-1][3].startswith('Choice N accepted')
        frames=execute(b'BAD\r\x19OK\r\rQ',tail=tail);check(frames)
        assert any(f[23].startswith('BAD is rejected;') for f in frames)
        assert any(f[23].startswith('Value: [DEFAULT] _') for f in frames[1:])
        assert frames[-1][1].startswith('OK') and frames[-1][3].startswith('Choice N accepted')
        frames=execute(b'\x03\x1bQ',tail=tail);check(frames)
        assert frames[-1][1].startswith('Cancelled') and frames[-1][3].startswith('Cancelled')
        reports.append({'layout':40 if tail else 80,'scenarios':3,'result':'pass'})
    (BUILD/'consumer-results.json').write_text(json.dumps(reports,indent=2)+'\n');print(reports)


if __name__=='__main__':main()
