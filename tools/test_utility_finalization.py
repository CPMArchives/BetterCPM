#!/usr/bin/env python3
"""Execute finalized utility query and manager parsing paths on actual COM bytes."""
from pathlib import Path
from test_bios import Z80

ROOT = Path(__file__).resolve().parents[1]

def execute(name, tail, queries=True):
    image=(ROOT/'build/utilities'/(name+'.COM')).read_bytes()
    c=Z80(b'');c.mem[256:256+len(image)]=image
    c.mem[5:8]=b'\xd3\x00\xc9';c.mem[0:3]=b'\xc3\xfe\xff'
    data=tail.encode();assert len(data)<=127
    c.mem[128]=len(data);c.mem[129:129+len(data)]=data
    # CPX consumes the CCP-prepared second default FCB for module names.
    if name=='CPX' and tail.strip().upper().startswith(('LOAD','UNLOAD')):
        c.mem[0x6c:0x79]=bytes([0])+b'HELLO   '+b'   '+bytes([0])
    original=bytes(c.mem[128:256]);output=bytearray();requests=[]
    def service(port,value):
        if c.c==9:
            end=c.mem.index(36,c.de);output.extend(c.mem[c.de:end])
            if queries:c.bc=0xa5a5;c.de=0x5a5a;c.hl=0x1234
        elif c.c==6 and queries and c.e!=255:output.append(c.e)
        elif c.c==0 and not queries:c.pc=0xffff
        elif c.c==2:output.append(c.e)
        elif c.c in (176,177) and not queries:
            requests.append(bytes(c.mem[c.de:c.de+18]));c.a=0
        else:raise AssertionError((name,tail,'Unexpected BDOS service',c.c))
    c.port_write=service;c.run(256,limit=2000000)
    assert bytes(c.mem[128:256])==original,(name,'command tail changed')
    return output.decode('ascii'),requests

def main():
    names=['STAT','CPX','RSX','DIR','USER','CLS','VER','COPY','MOVE','ERA','REN','TYPE','TIME',
           'DUP','SYSGEN','ED','SUBMIT','XSUB','PIP','DLINK','DUMP','DASM','DSYM','TED',
           'ADMTST','VT52TST','ANSITST','SYSBUILD','RESPACK','RLMBUILD','WARM',
           'DDT','COMPARE','CRCKSUM','MD5SUM','PATCH','SEARCH']
    count=0;version_count=0
    for name in names:
        expected,_=execute(name,'/HELP')
        from utility_versions import identities
        version,revision=identities()[name]
        assert f'{name} {version} ({revision:03d}' in expected,(name,'wrong identity',expected)
        assert 'Usage:' in expected and '/H /HELP' in expected,(name,expected)
        assert len(expected.splitlines())<=23 and max(map(len,expected.splitlines()))<=79,(name,'help exceeds screen')
        from test_utility_versions import expected_identification
        version_expected=expected_identification(name)
        for tail in ['/VER',' /ver  ','ignored /VER /BOGUS','/VER /VER','\t/VER\t','X'*122+' /VER']:
            actual,_=execute(name,tail)
            assert actual==version_expected,(name,tail,actual,version_expected)
            version_count+=1
        for tail in ['/h',' /H  ','/ver /h /BOGUS','/VER /HELP','\t/h\t','/h /help','/h'+' '*125,'X'*124+' /h']:
            actual,_=execute(name,tail);assert actual==expected,(name,tail,actual);count+=1
    for name in ('CPX','RSX'):
        canonical,req=execute(name,'LIST',False);assert req and 'TPA available:' in canonical
        for tail in ('list','List ',' LIST  ','\tlist\t'):
            actual,requests=execute(name,tail,False);assert actual==canonical and requests==req,(name,tail);count+=1
        for tail in ('/BOGUS','LISTX','LIST BAD','LOAD','UNLOAD',''):
            actual,requests=execute(name,tail,False);assert not requests and 'Invalid usage.' in actual and execute(name,'/HELP')[0] in actual;count+=1
        for operation in ('LOAD','UNLOAD'):
            _,expected=execute(name,operation+' HELLO',False)
            assert expected,(name,operation)
            for tail in (operation.lower()+' hello',operation+'\thello  '):
                _,actual=execute(name,tail,False);assert actual==expected,(name,tail);count+=1
    print(f'PASS: {len(names)} help screens, {count} alias/precedence and manager parser checks; {version_count} version queries; command tails preserved')

if __name__=='__main__':main()
