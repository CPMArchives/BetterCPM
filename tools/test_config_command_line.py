#!/usr/bin/env python3
"""CONFIG full-tail validation, quoted startup strings and pure identity."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
from utility_versions import banner
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    def setup(tail):
        c=Z80(b'');c.mem[256:256+len(image)]=image
        c.mem[:3]=bytes.fromhex('c3ffff');c.mem[5:8]=bytes((0xdb,254,0xc9))
        data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        return c,data
    valid={'':(0,''),'  ':(0,''),' /SHOW ':(1,''),'\t/show\t':(1,''),
           '/STARTUP="SUBMIT STARTUP"':(2,'SUBMIT STARTUP'),
           '/startup="Mixed Case /VER /B"':(2,'Mixed Case /VER /B'),
           '/STARTUP=""':(2,''),'/STARTUP="spaces  retained"  ':(2,'spaces  retained'),
           '/STARTUP="'+'x'*116+'"':(2,'x'*116)}
    for tail,(mode,text) in valid.items():
        c,data=setup(tail);c.port_read=lambda p: (_ for _ in ()).throw(AssertionError('unexpected BDOS'))
        c.run(address(listing,'CF_PARSE'),limit=100000)
        assert not c.carry,(tail,c.a)
        assert c.mem[address(listing,'CF_MODE')]==mode
        if mode==2:
            size=c.mem[address(listing,'CF_LEN')];start=address(listing,'CF_TEXT')
            assert bytes(c.mem[start:start+size])==text.encode()
        assert bytes(c.mem[129:129+len(data)])==data
    for tail in ['/SHOW X','/SHO','/SHOW/VER','X','/STARTUP=X','/STARTUP="X','/STARTUP="X" /SHOW','/STARTUP="X"Y','/STARTUP="a\tb"','/STARTUP="X" /VER','x'*128]:
        c,_=setup(tail);c.run(address(listing,'CF_PARSE'),limit=100000);assert c.carry,tail
    for tail in ['/VER',' /ver ','/SHOW /VER','/STARTUP="X" /VER','/STARTUP="Mixed /VER /B"','/SHOW X']:
        c,_=setup(tail);calls=[];out=[]
        # Reaching INIT is enough: the prefix must not intercept quoted /VER.
        start=address(listing,'INIT');c.mem[start:start+3]=bytes.fromhex('c3ffff')
        def io(port):
            calls.append(c.c)
            if c.c==9:
                end=c.mem.index(36,c.de);out.extend(c.mem[c.de:end]);return 0
            assert c.c==2,('unexpected mutation',c.c)
            out.append(c.e);return 0
        c.port_read=io;c.run(256,limit=100000)
        if tail.strip().upper()=='/VER':assert calls==[9] and bytes(out)==(banner('CONFIG')+'\r\n').encode()
        elif tail.startswith('/STARTUP="Mixed'):assert calls==[] and not out
        elif tail=='/SHOW X':assert bytes(out)==b'Invalid CONFIG usage.\r\n'
        else:assert calls==[9] and bytes(out)==(banner('CONFIG')+'\r\n').encode()
    def zstring(label):
        start=address(listing,label);end=image.index(0,start-256)
        return image[start-256:end]
    assert zstring('TITLE')==banner('CONFIG').encode()
    menu=zstring('MAINMSG')
    assert all(f'[ {x} ]'.encode() not in menu for x in 'FGHIJK')
    assert all(f'[ {x} ]'.encode() in menu for x in 'ABCDES')
    # Exercise the actual dispatch without entering any setting or save code.
    targets={'A':'STARTMENU','B':'IO_MENU','C':'PHYSMENU','D':'LOGMENU',
             'E':'EDITDRIVE','S':'SAVEMENU',chr(3):'DONE'}
    for key,target in targets.items():
        c,_=setup('')
        reached=[]
        for label in ('HEADER','PUTS'):
            c.mem[address(listing,label)]=0xC9
        choice=address(listing,'CHOICE')
        c.mem[choice:choice+3]=bytes((0x3E,ord(key),0xC9))
        for label in targets.values():
            at=address(listing,label)
            c.mem[at:at+5]=bytes((0x3E,list(targets.values()).index(label),0xD3,253,0xC9))
        c.port_write=lambda port,value: reached.append(value)
        c.run(address(listing,'MAIN'),limit=10000)
        assert reached==[list(targets.values()).index(target)],(key,target,reached)
    print('PASS: CONFIG menu/identity, full-tail parser, quoted startup text, invalid requests and pure /VER')


if __name__=='__main__':main()
