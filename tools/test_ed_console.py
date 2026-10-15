#!/usr/bin/env python3
"""Single console turns: prompts, input, file-action handoff and safe errors."""
from test_ed_buffer import context


def main():
    c,s,call,text,run=context(64);lines=[];keys=[];output=[];calls=[]
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        calls.append(c.c)
        if c.c==2:output.append(c.e);return 0
        if c.c==10:
            line=lines.pop(0);assert len(line)<c.mem[c.de]
            c.mem[c.de+1]=len(line);c.mem[c.de+2:c.de+2+len(line)]=line
            output.extend(line+b'\r');return 0
        if c.c==1:
            key=keys.pop(0);output.append(key);return key
        if c.c==11:return 0
        raise AssertionError(('unexpected file/mutation BDOS',c.c))
    c.port_read=io
    def turn(line,keyboard=b''):
        output.clear();calls.clear();lines.append(line);keys.extend(keyboard)
        result=call('EU_READ');assert not lines and not keys
        return result,bytes(output)
    result,out=turn(b'i',b'abc\rdef\x1a')
    assert result==(False,0) and text()==(b'abc\r\ndef',8)
    assert out.startswith(b'     : *i\r\n    1:  ')
    assert out.endswith(b'\r\n')
    result,out=turn(b'B-V#T');assert result==(False,0)
    assert out.endswith(b'abc\r\ndef') and text()[1]==0
    result,out=turn(b'E');assert result==(False,ord('E'))
    assert b'(Y/N)' not in out
    result,out=turn(b'Q',b'N');assert result==(False,0) and b'Q-(Y/N)?N\r\n' in out
    result,out=turn(b'q',b'y');assert result==(False,ord('Q'))
    result,out=turn(b'o',b'Y');assert result==(False,ord('O'))
    result,out=turn(b'H');assert result==(False,ord('H'))
    result,out=turn(b'2q');assert result==(False,0) and b'BREAK "?" AT Q\r\n' in out
    result,out=turn(b'0V');assert result==(False,0) and out.endswith(b'   56/   64\r\n')
    result,out=turn(b'0V2C');assert result==(False,0) and text()[1]==2
    result,out=turn(b'B');assert result==(False,0)
    result,out=turn(b'');assert result==(False,0) and out.endswith(b'def') and text()[1]==5
    result,out=turn(b'fmissing')
    assert result==(False,0) and b'BREAK "#" AT \r\r\n' in out
    result,out=turn(b'i',b'q'*57)
    assert result==(False,0) and b'BREAK ">" AT q\r\n' in out
    assert len(text()[0])==64  # successful bytes survive the overflow
    # Internal code never performs a file action. Only the future owner may
    # turn E/H/O/Q requests into stream/commit operations.
    assert set(calls)<={1,2,10,11}
    print('PASS: console prompts, interactive turn, E/H/O/Q authorization handoff, errors, 0V and blank-line movement/type')


if __name__=='__main__':main()
