#!/usr/bin/env python3
"""CONFIG help queries are pure, bounded, quote-aware and screen-sized."""
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address
from build_config import validate_layout

ROOT=Path(__file__).resolve().parents[1]

def main():
    image=(ROOT/'build/utilities/CONFIG.COM').read_bytes()
    listing=(ROOT/'build/utilities/config.lst').read_text()
    validate_layout(image,listing)
    def execute(tail,stop_init=False):
        c=Z80(b'');c.mem[256:256+len(image)]=image
        c.mem[:3]=bytes.fromhex('c3ffff');c.mem[5:8]=bytes((0xdb,254,0xc9))
        data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        if stop_init:
            at=address(listing,'INIT');c.mem[at:at+3]=bytes.fromhex('c3ffff')
        output=[];calls=[]
        def io(port):
            calls.append(c.c)
            if c.c==9:
                output.extend(c.mem[c.de:c.mem.index(36,c.de)])
            elif c.c==2:output.append(c.e)
            else:raise AssertionError(('unexpected disk/settings operation',c.c,tail))
            return 0
        c.port_read=io;c.run(256,limit=200000)
        assert bytes(c.mem[129:129+len(data)])==data,tail
        return bytes(output).decode(),calls
    expected,_=execute('/HELP')
    assert 'BetterCP/M Utilities' in expected and 'Usage: CONFIG' in expected,expected
    assert len(expected.splitlines())<=23 and max(map(len,expected.splitlines()))<=80,expected
    for option in ('/SHOW','/STARTUP=','/DEFAULT','/IOBYTE=','/PHYSICAL=',
                   '/LOGICAL=','/FORMAT=','/UNBIND','/EDIT=','/SLOT','/ID','/CODE','/H /HELP','/VER'):
        assert option in expected,(option,expected)
    for tail in ('/H',' /h ','\t/HeLp\t','/VER /HELP /BOGUS','/H /VER',
                 '/BOGUS /H','/HELP /VER',' '*125+'/H',
                 '/STARTUP="literal /H /HELP" /HELP'):
        output,calls=execute(tail)
        assert output==expected and calls==[9],(tail,output,calls)
    for tail in ('/HH','/HELPER','/HELP=YES','X/HELP','/HEL','/HXYZ'):
        output,calls=execute(tail)
        assert output=='Invalid CONFIG usage.\r\n',(tail,output)
        assert all(call==2 for call in calls),(tail,calls)
    for tail in ('/STARTUP="Mixed /H /HELP /VER"',
                 '/LOGICAL=B /PHYSICAL=1 /FORMAT="NAME /HELP"'):
        output,calls=execute(tail,stop_init=True)
        assert not output and not calls,(tail,output,calls)
    # The builder rejects real main-code/stack overlap, not the help appendix.
    bad=listing.replace('CF_MAIN_END:', 'CF_MAIN_OLD:')+'\n3e01  CF_MAIN_END:\n'
    try:validate_layout(image,bad)
    except ValueError:pass
    else:raise AssertionError('stack overlap was accepted')
    print('PASS: CONFIG help/alias precedence, quoted data, no-I/O queries, layout and stack boundary')

if __name__=='__main__':main()
