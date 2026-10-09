#!/usr/bin/env python3
"""Execute the shared attribute predicate compiler over all eight states."""
import itertools
import re
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    image=(ROOT/'build/utilities/COPY.COM').read_bytes()
    listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    terms={'RO':(1,True),'RW':(1,False),'SYS':(2,True),'DIR':(2,False),
           'ARC':(4,True),'R/O':(1,True),'R/W':(1,False)}
    def expected(expression):
        def atom(text,state):
            neg=len(text)-len(text.lstrip('!'))
            key=text[neg+1:].upper()
            bit,positive=terms[key]
            value=bool(state&bit)==positive
            return not value if neg%2 else value
        return sum(1<<state for state in range(8)
                   if any(all(atom(x,state) for x in group.split('+'))
                          for group in expression.split(',')))
    def execute(text):
        c=Z80(b''); c.mem[256:256+len(image)]=image
        c.mem[0x7000:0x7000+len(text)]=text.encode()
        c.hl,c.b=0x7000,len(text)
        c.mem[addr('AT_RESULT')]=255
        c.run(addr('AT_PARSE'),limit=20000)
        return c
    atoms=['$'+k for k in terms]+['!$RO','!$SYS','!$ARC','!!$RO']
    expressions=atoms+[x.lower() for x in atoms]
    expressions += [a+op+b for a,b in itertools.product(atoms,repeat=2) for op in ('+',',')]
    expressions += [a+','+b+'+'+c for a,b,c in itertools.product(['$RO','!$SYS','$ARC'],repeat=3)]
    expressions += ['$RO+!$RO','$RO,!$RO','$ARC+!$SYS,$RO','!$RO+$SYS,!$ARC']
    for text in expressions:
        c=execute(text)
        assert not c.carry and c.a==expected(text),(text,c.a,expected(text))
        assert c.b==0 and c.hl==0x7000+len(text),text
        assert c.mem[addr('AT_RESULT')]==expected(text),text
    for text in ['', '$', '!', '!$', '$WHL', '$R', '$ARCC', '$RO+', '$RO,',
                 '+$RO', ',$RO', '$RO++$SYS', '$RO,,$SYS', '$RO!$SYS',
                 '$RO $SYS', '$RO\t', '($RO)', '$RO,$', '$R/O/', 'SIZE>3K']:
        c=execute(text)
        assert c.carry and c.a==0 and c.mem[addr('AT_RESULT')]==0,text
    print(f'Attribute predicate compiler: {len(expressions)} expressions x 8 states and malformed cases pass')


if __name__=='__main__': main()
