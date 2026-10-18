#!/usr/bin/env python3
"""Exercise transient TYPE page replay, row accounting and EOF navigation."""
from test_type_streaming import run
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=(1,3,b'A       TXT');B=(1,3,b'B       TXT')
PROMPT='MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.'

def main():
    lines=b''.join(f'ROW {i:02d}\r\n'.encode() for i in range(50))
    files={A:(lines+b'\x1a',0)}
    for forward in ('.',' ','\x03'):
        out,_=run('/P B3:A.TXT',files, responses=forward*2+'\x11')
        assert out.count(PROMPT)==3 and out.count('ROW 00')==1 and out.count('ROW 49')==1,out
    for back in (',','\x12'):
        out,_=run('B3:A.TXT /P',files,responses='.'+back+'\x11')
        assert out.count('ROW 00')==2 and out.count('ROW 23')==1 and 'ROW 49' not in out,out
    out,_=run('/P B3:A.TXT',files,responses=',\x1bX\x11')
    assert out.count(PROMPT)==1 and out.count('ROW 00')==1 and '\x07' in out,out
    # EOF remains navigable; Next at final EOF does not create another page.
    out,_=run('/P B3:A.TXT',{A:(b'LAST\r\n\x1a',0)},responses='. \x03\x11')
    assert out.count('LAST')==1 and out.count(PROMPT)==1 and out.count('\x07')==3,out
    out,_=run('/P B3:A.TXT',{A:(b'\x1a',0)})
    assert PROMPT not in out,out
    # Width spillover consumes rows even without any LF source bytes.
    out,_=run('/P B3:A.TXT',{A:(b'X'*1840+b'NEXT\x1a',0)},responses='.\x11')
    assert out.count(PROMPT)==2 and out.index(PROMPT)<out.index('NEXT'),out
    # Caret controls expand before row accounting; /CTL takes precedence over tabs.
    out,_=run('/P /CTL /T B3:A.TXT',{A:(b'\t'*920+b'NEXT\x1a',0)},responses='.\x11')
    assert out.count('^I')==920 and out.count(PROMPT)==2 and out.index(PROMPT)<out.index('NEXT'),out
    # Native clear/home and BDOS's cooked tab counter must agree.
    out,_=run('/P B3:A.TXT',{A:(b'\tA\tB\x1a',0)},responses='\x11',cooked_output=True)
    assert '\x1c\r        A       B' in out,out
    out,_=run('/P /7 B3:A.TXT',{A:(b'\x9a'*1840+b'NEXT\x1a',0)},responses='.\x11')
    assert out.count(PROMPT)==2 and out.index(PROMPT)<out.index('NEXT'),out
    # A cross-file page is continuous; banners consume real display rows.
    out,_=run('/P B3:*.TXT',{A:(b'A LINE\r\n',0),B:(b'B LINE\r\n',0)},responses='\x11')
    assert out.count(PROMPT)==1 and 'B3:A.TXT' in out and 'B3:B.TXT' in out,out
    # The current file is the page's first-byte anchor, not the last file shown.
    listing=(ROOT/'build/utilities/type.lst').read_text()
    anchor=int(re.search(r'^([0-9a-f]{4})\s+.*?\bTP_ANCH:',listing,re.M|re.I)[1],16)
    anchors=[]
    def observe(c, service):
        if service==6:anchors.append(bytes(c.mem[anchor:anchor+13]))
    run('/P B3:*.TXT',{A:(b'A LINE\r\n',0),B:(b'B LINE\r\n',0)},responses='\x11',observe=observe)
    assert anchors==[bytes((1,3))+b'A       TXT'],anchors
    anchors.clear()
    run('/P B3:*.TXT',{A:(b'A LINE\r\n'*20,0),B:(b'B LINE\r\n',0)},responses='.\x11',observe=observe)
    assert anchors==[bytes((1,3))+b'A       TXT',bytes((1,3))+b'B       TXT'],anchors
    # Reconstruct beyond a small cached history (there is no anchor cache).
    long={A:(b''.join(f'LONG {i:03d}\r\n'.encode() for i in range(230))+b'\x1a',0)}
    out,_=run('/P B3:A.TXT',long,responses='.'*9+','*9+'\x11')
    assert out.count('LONG 000')==2 and 'LONG 229' in out and out.count(PROMPT)==19,out
    # Full last page must not require a blank page before quitting.
    out,_=run('/P B3:A.TXT',{A:(b'LINE\r\n'*23+b'\x1a',0)},responses='.\x11')
    assert out.count(PROMPT)==1 and out.count('LINE')==23,out
    # A changed source may shrink below a replay target; clamp to the last page.
    from test_resident_type import execute
    changed={A:(b'OLD\r\n'*70+b'\x1a',0)}
    polls=[0]
    def shrink(c,service):
        if service==6:
            polls[0]+=1
            if polls[0]==4:changed[A]=(b'NEW\r\n'*10+b'\x1a',0)
    out,_=execute('/P B3:A.TXT',changed,responses='...\x12\x11',transient=True,observe=shrink)
    assert out.count('NEW')==10 and polls[0]==5,out
    out,calls=run('/P B3:A.TXT /BAD',{A:(b'DATA',0)})
    assert 'Invalid filespec.' in out and not any(f in calls for f in (15,17,20))
    print('PASS: TYPE bidirectional page replay, EOF, Ctrl-C next, Ctrl-Q quit, row wrapping, controls and history reconstruction')
if __name__=='__main__':main()
