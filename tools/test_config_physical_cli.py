#!/usr/bin/env python3
"""Physical CONFIG CLI: full parsing, atomic profile updates and boot protection."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    addr=lambda n:address(listing,n)
    def setup(tail):
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[:3]=bytes.fromhex('c3ffff')
        c.mem[5:8]=bytes((0xdb,254,0xc9));data=tail.encode()
        c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        return c
    valid={
      '/PHYSICAL=1 /TRACKS=35':(1,2,[None,35,None,None,None,None]),
      ' /physical=0 /settle=0 ':(0,32,[None,None,None,None,None,0]),
      '/PHYSICAL=3 /TYPE=8 /TRACKS=77 /SIDES=1 /STEP=30 /SPINUP=16 /SETTLE=255':(3,63,[8,77,1,3,16,255]),
      '/PHYSICAL=2\t/STEP=20 /SETTLE=015':(2,40,[None,None,None,2,None,15]),
      '/PHYSICAL=1 /STEP=12':(1,8,[None,None,None,1,None,None]),
      '/PHYSICAL=1 /STEP=6':(1,8,[None,None,None,0,None,None]),
      '/PHYSICAL=1 /TRACKS=40 /SIDES=2 /SPINUP=0':(1,22,[None,40,2,None,0,None]),
      '/PHYSICAL=1 /TRACKS=80':(1,2,[None,80,None,None,None,None]),
    }
    for tail,(drive,mask,values) in valid.items():
        c=setup(tail);c.port_read=lambda p:(_ for _ in ()).throw(AssertionError('parser did I/O'))
        c.run(addr('CF_PARSE'),limit=100000)
        assert not c.carry,tail
        assert c.mem[addr('CF_MODE')]==3 and c.mem[addr('CD_DRIVE')]==drive,tail
        assert c.mem[addr('CD_MASK')]==mask,tail
        for i,value in enumerate(values):
            if value is not None:assert c.mem[addr('CD_VALS')+i]==value,(tail,i)
    invalid=['/PHYSICAL=1','/PHYSICAL=4 /SETTLE=1','/PHYSICAL=-1 /SETTLE=1',
      '/PHYSICAL=1/SETTLE=1','/PHYSICAL=1 /TYPE=3','/PHYSICAL=1 /TRACKS=79',
      '/PHYSICAL=1 /SIDES=0','/PHYSICAL=1 /SIDES=3','/PHYSICAL=1 /STEP=0',
      '/PHYSICAL=1 /STEP=7','/PHYSICAL=1 /SPINUP=17','/PHYSICAL=1 /SETTLE=256',
      '/PHYSICAL=1 /SETTLE=65536','/PHYSICAL=1 /SETTLE=+1','/PHYSICAL=1 /SETTLE=',
      '/PHYSICAL=1 /SETTLE=1 /SETTLE=2','/PHYSICAL=1 /TYPE=5 /UNKNOWN=1',
      '/PHYSICAL=1 /SETTLE=1 /PHYSICAL=2','/PHYSICAL=1 /SETTLE=1 X',
      '/PHYSICAL=1 /SETTLE=1 /SHOW','/TRACKS=80 /PHYSICAL=1']
    for tail in invalid:
        c=setup(tail);c.run(addr('CF_PARSE'),limit=100000);assert c.carry,tail
        calls=[];out=[]
        c=setup(tail)
        def io(p):
            calls.append(c.c);assert c.c==2,('invalid request did I/O',tail,c.c)
            out.append(c.e);return 0
        c.port_read=io;c.run(256,limit=150000)
        assert bytes(out)==b'Invalid CONFIG usage.\r\n',tail
    cases=[('menu-boot','/PHYSICAL=0 /TRACKS=35',None),
           ('menu-detach','/PHYSICAL=1 /TRACKS=35',None),
           ('detach','/PHYSICAL=1 /TRACKS=35',None),
           ('boot','/PHYSICAL=0 /TRACKS=40',None),
           ('sides','/PHYSICAL=0 /SIDES=1',None),
           ('timing','/PHYSICAL=0 /SETTLE=20',None),
           ('readonly','/PHYSICAL=1 /SETTLE=20','get-profile'),
           ('guard-read','/PHYSICAL=1 /TRACKS=35','get-boot'),
           ('rejected','/PHYSICAL=1 /TRACKS=35','set-profile'),
           ('cleanup-read','/PHYSICAL=1 /TRACKS=35','get-binding'),
           ('cleanup-write','/PHYSICAL=1 /TRACKS=35','detach')]
    for name,tail,fault in cases:
        c=setup(tail);c.run(addr('CF_PARSE'),limit=100000);assert not c.carry
        profiles=[bytearray([5,80,2,0,2,15]) for _ in range(4)]
        bindings=[bytearray(64) for _ in range(4)]
        for n,physical,tracks,flags in [(0,0,80,64),(1,1,80,64),(2,1,40,0),(3,255,0,0)]:
            bindings[n][0]=physical;bindings[n][16]=tracks;bindings[n][19]=flags
        before=[bytes(x) for x in profiles];oldbind=[bytes(x) for x in bindings]
        ops=[];resets=[];out=[]
        c.mem[addr('API'):addr('API')+3]=bytes((0xdb,230,0xc9))
        def io(port):
            if port&255==254:
                if c.c==2:out.append(c.e);return 0
                assert c.c==37,('unexpected filesystem/write/prompt',c.c)
                resets.append(c.de);return 0
            assert port&255==230
            op=c.b;at=c.de;n=c.mem[at];ops.append((op,n))
            fail=(fault=='get-profile' and op==1 or fault=='set-profile' and op==2 or
                  fault=='get-boot' and op==3 and n==0 or
                  fault=='get-binding' and op==3 and n==1 or
                  fault=='detach' and op==4 and n==1)
            if fail:c.z=False;return 1
            if op==1:c.mem[at+1:at+7]=profiles[n]
            elif op==2:profiles[n][:]=c.mem[at+1:at+7]
            elif op==3:c.mem[at+1:at+65]=bindings[n]
            elif op==4:
                assert n!=0 and c.mem[at+1]==255,'unsafe boot/binding change'
                bindings[n][0]=255
            else:raise AssertionError(('unexpected API operation',op))
            c.z=True;return 0
        c.port_read=io
        if name.startswith('menu-'):
            drive=c.mem[addr('CD_DRIVE')]
            c.mem[addr('PHINDEX')]=drive;c.mem[addr('PHREQ')]=drive
            c.mem[addr('PHREQ')+1:addr('PHREQ')+7]=profiles[drive]
            c.mem[addr('FIELD')]=1;c.a=35
            c.mem[addr('PHEDIT'):addr('PHEDIT')+3]=bytes.fromhex('c3ffff')
            c.mem[addr('ERROR')]=0xc9
            c.run(addr('PHSAVE'),limit=200000)
        else:c.run(addr('CD_APPLY'),limit=200000)
        text=bytes(out)
        assert b'Push ENTER' not in text
        if name in ('menu-boot','boot','sides','readonly','guard-read','rejected'):
            assert [bytes(x) for x in profiles]==before and [bytes(x) for x in bindings]==oldbind
            if name!='menu-boot':assert b'Nothing changed.' in text,(name,text)
            assert not any(op==4 for op,n in ops)
        elif name in ('menu-detach','detach'):
            assert profiles[1][1]==35 and bindings[1][0]==bindings[2][0]==255
            assert bindings[0][0]==0 and resets==[2,4]
            if name=='detach':assert b'unconfigured' in text and b'until cold boot' in text
        elif name=='timing':
            assert profiles[0][-1]==20 and [bytes(x) for x in bindings]==oldbind
            assert b'until cold boot' in text
        else:
            assert profiles[1][1]==35 and b'binding cleanup incomplete.' in text
            assert b'Nothing changed.' not in text and b'until cold boot' not in text
    print('PASS: physical CLI parsing, full validation before I/O, merged profile commit, boot geometry guard, detach/reset and honest partial-failure reporting')


if __name__=='__main__':main()
