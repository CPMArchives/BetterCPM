#!/usr/bin/env python3
"""Setup ordering and DU isolation with a simulated BDOS directory."""
from test_ed_buffer import context


def setup(files,source=(1,7),dest=(2,3),attrs=0,fail_make=None):
    c,s,call,_,_=context();live=set(files);ops=[];drive=0;user=0
    name=b'CASE    TXT'
    c.mem[s['EI_FCB']:s['EI_FCB']+36]=b'\x00'+name+b'\x00'*24
    for symbol,value in [('EI_SDRV',source[0]),('EI_SUSR',source[1]),
                         ('EI_ODRV',dest[0]),('EI_OUSR',dest[1])]:c.mem[s[symbol]]=value
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    def io(port):
        nonlocal drive,user
        if c.c==14:drive=c.e;return 0
        if c.c==32:user=c.e;return 0
        if c.c==26:assert c.de==s['ES_DATA'];return 0
        assert c.c in (15,17,19,22),c.c
        fcb=c.de;selected=c.mem[fcb]-1 if c.mem[fcb] else drive
        assert selected==drive
        key=(drive,user,bytes(c.mem[fcb+1:fcb+12]));ops.append((c.c,key))
        if c.c==19:
            if key not in live:return 255
            live.remove(key);return 0
        if c.c==22:
            if key==fail_make:return 255
            live.add(key);return 0
        if key not in live:return 255
        if c.c==15:
            c.mem[fcb+9]|=128 if attrs&1 else 0
            c.mem[fcb+10]|=128 if attrs&2 else 0
        return 0
    c.port_read=io
    return c,s,call,live,ops


def main():
    src=(1,7,b'CASE    TXT');dst=(2,3,b'CASE    TXT')
    sbak=(1,7,b'CASE    BAK');dbak=(2,3,b'CASE    BAK');temp=(2,3,b'CASE    $$$')
    for exists in (False,True):
        c,s,call,live,ops=setup(({src} if exists else set())|{sbak,dbak,temp})
        assert call('FS_SETUP')==(False,0)
        assert live=={src,temp} and c.mem[s['FS_NEW']]==int(not exists)
        expected=[(17,dst),(15,src)]+([] if exists else [(22,src)])+[(19,sbak),(19,dbak),(19,temp),(22,temp)]
        assert ops==expected,(ops,expected)
        assert c.word(s['ES_FCB'])==s['FS_SOURCE'] and c.word(s['EW_FCB'])==s['FS_WORK']
        assert c.mem[s['ES_USER']]==7 and c.mem[s['EW_USER']]==3
    c,s,call,live,ops=setup({src,dst,sbak,dbak,temp})
    assert call('FS_SETUP')==(True,1) and ops==[(17,dst)] and len(live)==5
    c,s,call,live,ops=setup({src,sbak},attrs=2)
    assert call('FS_SETUP')==(True,2) and live=={src,sbak}
    c,s,call,live,ops=setup({src},attrs=3)
    assert call('FS_SETUP')==(False,0) and c.mem[s['FS_RO']]==128
    c,s,call,live,ops=setup(set(),fail_make=src)
    assert call('FS_SETUP')==(True,3) and not live
    c,s,call,live,ops=setup({src},fail_make=temp)
    assert call('FS_SETUP')==(True,3) and live=={src}
    # Same drive, different user must still receive collision protection.
    c,s,call,live,ops=setup({src,(1,3,b'CASE    TXT')},dest=(1,3))
    assert call('FS_SETUP')==(True,1) and len(ops)==1
    c,s,call,live,ops=setup({src,sbak},dest=(1,7))
    assert call('FS_SETUP')==(False,0)
    assert [n for n,_ in ops]==[15,19,19,22] and live=={src,(1,7,b'CASE    $$$')}
    print('PASS: file setup order, new/existing source, DU collision safety, attributes and create failures')


if __name__=='__main__':main()
