#!/usr/bin/env python3
"""W writes complete lines and restores the surviving editing position."""
from test_ed_output import output


def setup(body,fail_at=None):
    c,s,call,put,records,calls=output(fail_at,2,capacity=1024)
    c.hl=0x6000;c.de=0x6400;call('EB_INIT')
    def run(line):
        c.mem[0x5000:0x5000+len(line)]=line;c.hl=0x5000;c.b=len(line)
        return call('EC_RUN')
    for byte in body:
        c.c=byte;assert not call('EB_PUT')[0]
    def state():
        f=c.word(s['EB_FRONT']);b=c.word(s['EB_BACK'])
        return bytes(c.mem[0x6000:f]+c.mem[b:0x6400]),f-0x6000
    def written():return b''.join(records)+bytes(c.mem[s['EW_DATA']:s['EW_DATA']+c.mem[s['EW_POS']]])
    return c,s,call,run,state,written,calls


def main():
    for prefix,want,pos in [(b'B',b'two\r\nlast',0),(b'B7C',b'two\r\nlast',2),
                            (b'',b'two\r\nlast',9)]:
        c,s,call,run,state,written,_=setup(b'one\r\ntwo\r\nlast')
        if prefix:assert not run(prefix)[0]
        assert not run(b'w')[0] and state()==(want,pos)
        assert written()==b'one\r\n' and c.word(s['EB_BASE'])==2
        assert not run(b'#w')[0] and state()==(b'',0)
        assert written()==b'one\r\ntwo\r\nlast'
    c,s,call,run,state,written,_=setup(b'x\n'*300)
    assert not run(b'0w')[0] and len(state()[0])==512 and len(written())==88
    before=state();assert run(b'-w')[0] and state()==before
    c,s,call,run,state,written,calls=setup(b'x'*200,1)
    assert run(b'#w')==(True,ord('?'))
    assert written()==b'x'*128 and state()==(b'x'*72,0)
    assert c.mem[s['EX_ERROR']]==2
    count=len(calls);assert run(b'w')[0] and len(calls)==count and state()==(b'x'*72,0)
    print('PASS: W line counts, surviving cursor, half-buffer write, line base and failed-write retention')


if __name__=='__main__':main()
