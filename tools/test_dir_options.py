#!/usr/bin/env python3
"""Execute DIR's complete command transaction before any BDOS operation."""
import re
from pathlib import Path
from test_bios import Z80

ROOT=Path(__file__).resolve().parents[1]

def main():
    image=(ROOT/'build/utilities/DIR.COM').read_bytes()
    listing=(ROOT/'build/utilities/dir-transient.lst').read_text()
    def addr(name):
        return int(re.search(r'^([0-9a-f]{4})\s+.*?\b'+name+':',listing,re.M|re.I)[1],16)
    c=Z80(b'');c.mem[256:256+len(image)]=image
    # A call to BDOS cannot return accidentally: parsing must stay pure.
    c.mem[5]=0x76
    valid=[('', 'N',0),('/S=N','N',0),('/S=N-','N',1),('/S=N+ /S=T-','T',1),
           ('A2:*.COM /S=Z-','Z',1),('/S=U A[1,3]:F?*.DAT','U',0),
           ('/s=t+ B3:FOO.DAT','T',0),(' /S=Z-  A0:*.TXT /S=N+ ','N',0),
           ('/S=U /S=Z+','Z',0),('A0:*.TXT[$R/O] /S=N','N',0),
           ('/S=N- /S=T+ /S=Z- /S=U','U',0),
           ('/A','N',0),('/a /A /S=T- A0:*.COM','T',1),
           ('A[0,2]:*.TXT[$SYS] /A','N',0),
           ('/C=1','N',0),('/c=2 /C=4','N',0),('/C=4 /A /C=1','N',0),
           ('/P','N',0),('/p /P /A /Z=S','N',0),('/P A[0,2]:*.TXT /S=T-','T',1),
           ('/Z','N',0),('/Z=K','N',0),('/z=s /A /S=Z- A0:*.DAT','Z',1),
           ('/Z=E','N',0),('/z=e /P /A /C=2','N',0),('/Z=S /Z=E','N',0),('/Z=E /Z','N',0),('/Z=S /Z=K','N',0),('/Z=S /Z','N',0),('/Z=K /Z=S','N',0),
           (' /S=N'*24+' A0:*.*','N',0)]
    invalid_options=['/C','/C=','/C=0','/C=3','/C=8','/C=2+','/C=01','/C:1','/C=3 /C=1','/S','/S=','/S=X','/S=U+','/S=U-','/S=N--',
                     '/P=ON','/PP','/P+','/Z=X','/Z=E+','/Z=EE','/Z=','/Z=S+','/Z=K-','/Z:S','/Z=X /Z=K','/A=RO','/AA','/A+','/A /S=X','/S=N?','/S=N /BOGUS','/S=X /S=N','/S==N','/S=T++','/S:N']
    invalid_files=['A0:F*A.COM /S=N','A0:*.COM B0:','/S=T A[32]:*.COM',
                   '/S=Z- A0:*.COM /S=N SECOND.DAT']
    def execute(text):
        data=text.encode();c.mem[0x6000:0x6000+len(data)]=data
        c.hl=0x6000;c.b=len(data);c.d,c.e=0,3
        c.run(addr('DP_PARSE'),limit=100000)
        assert bytes(c.mem[0x6000:0x6000+len(data)])==data,text
    for text,key,reverse in valid:
        execute(text)
        assert not c.carry,(text,c.pc)
        assert c.mem[addr('DN_MODE')]==ord(key) and c.mem[addr('DN_REV')]==reverse,text
        assert c.mem[addr('DT_SHOWATTR')]==int(any(token.upper()=='/A' for token in text.split())),text
        units=[token.upper().split('=')[-1] if '=' in token else 'K' for token in text.split() if token.upper()=='/Z' or token.upper().startswith('/Z=')]
        assert c.mem[addr('DT_UNIT')]==ord(units[-1] if units else 'K'),text
        assert c.mem[addr('DG_PAGE')]==int(any(token.upper()=='/P' for token in text.split())),text
        assert c.mem[addr('DG_LINES')]==0,text
        columns=[int(token[-1]) for token in text.upper().split() if token.startswith('/C=')]
        assert c.mem[addr('DC_REQUEST')]==(columns[-1] if columns else 0),text
        assert any(c.mem[addr('DU_MAP'):addr('DU_MAP')+64]),text
    for text in invalid_options+invalid_files:
        execute('/S=T- A0:*.COM[$RO]') # leave valid state for rejection to clear
        execute(text)
        assert c.carry,text
        assert c.mem[addr('DP_ERROR')]==int(text in invalid_options),text
        assert bytes(c.mem[addr('DU_MAP'):addr('DU_MAP')+64])==bytes(64),text
        assert bytes(c.mem[addr('FS_FCB'):addr('FS_FCB')+36])==bytes(36),text
        assert c.mem[addr('FS_MASK')]==0,text
    execute('/P /A /Z=S /S=N- A2:*.COM');execute('')
    assert c.mem[addr('DG_PAGE')]==0
    assert c.mem[addr('DT_UNIT')]==ord('K')
    assert c.mem[addr('DT_SHOWATTR')]==0
    assert not c.carry and c.mem[addr('DN_MODE')]==ord('N') and c.mem[addr('DN_REV')]==0
    assert bytes(c.mem[addr('DU_MAP'):addr('DU_MAP')+64])==b'\x08'+bytes(63)
    assert bytes(c.mem[addr('FS_FCB')+1:addr('FS_FCB')+12])==b'?'*11
    print(f'DIR sort options: {len(valid)} valid and {len(invalid_options+invalid_files)} invalid forms; reset and failure atomicity pass')

if __name__=='__main__':main()
