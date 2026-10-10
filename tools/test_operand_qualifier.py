#!/usr/bin/env python3
"""Execute shared DU parsing followed by operand-qualifier splitting."""
import re
from test_bios import Z80
from test_disk_utilities import ROOT


def main():
    image=(ROOT/'build/utilities/COPY.COM').read_bytes()
    listing=(ROOT/'build/utilities/copy-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    def execute(text,du=False):
        c=Z80(b''); c.mem[256:256+len(image)]=image
        c.mem[0x7000:0x7000+len(text)]=text.encode()
        c.hl,c.b=0x7000,len(text)
        if du:
            c.d,c.e=2,5
            c.run(addr('DU_PARSE'),limit=50000)
            assert not c.carry,text
        bitmap=bytes(c.mem[addr('DU_MAP'):addr('DU_MAP')+64])
        original=c.hl
        c.run(addr('OQ_SPLIT'),limit=10000)
        assert c.hl==original,text
        error=c.word(addr('OQ_ERRPTR'))
        assert (original<=error<=0x7000+len(text)) if c.carry else error==0,text
        assert bytes(c.mem[addr('DU_MAP'):addr('DU_MAP')+64])==bitmap,text
        ptr,length=c.word(addr('OQ_PTR')),c.mem[addr('OQ_LEN')]
        return c,bytes(c.mem[c.hl:c.hl+c.b]).decode(),bytes(c.mem[ptr:ptr+length]).decode()
    for text,body,qualifier in [
        ('*.COM','*.COM',''), ('','',''),
        ('FOO.COM[$RO]','FOO.COM','$RO'),
        ('[$RW,!$ARC]','','$RW,!$ARC'),
        ('F?*.DOC[$ARC+!$SYS]','F?*.DOC','$ARC+!$SYS'),
        ('F***.COM[$R/O,$R/W]','F***.COM','$R/O,$R/W')]:
        c,actual,q=execute(text)
        assert not c.carry and (actual,q)==(body,qualifier),text
    for selector,body,qualifier in [
        ('B[-]:*.DOC[$ARC]','*.DOC','$ARC'),
        ('[A0,C[3,5,7-11],5]:F?*.DAT[!$SYS]','F?*.DAT','!$SYS'),
        ('D0:[$RW,!$ARC]','','$RW,!$ARC'),
        ('B[3-5]:*.COM','*.COM','')]:
        c,actual,q=execute(selector,True)
        assert not c.carry and (actual,q)==(body,qualifier),selector
        bitmap=bytes(c.mem[addr('DU_MAP'):addr('DU_MAP')+64])
        assert any(bitmap),selector
    for text in ['F.COM[]','F.COM[','F.COM[$RO','F.COM]','F.COM[$RO]X',
                 'F.COM[$RO][$SYS]','F.COM[[$RO]]','F.COM[$RO ]',
                 'F.COM[ $RO]','F.COM[$RO\t]','F.COM[$RO\x7f]']:
        c,_,_=execute(text)
        assert c.carry and c.word(addr('OQ_PTR'))==0 and c.mem[addr('OQ_LEN')]==0,text
    # Every truncation after the opening bracket is rejected until its terminal ].
    value='F.COM[$ARC+!$SYS]'
    for end in range(value.index('[')+1,len(value)):
        c,_,_=execute(value[:end]); assert c.carry,value[:end]
        assert c.word(addr('OQ_ERRPTR'))==0x7000+end,value[:end]
    for text,position in [('F[]',2),('F]',1),('F[[$RO]]',2),
                          ('F[$RO]X',6),('F[$RO ]',5),('F[$RO][$SYS]',6)]:
        c,_,_=execute(text)
        assert c.carry and c.word(addr('OQ_ERRPTR'))==0x7000+position,text
    # A failed call must not leave a stale diagnostic after a successful call.
    c.hl,c.b=0x7000,1
    c.run(addr('OQ_SPLIT'),limit=10000)
    assert not c.carry and c.word(addr('OQ_ERRPTR'))==0
    # Maximum command-tail length cannot overrun the next byte.
    c,body,q=execute('F['+'X'*123+']')
    assert not c.carry and body=='F' and q=='X'*123
    assert c.mem[0x7000+126]==0
    print('Operand qualifier splitting, DU bracket separation and malformed/truncated cases pass')


if __name__=='__main__': main()
