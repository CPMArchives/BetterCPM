#!/usr/bin/env python3
"""Differential confirmation and exhaustive recovery-binding checks for ERA."""
import hashlib,json
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_utility_versions import address,runner,output
from utility_versions import banner
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/era-shared-input'


def invoke(image,listing,entry,keys,state=None):
    at=lambda n:address(listing,n)
    if state is not None and 'cpu' in state:c=state['cpu']
    else:
        c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
        if state is not None:state['cpu']=c
    c.bc=0xabcd;c.de=0x3456;c.hl=0x6789;c.ix=0xbeef
    pending=list(keys);text=bytearray();reads=[]
    def io(port):
        assert port&255==244
        if c.c==6:
            assert c.e==255 and pending,'unexpected read'
            value=pending.pop(0);reads.append(value)
        else:
            assert c.c==2,('unexpected service',c.c)
            text.append(c.e);value=0
        c.bc=0xeeee;c.de=0xdddd;c.hl=0xcccc;c.ix=0xbbbb
        return value
    c.port_read=io;sp=c.sp;c.run(at(entry),limit=200000)
    assert c.sp==sp
    de='newline' if c.de==at('E_NL') else c.de
    return (c.a,bool(c.carry),bool(c.z),c.bc,de,c.hl,c.ix,bytes(text),pending,reads)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for ix,de,z,expected,carry in [(0x1000,32,True,0x1020,False),(0xfff0,32,False,16,True),(0,0,True,0,False)]:
        probe=Z80(b'');probe.mem[256:259]=b'\xdd\x19\xc9';probe.ix=ix;probe.de=de;probe.z=z;probe.carry=not carry
        probe.run(256,limit=10)
        assert (probe.ix,probe.carry,probe.z)==(expected,carry,z)
    image=(ROOT/'build/utilities/ERA.COM').read_bytes();listing=(ROOT/'build/utilities/era.lst').read_text()
    # Retain the old routine independently of git history/shallow checkout.
    # Link to the unchanged real console helpers; candidate E_YN stays unpatched.
    origin=0x3000
    assert 256+len(image)<origin
    source='        ASEG\n        ORG 03000H\n'
    for name in ('E_KEY','E_CHAR','E_NEWLINE','E_NL'):
        source+=f'{name} EQU 0{address(listing,name):04X}H\n'
    source+=(ROOT/'tools/fixtures/era-legacy-yn.inc').read_text()+'\n        END\n'
    (OUT/'baseline-expanded.mac').write_text(source)
    raw=assemble(Path.home()/'bin/z80asm',source,OUT/'baseline.bin',OUT/'baseline.lst',origin)
    old_image=image+bytes(origin-256-len(image))+raw;old_listing=(OUT/'baseline.lst').read_text()
    for key in range(256):
        before=invoke(old_image,old_listing,'E_YN',bytes([key])+b'Y!')
        after=invoke(image,listing,'E_YN',bytes([key])+b'Y!')
        assert before==after,(key,before,after)
        # Recovery retains the exact retry policy, including ESC/Enter invalidity.
        result=invoke(image,listing,'EU_RCHO',bytes([key])+b'S!')
        folded=key-32 if ord('a')<=key<=ord('z') else key
        valid=folded in b'RSA?' or key==3
        expected=3 if key==3 else folded if valid else ord('S')
        assert result[0]==expected and result[3:7]==(0xabcd,0x3456,0x6789,0xbeef),(key,result)
        prompts=1 if valid or key==0 else 2
        assert result[7]==b'R/S/A/? '*prompts,(key,result)
        assert result[8]==([ord('S'),ord('!')] if valid else [ord('!')])
    state={}
    for entry,key,expected_text in [('EU_YN',b'Y',b''),('EU_RCHO',b'?',b'R/S/A/? '),('EU_YN',b'N',b'')]:
        result=invoke(image,listing,entry,key,state)
        assert result[0]==key[0] and result[7]==expected_text and result[8]==[]
        assert result[3:7]==(0xabcd,0x3456,0x6789,0xbeef)
    # Classification ends one-past-list; exact approval must name E_FIRST's hit.
    at=lambda n:address(listing,n)
    c=Z80(b'');c.mem[256:256+len(image)]=image;c.mem[5:8]=b'\xdb\xf4\xc9'
    heap=at('E_HEAP');c.mem[heap:heap+128]=bytes([26])*128
    for index,name in enumerate((b'FIRST   DAT',b'SECOND  DAT',b'THIRD   DAT')):
        entry=bytearray(32);entry[0]=1;entry[1]=3;entry[2:13]=name;entry[14]=1 if index==0 else 2
        c.mem[heap+index*32:heap+(index+1)*32]=entry
    c.setword(at('E_CURRENT'),heap+96);c.run(at('E_FIRST'),limit=10000)
    assert c.ix==heap+32 and c.word(at('E_CURRENT'))==heap+32
    shown=bytearray()
    def show(port):
        assert port&255==244 and c.c==2
        shown.append(c.e);return 0
    c.port_read=show;c.run(at('E_FULL'),limit=100000)
    assert shown==b'B3:SECOND.DAT',shown
    for name in ('EDITBUF','UE_INIT','UP_RUN','UT_TEXT'):
        assert name not in listing,name
    for tail in ['/VER',' /ver  ','/VER x','x /VER','/VER /VER','/VER /B']:
        c=runner(image);data=tail.encode();c.mem[128]=len(data);c.mem[129:129+len(data)]=data;c.run(256,limit=100000)
        assert output(c)==(banner('ERA')+'\r\n')
    report={'status':'PASS','confirmation_differential_cases':256,'recovery_cases':256,'context_transitions':3,'exact_prompt_target_cases':1,'version_cases':6,
            'bytes':len(image),'sha256':hashlib.sha256(image).hexdigest(),
            'scope':'Retained pre-migration E_YN linked to unchanged production console helpers; all byte inputs, retry/echo/cancel, no typeahead flush, register/stack preservation, no editor modules.'}
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n');print(report)


if __name__=='__main__':main()
