#!/usr/bin/env python3
"""Execute VAR's owner, transaction, expansion and reconstructed-code contracts."""
from pds_layout import header, layout
from system_layout import LAYOUT as L
from test_ccp import cpu,call,symbol,BASE,install_bdos


def machine(capacity=1):
    c=cpu(bind=False)
    d=header(2,1,capacity); p=layout(d,L['SYSTEM'])
    c.mem[p['low']:L['SYSTEM']]=bytes(p['total'])
    c.mem[L['SYSTEM']-12:L['SYSTEM']]=d
    c.setword(L['SYSTEM']+0x8c,BASE)
    c.ix=symbol('HF_MAIN');c.hl=symbol('CCP_RAW');call(c,0x1706)
    call(c,symbol('V_INIT'))
    out=bytearray()
    def bdos(port,value):
        if c.c==9:out.extend(c.mem[c.de:c.mem.index(36,c.de)])
        elif c.c==2:out.append(c.e)
        c.a=0
    install_bdos(c,b'\xd3\xff\xc9');c.port_write=bdos
    return c,p,out


def expand(c,text):
    c.mem[symbol('CCP_COUNT')]=len(text)
    c.mem[symbol('CCP_DATA'):symbol('CCP_DATA')+len(text)]=text
    call(c,symbol('V_EXPAND'))
    return bytes(c.mem[symbol('CCP_DATA'):symbol('CCP_DATA')+c.mem[symbol('CCP_COUNT')]])


def command(c,text):
    expand(c,text)
    if c.carry:return
    call(c,symbol('CCP_UPPER'));call(c,symbol('V_COMMAND'))


def main():
    for capacity in (1,2,3):
        c,p,out=machine(capacity);at,n=p['owners']['VAR'];outside=bytes(c.mem[at+n:L['SYSTEM']])
        command(c,b'VAR z=Last')
        command(c,b'var A=First= With Spaces ')
        command(c,b'VAR EMPTY=')
        out.clear();command(c,b'VAR')
        assert out==b'A=First= With Spaces \r\nEMPTY=\r\nZ=Last\r\n',out
        out.clear();command(c,b'VAR a');assert out==b'A=First= With Spaces \r\n'
        assert expand(c,b'%a%|%EMPTY%|%Z%|%%')==b'First= With Spaces ||Last|%' and not c.carry
        command(c,b'VAR A=Replaced')
        command(c,b'VAR P=%%A%%')
        assert expand(c,b'%P%')==b'%A%' and not c.carry
        command(c,b'VAR /d z')
        out.clear();expand(c,b'TYPE %z%');assert c.carry and b'undefined' in out
        for bad in (b'VAR 1X=no',b'VAR ABCDEFGHI=no',b'VAR A-B=no',b'VAR A =no',b'VAR /D A=x',b'VAR A extra',b'VAR A=\x1f',b'VAR A=\x7f'):
            before=bytes(c.mem[at:at+n]);out.clear();command(c,bad)
            assert b'invalid' in out and bytes(c.mem[at:at+n])==before,(bad,out)
        for bad in (b'%',b'%A',b'%1A%',b'%A-B%',b'%ABCDEFGHI%'):
            out.clear();expand(c,bad);assert c.carry and b'invalid' in out,(bad,out)
        command(c,b'VAR LONG='+b'x'*100)
        if capacity==1:
            # Several prior records occupy the small table; capacity failure is atomic.
            assert b'full' in out
            command(c,b'VAR /D A');command(c,b'VAR /D EMPTY');command(c,b'VAR /D P')
            command(c,b'VAR LONG='+b'x'*100)
        assert expand(c,b'x'*27+b'%LONG%')==b'x'*127 and not c.carry
        original=b'x'*28+b'%LONG%';expand(c,original)
        assert c.carry and bytes(c.mem[symbol('CCP_DATA'):symbol('CCP_DATA')+len(original)])==original
        before=bytes(c.mem[at:at+n])
        command(c,b'VAR EXTRA='+b'y'*110)
        if capacity==1:assert bytes(c.mem[at:at+n])==before
        # Reconstruct code/cache and validate warm preservation, with worker memory clobbered.
        c.mem[0x1700:0x1e00]=b'Z'*(0x1e00-0x1700)
        call(c,symbol('V_INIT'));assert expand(c,b'%LONG%')==b'x'*100
        assert bytes(c.mem[at+n:L['SYSTEM']])==outside
        # Cold composition's specified zero table is valid and loses previous names.
        c.mem[at:at+n]=bytes(n);call(c,symbol('V_INIT'))
        expand(c,b'%LONG%');assert c.carry
    # Malformed payloads reset only VAR and reject the selected command.
    for bad in (b'\xff\xff',b'\x03\0\0\0A',b'\x03\0\x01\0a',
                b'\x04\0\x01\x01A\x7f',b'\x06\0\x01\0B\x01\0A',
                b'\x06\0\x01\0A\x01\0A',b'\0\0x',b'\x03\0\x01\x7fA'):
        c,p,out=machine();at,n=p['owners']['VAR'];c.mem[at:at+n]=bad.ljust(n,b'\0')
        original=bytes(c.mem[p['low']:at]);expand(c,b'VER')
        assert c.carry and b'VAR reset.' in out and bytes(c.mem[at:at+n])==bytes(n),(bad,out)
        assert bytes(c.mem[p['low']:at])==original
    c,p,out=machine();c.mem[L['SYSTEM']-2]^=1
    try:expand(c,b'VER')
    except AssertionError as error:assert 'execution limit reached' in str(error)
    else:raise AssertionError('changed PDS metadata reached expansion')
    assert b'cold boot required' in out
    c,p,out=machine(0)
    assert expand(c,b'TYPE %unknown% %%')==b'TYPE %unknown% %%' and not c.carry
    command(c,b'VAR');assert b'disabled' in out
    for text in (b'A',b'B:',b'DIR',b'VARIABLE',b'VAX'):
        expand(c,text);call(c,symbol('CCP_UPPER'));call(c,symbol('V_COMMAND'));assert not c.carry,text
    print('PASS VAR owner validation, sorted edits, empty/query/delete, atomic full/error, one-pass/percent/overflow, warm/cold, disabled input and GET lifetime')


if __name__=='__main__':main()
