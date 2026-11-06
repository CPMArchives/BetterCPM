"""Check case-insensitive DIR operands without modifying the caller's tail."""
from pathlib import Path
import re
from test_bios import Z80
from test_dir_whereis import execute, row

ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/DIR.COM').read_bytes()
    listing=(ROOT/'build/utilities/dir-transient.lst').read_text()
    at=lambda n:int(re.search(r'^([0-9a-f]{4}).*\b'+n+':',listing,re.M|re.I)[1],16)
    cases=[('*.com',b'????????COM'),('foo.com',b'FOO     COM'),
           ('f?*.CoM',b'F???????COM'),('a[0,2]:foo.com[$r/o]',b'FOO     COM'),
           ('a0:az_{~.com /s=t-',b'AZ_{~   COM')]
    for tail,expected in cases:
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5]=0x76
        raw=tail.encode();c.mem[0x6000:0x6000+len(raw)]=raw
        c.hl=0x6000;c.b=len(raw);c.d=0;c.e=0
        c.run(at('DP_PARSE'),limit=100000)
        assert not c.carry,tail
        assert bytes(c.mem[at('FS_FCB')+1:at('FS_FCB')+12])==expected,tail
        assert bytes(c.mem[0x6000:0x6000+len(raw)])==raw,tail
    rows={0:[row(0,'FOO.COM'),row(0,'OTHER.DAT')]}
    for tail in ('*.com /whereis','*.CoM /WHEREIS','foo.com /whereis'):
        out,_,_,_=execute(tail,rows,configured=(0,))
        assert 'A0:FOO.COM' in out and 'OTHER.DAT' not in out,out
    print('PASS DIR lowercase/mixed-case names, wildcards, qualifiers, punctuation, unchanged tail and WHEREIS')


if __name__=='__main__':main()
