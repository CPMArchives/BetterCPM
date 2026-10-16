#!/usr/bin/env python3
"""Capture assembled interactive completion before newline-free program output."""
from test_ccp import cpu,call,symbol,install_bdos

# Function 2 captures E and may clobber BC/HL. Other fixture calls return zero
# (drive A, user 0). This tests the CCP boundary, not a terminal emulator.
provider=bytes((0x79,0xFE,2,0x20,0x10,0x2A,0,0x75,0x73,0x23,
                0x22,0,0x75,0x01,0,0,0x21,0,0,0xAF,0xC9,0xAF,0xC9))
for command in (b'',b'PROBE',b'PROBE ONE.TXT'):
    m=cpu();install_bdos(m,provider);m.setword(0x7500,0x7600)
    call(m,symbol('CCP_HINIT'))
    m.mem[symbol('CCP_COUNT')]=len(command)
    start=symbol('CCP_DATA');m.mem[start:start+len(command)]=command
    m.mem[symbol('CCP_EDCUR')]=min(2,len(command))
    call(m,symbol('CCP_EDFIN'))
    captured=bytes(m.mem[0x7600:m.word(0x7500)])
    assert captured==b'\rA0>'+command+b' \r\n',repr(captured)
    # A transient which starts with printable output must begin a fresh row.
    m.c,m.e=2,ord('X');call(m,5)
    assert bytes(m.mem[0x7600:m.word(0x7500)]).endswith(b'\r\nX')
    print('PASS command completion CR/LF:',repr(command))
