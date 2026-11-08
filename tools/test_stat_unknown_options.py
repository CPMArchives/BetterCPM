#!/usr/bin/env python3
"""Exercise STAT option rejection and missing files on compiled Z80 code."""
from test_bios import Z80
from test_utility_finalization import execute, ROOT


def run(tail):
    c=Z80(b''); data=(ROOT/'build/utilities/STAT.COM').read_bytes()
    c.mem[256:256+len(data)]=data
    c.mem[5:8]=b'\xd3\x00\xc9'; c.mem[0:3]=b'\xc3\xfe\xff'
    c.mem[128]=len(tail); c.mem[129:129+len(tail)]=tail.encode()
    original=bytes(c.mem[128:256]); output=bytearray(); calls=[]
    c.mem[0x8002]=3
    drive=user=0
    logged=1
    def service(port,value):
        nonlocal drive,user,logged
        calls.append(c.c)
        if c.c==9:output.extend(c.mem[c.de:c.mem.index(36,c.de)])
        elif c.c==2:output.append(c.e)
        elif c.c==0:c.pc=0xffff
        elif c.c==25:c.a=drive
        elif c.c==32:
            if c.e!=255:user=c.e
            c.a=user
        elif c.c==14:
            drive=c.e;logged|=1<<drive;c.a=0
        elif c.c==24:c.hl=logged
        elif c.c==29:c.hl=0
        elif c.c==31:c.hl=0x8000
        elif c.c==27:c.hl=0x8100
        elif c.c==17:c.a=255
        elif c.c==26:pass
        else:raise AssertionError(('unexpected BDOS',c.c))
    c.port_write=service;c.run(256,limit=2000000)
    assert (drive,user)==(0,0), (tail,drive,user)
    return output.decode(),calls,bytes(c.mem[128:256])==original


def main():
    for tail in ('/BOGUS',' /bogus ','\t/bogus','MISSING.DAT /BOGUS','/'):
        text,calls,preserved=run(tail)
        assert 'Invalid option.' in text and 'Usage: STAT' in text,(tail,text)
        assert 'File Not Found' not in text and set(calls)=={9} and preserved
    text,calls,_=run('MISSING.DAT')
    assert 'File Not Found' in text and 'Invalid option.' not in text and 17 in calls,text
    for tail in ('/BOGUS /H','/BOGUS /HELP'):
        assert execute('STAT',tail)[0]==execute('STAT','/HELP')[0]
    for tail in ('b:', 'c:', 'b3:', 'c07:', 'missing.dat', 'val:'):
        text,calls,_=run(tail)
        upper=run(tail.upper())[0]
        assert text==upper,(tail,text,upper)
        if tail.endswith(':') and tail[0] in 'bc':
            assert 'Invalid filespec' not in text and 'Bytes Remaining' in text,(tail,text)
            assert 14 in calls,(tail,calls)
    print('PASS STAT case-insensitive drive/user, filename and keyword operands, context restoration, option rejection and query precedence')


if __name__=='__main__':main()
