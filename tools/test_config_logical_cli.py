#!/usr/bin/env python3
"""Logical CONFIG CLI: quoted names, unique resolution, boot protection and errors."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text();addr=lambda n:address(listing,n)
    def cpu(tail):
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[:3]=bytes.fromhex('c3ffff')
        c.mem[5:8]=bytes((0xdb,254,0xc9));data=tail.encode()
        c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        return c
    for tail,mode,drive,physical,name in [
      ('/LOGICAL=B /PHYSICAL=1 /FORMAT="mm 80t ds data"',4,1,1,'MM 80T DS DATA'),
      (' /logical=d\t/physical=3 /format="'+32*'x'+'" ',4,3,3,32*'X'),
      ('/LOGICAL=C /UNBIND',5,2,None,None),
      ('/LOGICAL=B /PHYSICAL=0 /FORMAT="NAME /VER"',4,1,0,'NAME /VER')]:
        c=cpu(tail);c.run(addr('CF_PARSE'),limit=100000)
        assert not c.carry and c.mem[addr('CF_MODE')]==mode,tail
        assert c.mem[addr('CL_DRIVE')]==drive
        if name is not None:
            assert c.mem[addr('CL_PHYS')]==physical
            assert bytes(c.mem[addr('CL_NAME'):addr('CL_NAME')+32])==name.ljust(32).encode()
    bad=['/LOGICAL=A /UNBIND','/LOGICAL=E /UNBIND','/LOGICAL=B:/UNBIND',
         '/LOGICAL=B/UNBIND','/LOGICAL=B /UNBIND EXTRA','/LOGICAL=B',
         '/LOGICAL=B /PHYSICAL=4 /FORMAT="X"','/LOGICAL=B /FORMAT="X" /PHYSICAL=1',
         '/LOGICAL=B /PHYSICAL=1 /FORMAT=X','/LOGICAL=B /PHYSICAL=1 /FORMAT=""',
         '/LOGICAL=B /PHYSICAL=1 /FORMAT="   "','/LOGICAL=B /PHYSICAL=1 /FORMAT="X',
         '/LOGICAL=B /PHYSICAL=1 /FORMAT="'+33*'X'+'"',
         '/LOGICAL=B /PHYSICAL=1 /FORMAT="X" /UNBIND',
         '/LOGICAL=B /PHYSICAL=1 /FORMAT="X\tY"']
    for tail in bad:
        c=cpu(tail);c.run(addr('CF_PARSE'),limit=100000);assert c.carry,tail
        c=cpu(tail);out=[]
        def io(port):
            assert c.c==2,('invalid tail performed I/O',tail,c.c)
            out.append(c.e);return 0
        c.port_read=io;c.run(256,limit=100000)
        assert bytes(out)==b'Invalid CONFIG usage.\r\n',tail
    c=cpu('/LOGICAL=B /PHYSICAL=1 /FORMAT="NAME /VER"')
    c.mem[addr('INIT'):addr('INIT')+3]=bytes.fromhex('c3ffff')
    c.port_read=lambda p:(_ for _ in ()).throw(AssertionError('quoted format was treated as version'))
    c.run(256,limit=100000)
    for case in ['bind','unknown','ambiguous','unsupported','tracks','sides','get-fail','set-fail','unbind']:
        tail='/LOGICAL=C /UNBIND' if case=='unbind' else '/LOGICAL=B /PHYSICAL=1 /FORMAT="Target"'
        c=cpu(tail);c.run(addr('CF_PARSE'),limit=100000);assert not c.carry
        names=['Other','Target']
        if case=='unknown':names=['Other']
        if case=='ambiguous':names=['TARGET','target']
        c.mem[addr('FCOUNT')]=len(names)
        for i,name in enumerate(names):c.mem[0x9000+i*32:0x9020+i*32]=name.ljust(32).encode()
        bind=bytearray(64);bind[0]=0;bind[16]=40;bind[19]=64
        old=bytearray([7]*64);active=bytearray(old);ops=[];resets=[];out=[]
        for label,port in [('FDBNAME',230),('FDBBIND',231),('API',232)]:
            c.mem[addr(label):addr(label)+3]=bytes((0xdb,port,0xc9))
        def io(port):
            port&=255
            if port==254:
                if c.c==2:out.append(c.e);return 0
                assert c.c==37,('unexpected file access/prompt',case,c.c)
                resets.append(c.de);return 0
            if port==230:
                assert case!='unbind';c.hl=0x9000+c.a*32;c.carry=False;return 0
            if port==231:
                assert case!='unbind'
                if case=='unsupported':c.carry=True;return 1
                c.mem[addr('BIND'):addr('BIND')+64]=bind;c.carry=False;return 0
            assert port==232
            op=c.b;at=c.de;ops.append(op)
            if op==1:
                if case=='get-fail':c.z=False;return 1
                profile=bytes([5,35 if case=='tracks' else 80,1 if case=='sides' else 2,0,2,15])
                c.mem[at+1:at+7]=profile
            elif op==4:
                if case=='set-fail':c.z=False;return 1
                if case=='unbind':active[0]=255
                else:active[:]=c.mem[at+1:at+65]
            else:raise AssertionError(op)
            c.z=True;return 0
        c.port_read=io;c.run(addr('CL_UNBIND') if case=='unbind' else addr('CL_BIND'),limit=200000)
        text=bytes(out);assert b'Push ENTER' not in text
        if case=='bind':
            expected=bytearray(bind);expected[0]=1
            assert active==expected and ops==[1,4] and resets==[2]
            assert b'until cold boot' in text
        elif case=='unbind':assert active[0]==255 and active[1:]==old[1:] and ops==[4] and resets==[4]
        else:
            assert active==old and not resets and b'Nothing changed.' in text,(case,text)
            if case in ('unknown','ambiguous','unsupported','tracks','sides','get-fail'):assert 4 not in ops
    # Catalogue failure returns directly for CLI; interactive callers retain pause.
    for mode in (0,4):
        c=cpu('');c.mem[addr('CF_MODE')]=mode;c.hl=addr('CL_BADFMT');calls=[]
        def io(port):
            calls.append(c.c)
            if c.c==2:return 0
            assert mode==0 and c.c==6;return 13
        c.port_read=io;c.run(addr('CF_FATAL'),limit=100000)
        assert (6 in calls)==(mode==0)
    print('PASS: logical parser/quote bounds, no side effects on invalid tails, exact case-insensitive/ambiguous names, backend rejection, unbind/reset, no-prompt CLI catalogue errors')


if __name__=='__main__':main()
