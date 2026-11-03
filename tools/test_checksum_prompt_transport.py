#!/usr/bin/env python3
"""Compare checksum prompt transport with the retained decision loop.

Executes actual compiled prompt routines, preserving public BDOS clobbers;
complete file transactions are covered separately by test_crc/test_md5sum.
"""
import hashlib,json,re
from pathlib import Path
from build_crc import expanded_source as crc_source
from build_md5sum import expanded_source as md5_source
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/checksum-prompt-transport'


def invoke(image,listing,keys):
    at=lambda n:address(listing,n)
    c=Z80(b'');c.mem[256:256+len(image)]=image
    c.mem[5:8]=b'\xdb\xf4\xc9'
    c.ix=0x9000;c.mem[0x9000:0x9080]=bytes(128)
    c.mem[0x9001:0x900c]=b'CHECK   LST'
    c.mem[0x906c:0x906e]=bytes([2,7])
    for n in ('CANCEL','INCOMPLE','ALLYES'):c.mem[at(n)]=0
    c.mem[at('WRESPONS')]=ord('!')
    pending=list(keys);text=bytearray();reads=[];depth=0;top=c.sp
    push=c.push
    def tracked(v):
        nonlocal depth
        push(v);depth=max(depth,top-c.sp)
    c.push=tracked
    def io(port):
        assert port&255==244
        if c.c==1 or (c.c==6 and c.e==255):
            assert pending,'prompt exhausted input'
            value=pending.pop(0);reads.append(value)
            # Model cooked echo, including controls, identically in both runs.
            if c.c==1:text.append(value)
        elif c.c in (2,6):text.append(c.e);value=0
        else:raise AssertionError(('unexpected BDOS',c.c))
        c.bc=0xbcbc;c.de=0xdede;c.hl=0xeeee;c.ix=0xaaaa
        return value
    c.port_read=io;c.run(at('WPROMPT'),limit=300000)
    assert c.sp==top and c.ix==0x9000
    flags=tuple(c.mem[at(n)] for n in ('CANCEL','INCOMPLE','ALLYES','WRESPONS'))
    return (bytes(text),pending,reads,flags),depth


def main():
    OUT.mkdir(parents=True,exist_ok=True);report={}
    legacy=(ROOT/'tools/fixtures/checksum-legacy-choice.inc').read_text()+'\nWC_PUT: JP BDOS\nWC_ACTIVE: DB 0\n'
    for name,source,stem in [('CRCKSUM',crc_source(),'crc'),('MD5SUM',md5_source(),'md5sum')]:
        text=source.replace('        CSEG\n','        ASEG\n').replace('        .PHASE 0103H\n','        ORG 0103H\n').replace('        .DEPHASE\n','')
        a=text.index('WPKEY:');b=text.index('; Find a fresh temporary/backup pair',a)
        text=text[:a]+legacy+text[b:]
        before=b'\xc3\x03\x01'+assemble(Path.home()/'bin/z80asm',text,OUT/(stem+'-legacy.bin'),OUT/(stem+'-legacy.lst'),0x103)
        oldls=(OUT/(stem+'-legacy.lst')).read_text()
        image=(ROOT/f'build/utilities/{name}.COM').read_bytes()
        listing=(ROOT/f'build/utilities/{stem}.lst').read_text()
        cases=[bytes([k])+b'N!' for k in range(256)]
        cases += [b'??xN!',b'\x1b\x1bN!',b'??\r!',b'??A!',b'??\x03!',b'xyzY!']
        maximum=0
        for keys in cases:
            expected,_=invoke(before,oldls,keys);actual,used=invoke(image,listing,keys)
            assert actual[1:]==expected[1:],(name,keys,expected,actual)
            # Direct input deliberately omits echo of unassigned controls.
            # For ordinary ASCII and CR/LF/BS, complete display remains identical.
            if all(32<=k<127 or k in (8,10,13) for k in actual[2]):
                assert actual[0]==expected[0],(name,keys,expected,actual)
            maximum=max(maximum,used)
        for label in ('UC_RUN','EDITNEW','UE_INIT','UP_RUN','UR_DRAW','UA_INIT'):
            assert not re.search(r'\b'+label+':',listing),label
        report[name]={'status':'PASS','cases':len(cases),'bytes':len(image),'sha256':hashlib.sha256(image).hexdigest(),'maximum_prompt_stack_bytes':maximum}
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
