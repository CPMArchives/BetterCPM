#!/usr/bin/env python3
"""Execute destination lists and override application without media."""
import itertools
import re
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    image=(ROOT/'build/utilities/COPY.COM').read_bytes()
    listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
    def addr(name):return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    def cpu():
        c=Z80(b'');c.mem[256:256+len(image)]=image;return c
    terms={'$RO':(1,1),'$RW':(1,0),'$SYS':(2,1),'$DIR':(2,0),'$ARC':(4,1),
           '!$RO':(1,0),'!$SYS':(2,0),'!$ARC':(4,0),'$R/O':(1,1),'$R/W':(1,0)}
    for a,b in itertools.product(terms,repeat=2):
        text=a+','+b;c=cpu();c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl,c.b=0x7000,len(text)
        c.run(addr('AT_STATE'),limit=20000)
        bit1,value1=terms[a];bit2,value2=terms[b]
        conflict=bit1==bit2 and value1!=value2
        assert c.carry==conflict,text
        if conflict:
            assert c.mem[addr('AT_SET')]==c.mem[addr('AT_CLEAR')]==0
        else:
            assert c.mem[addr('AT_SET')]==((bit1 if value1 else 0)|(bit2 if value2 else 0)),text
            assert c.mem[addr('AT_CLEAR')]==((bit1 if not value1 else 0)|(bit2 if not value2 else 0)),text
    for text in ['', '$RO+', '$RO+$SYS','$RO,,!$SYS','$WHL','$ARC,!$ARC','$SYS,$DIR','$RO,$R/W']:
        c=cpu();c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl,c.b=0x7000,len(text)
        c.run(addr('AT_STATE'),limit=20000);assert c.carry,text
    for text,accepted in [('D3:[$RW,!$ARC]',True),('F.DAT[$ARC]',True),
                          ('D3:',True),('[$RO]',False),('D3:[]',False),
                          ('D3:[$RO,$RW]',False),('D3:[$RO]+',False)]:
        c=cpu();c.mem[addr('BC_COPAR'):addr('BC_COPAR')+2]=b'\x37\xc9'
        c.mem[0x7000:0x7000+len(text)]=text.encode();c.hl,c.b=0x7000,len(text)
        c.run(addr('CTDSCOPE'),limit=20000)
        assert c.carry==accepted,text
    for initial in range(8):
        for choices in itertools.product((None,False,True),repeat=3):
            setmask=sum(1<<i for i,x in enumerate(choices) if x is True)
            clear=sum(1<<i for i,x in enumerate(choices) if x is False)
            c=cpu();fcb=addr('BC_NEWFCB')
            name=bytearray(b'ABCDEF'+bytes([ord('G')|128])+b'HCOM')
            for i in range(3):name[8+i]|=128 if initial&(1<<i) else 0
            c.mem[fcb+1:fcb+12]=name
            c.mem[addr('CTD_SET')]=setmask;c.mem[addr('CTD_CLR')]=clear
            c.run(addr('CTDATTR'),limit=10000)
            expected=(initial & ~clear)|setmask
            actual=c.mem[fcb+1:fcb+12]
            assert actual[:8]==name[:8]
            assert bytes(x&127 for x in actual)==bytes(x&127 for x in name)
            assert sum(1<<i for i in range(3) if actual[8+i]&128)==expected
    print('Destination attribute contradictions, aliases and all override states pass')


if __name__=='__main__':main()
