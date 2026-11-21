#!/usr/bin/env python3
"""Execute MCL worker parsing, bounds, publication and abort-latch contracts."""
from pathlib import Path
from pds_layout import header,layout
from system_layout import LAYOUT as L
from test_ccp import cpu,call,symbol,BASE,install_bdos
from build_z80pack_image import symbols

ROOT=Path(__file__).resolve().parents[1]
W=symbols(ROOT/'build/pds/worker.lst')


def machine(enabled=True,history=2):
    c=cpu(bind=False);d=header(history,int(enabled),1);p=layout(d,L['SYSTEM'])
    c.mem[p['low']:L['SYSTEM']]=bytes(p['total'])
    c.mem[L['SYSTEM']-12:L['SYSTEM']]=d
    c.setword(L['SYSTEM']+0x8c,BASE)
    c.ix=symbol('HF_MAIN');c.hl=symbol('CCP_RAW');call(c,0x1706)
    out=[]
    def bdos(port,value):
        if c.c==9:out.append(bytes(c.mem[c.de:c.mem.index(36,c.de)]))
        c.a=0
    install_bdos(c,b'\xd3\xff\xc9');c.port_write=bdos
    c.mem[L['SYSTEM']+0x95]=3
    return c,p,p['owners']['MCL'][0],out


def line(c,text):
    c.mem[symbol('CCP_COUNT')]=len(text)
    c.mem[symbol('CCP_DATA'):symbol('CCP_DATA')+len(text)]=text
    call(c,symbol('CCP_MCL')+6)
    return selected(c)


def selected(c):
    at=symbol('CCP_DATA');n=c.mem[symbol('CCP_COUNT')]
    return bytes(c.mem[at:at+n])


def main():
    cases=[(b'A;B;C',[b'A',b'B',b'C']),
           (b';A;;B;',[b'A',b'B']),
           (b' ;  ; ',[]),
           (b'GET "A;B";DIR',[b'GET "A;B"',b'DIR']),
           (b' A ; B ',[b' A ',b' B ']),
           (b'A"";B',[b'A""',b'B']),
           (b'A;'+b'B'*125,[b'A',b'B'*125]),
           (b'A'*127,[b'A'*127])]
    for text,expected in cases:
        c,p,at,out=machine();outside=bytes(c.mem[at+128:L['SYSTEM']])
        first=line(c,text);got=[first] if first else []
        while c.mem[at+1]:
            call(c,symbol('CCP_MCL'))
            if c.carry:got.append(selected(c))
        assert got==expected,(text,got,expected)
        assert bytes(c.mem[at:at+128])==bytes(128)
        assert bytes(c.mem[at+128:L['SYSTEM']])==outside and not out
    for h in (0,1,3):
        c,p,at,out=machine(history=h)
        assert line(c,b'A;B')==b'A'
        call(c,symbol('CCP_MCL'))
        assert c.carry and selected(c)==b'B'
    for text in (b'A;"B',b'A";B',b'A\x01;B',b'A'*128):
        c,p,at,out=machine();assert line(c,text)==b''
        assert bytes(c.mem[at:at+128])==bytes(128) and b'MCL invalid.' in out[-1]
    c,p,at,out=machine(False)
    assert line(c,b'A;"B')==b'A;"B' and not out
    # Pending validation happens before copy/dispatch and canonicalizes errors.
    for bad in (b'\x00\x01',b'\x7e\x01',b'\x01\x02A',b'\x01\x01"',b'\x01\x01\x7f',b'\x01\x01AB',b'\x00\x00X'):
        c,p,at,out=machine();c.mem[at:at+128]=bad.ljust(128,b'\0')
        call(c,symbol('CCP_MCL'))
        assert not c.carry and bytes(c.mem[at:at+128])==bytes(128)
        assert b'MCL invalid.' in out[-1]
    # Ordinary warm entry preserves the queue; a recognized abort clears it.
    for abort in (False,True):
        c,p,at,out=machine();assert line(c,b'A;B')==b'A'
        before=bytes(c.mem[at:at+128]);c.mem[L['SYSTEM']+0x95]=3|(4 if abort else 0)
        call(c,0x1700)
        assert c.z and c.mem[L['SYSTEM']+0x95]==3
        assert bytes(c.mem[at:at+128])==(bytes(128) if abort else before)
    # Runtime code is inside CCP, independent of the finished-program loader.
    c,p,at,out=machine();line(c,b'A;B')
    c.mem[0x1700:0x1e00]=b'\x76'*(0x1e00-0x1700)
    call(c,symbol('CCP_MCL'))
    assert c.carry and selected(c)==b'B'
    # A changed immutable directory stops before copying any pending text.
    c,p,at,out=machine();line(c,b'A;B');before=bytes(c.mem[at:at+128])
    c.mem[L['SYSTEM']-2]^=1
    try:
        call(c,symbol('CCP_MCL'))
    except AssertionError as error:
        assert 'execution limit reached' in str(error)
    else:raise AssertionError('invalid metadata did not stop acquisition')
    assert bytes(c.mem[at:at+128])==before and b'cold boot required' in out[-1]
    # The callable transient cancel preserves the caller's register context.
    c,p,at,out=machine();line(c,b'A;B')
    c.a=37;c.bc=0x1234;c.de=0x5678;c.hl=0x9abc;c.ix=0x789a
    call(c,symbol('CCP_MCL')+3)
    assert (c.a,c.bc,c.de,c.hl,c.ix)==(37,0x1234,0x5678,0x9abc,0x789a)
    assert bytes(c.mem[at:at+128])==bytes(128)
    print('PASS MCL split/quotes/empty/max bounds, disabled legacy input, invalid-owner rejection, warm/abort lifetime and cancel context')


if __name__=='__main__':main()
