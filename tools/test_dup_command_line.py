#!/usr/bin/env python3
"""DUP parser, direct dispatch and cleanup gates without media side effects."""
from pathlib import Path
from test_utility_versions import address, runner, output
from utility_versions import banner
ROOT=Path(__file__).resolve().parents[1]
def main():
    image=(ROOT/'build/utilities/DUP.COM').read_bytes()
    listing=(ROOT/'build/utilities/dup.lst').read_text()
    valid={'':(0,0,0),' /FORMAT B:':(1,1,0),' /copy a: d: ':(2,0,3),
           ' /CHECK C:':(3,2,0),' /FORMAT A:':(1,0,0)}
    invalid=[' /FORMAT',' /FORMAT E:',' /COPY A:',' /COPY A: A:',
             ' /COPY A:B:',' /CHECK B: C:',' /CHECK B7:',
             ' /CHECK B:*.COM',' /CHECK B[-]:',' /FORMAT B: /CHECK B:',
             ' /FOR B:',' /CHECKB:',' /COPY A: E:',' /CHECK B: /Y']
    for tail in list(valid)+invalid:
        c=runner(image);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        c.run(address(listing,'DCPARSE'),limit=100000)
        assert c.carry == (tail in invalid),tail
        if tail in valid:
            got=tuple(c.mem[address(listing,n)] for n in ['DCMODE','DCFIRST','DCSECOND'])
            assert got==valid[tail],(tail,got)
    for mode,label in [(1,'DFORMAT'),(2,'DCOPY'),(3,'DCHECK')]:
        c=runner(image);c.mem[address(listing,'DCMODE')]=mode
        c.mem[address(listing,'CLEANUP'):address(listing,'CLEANUP')+2]=b'\xaf\xc9'
        for other in ['DFORMAT','DCOPY','DCHECK']:
            at=address(listing,other)
            c.mem[at:at+6]=bytes([0x3e,1 if other==label else 2,0x32,8,0x70,0xc9])
        c.run(address(listing,'DMAIN'),limit=100000)
        assert c.mem[0x7008]==1,label
        c.mem[0x7008]=0
        c.run(address(listing,'DMAIN'),limit=100000)
        assert c.mem[0x7008]==0,'direct operation restarted instead of exiting'
    for tail in ['/VER','/VER /CHECK B:']:
        c=runner(image);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        c.run(256,limit=100000)
        assert output(c)==(banner('DUP')+'\r\n' if tail=='/VER' else 'Invalid /VER usage.\r\n')
    print('DUP command parsing, direct engine dispatch, one-shot exit and /VER checks pass')
if __name__=='__main__':main()
