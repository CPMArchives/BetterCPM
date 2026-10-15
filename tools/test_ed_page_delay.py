#!/usr/bin/env python3
"""P page ranges and Z polling/count/key semantics with pinned delay loop."""
from test_ed_buffer import context
from pathlib import Path


def machine(body=b'',start=0,ready_after=None,key=ord('x')):
    c,s,call,state,run=context(2048,execution_limit=2000000);out=[];polls=0;keys=0
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal polls,keys
        if c.c==2:out.append(c.e);return 0
        if c.c==11:
            polls+=1;return 255 if ready_after is not None and polls>ready_after else 0
        if c.c==1:keys+=1;return key
        raise AssertionError(('unexpected BDOS',c.c))
    c.port_read=io
    for byte in body:c.c=byte;call('EB_PUT')
    call('EB_TOP')
    for _ in range(start):call('EB_RIGHT')
    return c,s,call,state,run,out,lambda:(polls,keys)


def main():
    lines=[f'{i:02}\r\n'.encode() for i in range(70)];body=b''.join(lines)
    for command,start,line,count in [(b'0P',0,0,23),(b'P',0,23,23),(b'2P',0,46,46),
                                     (b'-P',50*4,27,23),(b'-2P',50*4,4,46),(b'#P',0,69,47)]:
        c,s,call,state,run,out,polls=machine(body,start)
        assert not run(b'-V')[0][0]
        assert run(command)[0]==(False,0) and state()==(body,line*4),(command,state())
        if command==b'2P':expected=b''.join(lines[23:69])
        elif command==b'-2P':expected=b''.join(lines[27:50]+lines[4:27])
        elif command==b'#P':expected=b''.join(lines[23:])
        else:expected=b''.join(lines[line:line+count])
        assert bytes(out)==expected,(command,bytes(out),expected)
    c,s,call,state,run,out,polls=machine()
    code=bytearray(c.mem[s['GZ_TICK']:s['GZ_TICK']+12])
    reference=Path(__file__).resolve().parents[1]/'third_party/dri-ed/ED-CPM22-reference.COM'
    original=reference.read_bytes()[0x1a11-256:0x1a11-256+12]
    code[5:7]=original[5:7];code[9:11]=original[9:11]  # relocated branch addresses
    assert bytes(code)==original
    assert run(b'2Z')[0]==(False,0) and polls()==(40,0)
    assert run(b'-Z')[0]==(True,ord('?')) and polls()==(40,0)
    c,s,call,state,run,out,polls=machine()
    assert run(b'0Z')[0]==(False,0) and polls()==(0,1)
    c,s,call,state,run,out,polls=machine(key=26)
    assert run(b'0Z')[0]==(True,0) and polls()==(0,1)
    c,s,call,state,run,out,polls=machine(ready_after=0)
    c.mem[s['EC_FLAG']]=ord('#')
    assert run(b'Z')[0]==(True,ord('#')) and polls()==(1,1)
    print('PASS: P forward/backward/current/end pages and Z counts, polling, acknowledgment and prior-break flags')


if __name__=='__main__':main()
