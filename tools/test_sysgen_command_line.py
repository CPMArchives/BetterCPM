#!/usr/bin/env python3
"""Reject malformed full tails before either SYSGEN source loader is entered."""
from pathlib import Path
from test_utility_versions import address, runner, output
from utility_versions import banner
ROOT=Path(__file__).resolve().parents[1]
def main():
    image=(ROOT/'build/utilities/SYSGEN.COM').read_bytes()
    listing=(ROOT/'build/utilities/sysgen.lst').read_text()
    valid=[' SYSTEM.SYS B:', ' C:SYSTEM.SYS D:', ' system.sys c: ', ' A: B:', ' A:', ' A: B:BACKUP.SYS', ' D: snap.sys',
           ' BACKUP.SYS C:', ' B:SNAP.BIN D:']
    invalid=[' SYSTEM.SYS B: EXTRA',' SYSTEM.SYS B:FOO',' B7:SYSTEM.SYS B:',
             ' E:SYSTEM.SYS B:',' SYSTEM.SYS E:',' SYSTEM.SYS A:',
             ' SYSTEM.SYS',' SYSTEM.SYS B: /CHECK',' SYSTEM.SYSB:',
             ' A: B: EXTRA',' A: E:',' A: A:', ' A:B:',
             ' A: B:TOOLONGXX.SYS', ' A: B:FOO.LONG', ' A: B:*.SYS',
             ' A: B7:FOO.SYS', ' A: B:[X].SYS', ' A: .SYS', ' A: FOO.',
             ' A: B:FOO..SYS', ' FOO.SYS BAR.SYS', ' B:FOO.SYS A:']
    for tail in valid+invalid:
        c=runner(image)
        data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        # Deliberately plausible CCP FCBs, even for malformed package tails.
        # A parser relying only on these would incorrectly enter LOADFILE.
        c.mem[0x5d:0x68]=b'SYSTEM  SYS' if 'system' in tail.lower() else b'           '
        c.mem[0x6c]=2
        for label,flag in [('LOADFILE',0x7008),('LOADDISK',0x7009)]:
            at=address(listing,label)
            c.mem[at:at+7]=bytes([0x3e,1,0x32,flag&255,flag>>8,0xaf,0xc9])
        c.run(address(listing,'PARSEARGS'),limit=100000)
        entered=bool(c.mem[0x7008] or c.mem[0x7009])
        assert entered == (tail in valid),(tail,c.a,entered)
        if tail in invalid:assert c.a==1,(tail,c.a)
    for tail in ['/VER', '/VER B:', 'A: B: /VER']:
        c=runner(image);data=tail.encode()
        c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        c.run(256,limit=100000)
        expected=(banner('SYSGEN')+'\r\n' if tail=='/VER'
                  else 'Invalid /VER usage.\r\n')
        assert output(c)==expected,(tail,output(c))
    print(f'{len(valid)+len(invalid)} SYSGEN command-tail and no-source-I/O checks pass')
if __name__=='__main__':main()
