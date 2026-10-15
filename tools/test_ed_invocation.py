#!/usr/bin/env python3
"""ED front-end grammar and pure /VER: no file calls or DU mutations allowed."""
from pathlib import Path
from test_bios import Z80,SENTINEL
from test_vt52_foundation import symbols
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/ed-development'


def execute(tail,label='EI_PARSE'):
    image=(OUT/'EDDEV.COM').read_bytes();syms=symbols(OUT/'ed.lst')
    c=Z80(b'');c.mem[256:256+len(image)]=image
    c.mem[0:3]=bytes((0xc3,SENTINEL&255,SENTINEL>>8))
    c.mem[5:8]=bytes((0xdb,254,0xc9))
    data=tail.encode('ascii');c.mem[128]=len(data);c.mem[129:129+len(data)]=data
    calls=[];output=[]
    def io(port):
        calls.append(c.c)
        if c.c==25:return 2
        if c.c==32:
            assert c.e==255
            return 7
        if c.c==9:
            end=c.mem.index(36,c.de);output.append(bytes(c.mem[c.de:end]).decode())
            return 0
        raise AssertionError(('unexpected or mutating BDOS call',c.c))
    c.port_read=io;c.run(syms[label],limit=100000)
    assert bytes(c.mem[129:129+len(data)])==data
    return c,syms,calls,''.join(output)


def main():
    valid={'file.txt':(2,7,2,7),'B:FILE.TXT':(1,7,1,7),'B7:FILE.TXT':(1,7,1,7),'31:FILE.TXT':(2,31,2,31),'B3:FILE.TXT C7:':(1,3,2,7),'B:FILE.TXT 31:':(1,7,2,31),'A00:FILE.TXT P31:':(0,0,15,31),'B003:FILE.TXT 00:':(1,3,2,0),'FILE.TXT\tA:':(2,7,0,7),'NAME.':(2,7,2,7),'P31:ABCDEFGH.XYZ':(15,31,15,31)}
    for tail,want in valid.items():
        c,s,calls,_=execute(tail);assert not c.carry,(tail,'rejected')
        assert tuple(c.mem[s[label]] for label in ['EI_SDRV','EI_SUSR','EI_ODRV','EI_OUSR'])==want,tail
        assert calls==[25,32]
        assert c.mem[s['EI_FCB']]==want[0]+1
        if 'file.txt' in tail.lower():assert bytes(c.mem[s['EI_FCB']+1:s['EI_FCB']+12])==b'FILE    TXT'
    for drive in range(16):
        for user in range(32):
            c,s,_,_=execute(f'{chr(65+drive)}{user}:X.TXT {31-user}:')
            assert not c.carry and c.mem[s['EI_SUSR']]==user and c.mem[s['EI_OUSR']]==31-user
    invalid=['',':FILE.TXT','A:','32:X','B32:X','Q:X','-1:X','B[-]:X','[A0,B3]:X','X[$RO]','*.TXT','X?.TXT','TOOLONGNM.TXT','X.TOOLONG','X.T.X','X A: Y','X A:OTHER','X B[3]:','X 32:','X C','/Y X','A::X','999:X','X=Y','X/Y','X\\Y']
    for tail in invalid:
        c,_,calls,_=execute(tail);assert c.carry,(tail,'accepted');assert calls==[25,32]
    for tail in ['/VER',' /ver  ','/VER X','X /VER','/VER /VER']:
        _,_,calls,text=execute(tail,'ED_START')
        assert calls==[9]
        assert text==('BetterCP/M ED 1.0 (Build 001)\r\n' if tail.strip().upper()=='/VER' else 'Invalid /VER usage.\r\n')
    print('PASS: ED invocation, all 16 drives/32 users, output inheritance, invalid selectors/names and pure /VER; no disk access or DU mutation')


if __name__=='__main__':main()
