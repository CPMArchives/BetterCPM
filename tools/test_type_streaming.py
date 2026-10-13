#!/usr/bin/env python3
"""Execute transient TYPE streaming and display transforms with a BDOS fixture."""
from test_resident_type import execute

def run(tail, files, **kwargs):
    before=files.copy()
    result=execute(tail, files, transient=True, **kwargs)
    assert files==before
    return result

def main():
    a=(1,3,b'A       TXT');b=(1,3,b'B       TXT');d=(2,5,b'D       TXT')
    fixtures={b:(b'BETA\x1aHIDDEN',2),a:(b'ALPHA $\r\n',1),d:(b'DELTA\r\n',4)}
    out,_=run('[B3,C5]:*.TXT',fixtures)
    assert out.index('B3:A.TXT')<out.index('B3:B.TXT')<out.index('C5:D.TXT'),out
    assert all(text in out for text in ('ALPHA $','BETA','DELTA')) and 'HIDDEN' not in out
    out,_=run('[B3,C5]:*.TXT[$ARC]',fixtures)
    assert 'DELTA' in out and 'ALPHA' not in out and 'BETA' not in out
    out,_=run('B3:A.TXT',fixtures);assert out=='ALPHA $\r\n',out
    for tail in ('', 'B3:F*A.TXT', '[B3,E0]:*.TXT', 'B3:A.TXT OTHER.TXT', '/P B3:A.TXT', 'B3:A.TXT /7x'):
        out,calls=run(tail,fixtures)
        assert not any(f in calls for f in (15,17,20)),(tail,out)
    out,calls=run('/ver',{})
    assert 'BetterCP/M TYPE 1.0 (Build 001)' in out and not any(f in calls for f in (15,17,20,25,32))
    out,_=run('B3:*.TXT',fixtures,open_fail=(a,))
    assert 'TYPE B3:A.TXT - Cannot open.' in out and 'BETA' in out,out
    out,_=run('B3:*.TXT',fixtures,read_fail=(a,))
    assert 'TYPE B3:A.TXT - Read error.' in out and 'BETA' in out,out
    for tail in ('/7 /CTL B3:A.TXT','B3:A.TXT /ctl /7 /7'):
        out,_=run(tail,{a:(b'\x9aAFTER\x1aHIDDEN',0)})
        assert out=='^ZAFTER',out
    out,_=run('B3:A.TXT /7',{a:(b'\x9aAFTER\x1aHIDDEN',0)})
    assert out=='\x1aAFTER',out
    out,_=run('/T B3:A.TXT',{a:(b'A\tB\r\n\tC\x1a',0)})
    assert out=='A       B\r\n        C',repr(out)
    out,_=run('/CTL /T B3:A.TXT',{a:(b'A\tB\r\nC\rD\nE\x1a',0)})
    assert out=='A^IB^M^J\r\nC^M\r\nD^J\r\nE',repr(out)
    for data,wanted in [(b'A\r', 'A^M\r\n'),(b'\x00\x08\x0c\x1b\x7f','^@^H^L^[^?'),(b'X'*127+b'\r\nY','X'*127+'^M^J\r\nY')]:
        out,_=run('/CTL B3:A.TXT',{a:(data+b'\x1a',0)});assert out==wanted,repr(out)
    out,_=run('B3:*.TXT',{a:(b'',0),b:(b'BETA',0)})
    assert 'B3:A.TXT' in out and 'B3:B.TXT' in out and '[EMPTY]' not in out
    out,_=run('B3:A.TXT',{a:(b'X'*17000+b'\x1a',0)})
    assert out=='X'*17000,'duplicate extent output'
    print('PASS: transient TYPE shared selection, banners, EOF, transforms, record boundaries, errors, version and immutability')
if __name__=='__main__':main()
