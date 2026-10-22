#!/usr/bin/env python3
"""Verify SYSGEN's choice-only binding preserves its one-key safety policy."""
import hashlib,json
from pathlib import Path
from test_bios import Z80
from test_utility_versions import address,runner,output
from utility_versions import banner
ROOT=Path(__file__).resolve().parents[1]


def main():
    image=(ROOT/'build/utilities/SYSGEN.COM').read_bytes()
    listing=(ROOT/'build/utilities/sysgen.lst').read_text();at=lambda n:address(listing,n)
    cases=0
    for key in range(1,256):
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
        keys=[key,ord('!')];calls=[]
        def io(port):
            assert port&255==244 and c.c==6 and c.e==255
            calls.append(c.c);value=keys.pop(0)
            c.bc=0xbcbc;c.de=0xdede;c.hl=0xeeee
            return value
        c.port_read=io;sp=c.sp
        c.run(at('SG_ASK'),limit=100000)
        assert c.sp==sp and len(calls)==1 and keys==[ord('!')]
        expected=ord('Y') if key in (ord('Y'),ord('y')) else ord('N') if key in (ord('N'),ord('n')) else 0
        assert c.a==expected,(key,c.a,expected)
        assert c.mem[at('UC_DEF')]==0 and c.mem[at('UC_COUNT')]==2
        cases+=1
    # No edit buffer, word module or standard field controller is linked.
    for name in ('EDITBUF','UE_INIT','UP_RUN','UT_TEXT'):
        assert name not in listing,name
    # Corrupt prompt configuration must fail closed without reading a key.
    for field,value in [('UC_COUNT',0),('UC_LIST',0),('UC_DEF',ord('X'))]:
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
        if field=='UC_LIST':c.setword(at(field),value)
        else:c.mem[at(field)]=value
        def no_io(port):raise AssertionError('bad configuration read input')
        c.port_read=no_io;sp=c.sp;c.run(at('SG_ASK'),limit=100000)
        assert c.a==0 and c.sp==sp
    tails=['/VER',' /ver  ','/VER x','x /VER','/VER /VER','/VER /B']
    for tail in tails:
        c=runner(image);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data
        c.run(256,limit=100000)
        expected=banner('SYSGEN')+'\r\n' if tail.strip().upper()=='/VER' else 'Invalid /VER usage.\r\n'
        assert output(c)==expected,(tail,output(c))
    report={'status':'PASS','cases':cases,'program_bytes':len(image),
            'version_cases':len(tails),
            'bad_configuration_cases':3,
            'sha256':hashlib.sha256(image).hexdigest(),
            'scope':'All nonzero key bytes; only Y authorizes, any other key declines; one key consumed, no typeahead flush, hostile BDOS registers, no editor modules.'}
    (ROOT/'build/utilities/sysgen-shared-choice.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
