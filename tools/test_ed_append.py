#!/usr/bin/env python3
"""Source append: counts, cursor restoration, uppercase and lossless overflow."""
from test_ed_source import stream


def setup(body):
    padded=body+b'\x1a'*(128-len(body)%128)
    c,s,call,calls,pending=stream([padded[i:i+128] for i in range(0,len(padded),128)])
    def run(line):
        c.mem[0x5000:0x5000+len(line)]=line;c.hl=0x5000;c.b=len(line)
        return call('EC_RUN')
    def state():
        f=c.word(s['EB_FRONT']);b=c.word(s['EB_BACK'])
        return bytes(c.mem[0x6000:f]+c.mem[b:0x6040]),f-0x6000
    return c,s,call,run,state


def main():
    c,s,call,run,state=setup(b'one\r\ntwo\r\nlast')
    assert run(b'iHEAD\x1aB2C')==(False,0)
    assert run(b'a')==(False,0) and state()==(b'HEADone\r\n',2)
    assert run(b'2a')==(False,0) and state()==(b'HEADone\r\ntwo\r\nlast',2)
    assert run(b'#a')==(False,0) and state()[1]==2
    c,s,call,run,state=setup(b'Mixed\r\ncase')
    assert run(b'U#a')==(False,0) and state()==(b'MIXED\r\nCASE',0)
    c,s,call,run,state=setup(b'x\n'*30)
    assert run(b'0a')==(False,0) and state()==(b'x\n'*16,0)
    assert run(b'-a')[0] and state()==(b'x\n'*16,0)
    c,s,call,run,state=setup(b'z'*70)
    assert run(b'#a')==(True,ord('>')) and state()==(b'z'*64,64)
    assert c.mem[s['ES_POS']]==64
    assert run(b'-D')==(False,0)
    assert run(b'a')==(True,ord('>')) and c.mem[s['ES_POS']]==65
    print('PASS: append counts/EOF, original cursor, global uppercase, half-buffer append and lossless overflow')


if __name__=='__main__':main()
