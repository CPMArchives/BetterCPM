#!/usr/bin/env python3
"""Focused MCL execution on emitted Model II resident/CCP; disk transfer controlled."""
import argparse
import json
from pathlib import Path
import tempfile
from test_model2_external import Session,WINDOW,KEYS,ADVANCE,cpu_library,SHIM,disk
from test_submit_xsub import marker
from test_z80pack_submit_xsub import input_probe
from startup_record import build as startup_record
from pds_layout import layout
from build_ccp import assemble
from build_z80pack_image import symbols


class ComposedSession(Session):
    def __init__(self,library,out,media,enabled=True,startup=""):
        self.record=startup_record(startup,system_base=json.loads((out.parent/'profile/context.json').read_text())['symbols']['LY_SYS'],mcl=int(enabled))
        self.composed=False
        super().__init__(library,out,media)
    def step(self,keys,witness):
        if not self.composed:
            self.drives[0][128:384]=self.record
            self.composed=True
        return super().step(keys,witness)


def check(out,work,z80pack):
    window=WINDOW.replace('int enable =','if(port!=0xff)return;\n    int enable =')
    shim=SHIM[:SHIM.index('BYTE io_in')]+window+KEYS+SHIM[SHIM.index('void end_bus_request'):]+ADVANCE
    library=cpu_library(work,z80pack,shim)
    system=(out/'Model-II-System-candidate.imd').read_bytes()
    system_base=json.loads((out.parent/'profile/context.json').read_text())['symbols']['LY_SYS']
    def asm(name,text):return assemble(Path.home()/'bin/z80asm','        ORG 0100H\n'+text+'\n        END\n',work/(name+'.COM'),work/(name+'.lst'),0x100)
    cooked=asm('COOK','        LD C,1\n        CALL 5\n        RET')
    raw=asm('RAW','POLL: LD C,6\n        LD E,255\n        CALL 5\n        OR A\n        JR Z,POLL\n        JP 0')
    buffered=asm('BUFFER','        LD DE,0200H\n        LD A,20\n        LD (DE),A\n        LD C,10\n        CALL 5\n        RET')
    files=[('MARK.COM',marker(work)),('WORK.DAT',b'Z'*8192),('JPZERO.COM',b'\xc3\0\0'),('FNZERO.COM',b'\x0e\0\xcd\x05\0\xc9'),
           ('BIOSWB.COM',b'\x2a\x01\0\xe9'),
           ('FULL.COM',(bytes.fromhex('1109010e09cd0500c9')+b'MCL FULL FIT\r\n$').ljust(57216,b'\x76')),
           ('OVER.COM',(bytes.fromhex('1109010e09cd0500c9')+b'MCL FULL FIT\r\n$').ljust(57344,b'\x76')),
           ('ERROR.COM',bytes.fromhex('1109010e09cd0500c9')+b'TOOL ERROR\r\n$'),
           ('COOK.COM',cooked),('RAW.COM',raw),('BUFFER.COM',buffered),
           ('JOB.SUB',b'B:MARK JOB1\r\nB:MARK J;2\r\n'),
           ('BAD.SUB',b'B:MISSING\r\nB:MARK NEVER\r\n'),
           ('INPUT.COM',input_probe(work)),('XSUB.COM',(out.parent/'utilities/XSUB.COM').read_bytes()),
           ('BATCHIO.RSX',(out.parent/'rsx/BATCHIO.RSX').read_bytes()),
           ('INPUT.SUB',b'B:XSUB B:\r\nB:INPUT\r\nBATCHFULL\r\nB:MARK JOBEND\r\n')]
    scratch=disk(files);transcript=[]
    s=ComposedSession(library,out,[system,scratch])
    def command(text,witness=b'A0>'):
        result=s.step(text+b'\r',witness);transcript.append(result);return result
    def marks(text):
        import re
        return [tail.removeprefix(b' ') for tail in re.findall(rb'(?:^|[A-P][0-9]{1,2}> )MARK:([^\r\n]*)',text.replace(b'\r',b''),re.M)]
    def owner():
        plan=layout(bytes(s.ram[system_base-12:system_base]),system_base)
        return plan,plan['owners']['MCL'][0]
    text=command(b'B:MARK One;B:MARK "Two;2";;B:MARK THREE')
    assert marks(text)==[b'One',b'"Two;2"',b'THREE'],text
    plan,at=owner();h=plan['owners']['HISTORY'][0]
    assert s.ram[h+3]==1,'synthetic segments were recorded in history'
    n=s.ram[h+10];assert bytes(s.ram[h+11:h+11+n])==b'B:MARK One;B:MARK "Two;2";;B:MARK THREE'
    text=command(b'B:JPZERO;B:FNZERO;B:BIOSWB;B:MARK RETURN')
    assert marks(text)==[b'RETURN']
    text=command(b'B:MARK FIRST;B:MARK "bad')
    assert b'MCL invalid.' in text and not marks(text)
    for first in (b'B:MISSING',b'JUMP Z',b'POKE 8000 GG',b'GET MISSING.TXT',b'SAVE X B:BAD'):
        text=command(first+b';B:MARK NEVER')
        assert not marks(text),(first,text)
        assert bytes(s.ram[at:at+128])==bytes(128)
    text=command(b'B:FULL;B:MARK AFTERFULL')
    assert b'MCL FULL FIT' in text and marks(text)==[b'AFTERFULL']
    text=command(b'B:OVER;B:MARK NEVER')
    assert b'FILE WILL NOT FIT' in text and b'MCL FULL FIT' not in text and not marks(text)
    text=command(b'B:ERROR;B:MARK AFTERERROR')
    assert b'TOOL ERROR' in text and marks(text)==[b'AFTERERROR']
    for action,label in ((b'GO',b'AFTERGO'),(b'JUMP 100',b'AFTERJUMP')):
        text=command(b'GET B:MARK.COM;'+action+b' JUMPED;B:MARK '+label)
        assert marks(text)==[b'JUMPED',label],text
    text=command(b'VER;B:MARK CORE')
    assert marks(text)==[b'CORE'] and text.index(b'BetterCP/M')<text.index(b'MARK: CORE')
    text=command(b'1:;B0:MARK USER;0:')
    assert marks(text)==[b'USER']
    text=command(b'PATH B0:;MARK PATH;A:PATH /DEFAULT')
    assert marks(text)==[b'PATH'],text
    # GET/POKE may overwrite the complete finished-program worker area.
    text=command(b'RSX LOAD NDR;NDR WORK B0:;WORK:MARK NAMED;RSX UNLOAD NDR;B:MARK AFTER')
    assert marks(text)==[b'NAMED',b'AFTER'],text
    text=command(b'GET B:WORK.DAT;POKE 1700 41;SAVE 32 B:SAVED.DAT')
    expected=bytearray(b'Z'*8192);expected[0x1700-0x100]=0x41
    assert bytes(s.ram[0x100:0x2100])==expected,'GET/POKE data was overwritten by MCL'
    text=command(b'B:MARK AFTERGET')
    assert marks(text)==[b'AFTERGET']
    text=command(b'SUBMIT B:JOB;B:MARK AFTER')
    assert marks(text)==[b'JOB1',b'J;2',b'AFTER'],text
    text=command(b'SUBMIT B:BAD;B:MARK NEVER')
    assert not marks(text),text
    text=command(b'SUBMIT B:INPUT;B:MARK AFTERINPUT')
    assert b'INPUT OK' in text and b'INPUT FAILED' not in text
    assert marks(text)==[b'JOBEND',b'AFTERINPUT'],text
    command(b'RSX UNLOAD BATCHIO')
    # Let the application reach input first; then inject operator input.
    for program,keys,cancel in ((b'COOK',b'\x03',True),(b'BUFFER',b'\x03',True),
                                (b'BUFFER',(b'A',b'\x03\r'),False),(b'RAW',b'\x03',False)):
        command(b'B:'+program+b';B:MARK RESUMED',b'')
        assert s.ram[at+1]==1
        if isinstance(keys,tuple):
            transcript.append(s.step(keys[0],b''))
            keys=keys[1]
        text=s.step(keys,b'A0>');transcript.append(text)
        assert marks(text)==([] if cancel else [b'RESUMED']),(program,text)
        assert bytes(s.ram[at:at+128])==bytes(128)
    # Ordinary typed-ahead input survives pending commands in its original order.
    text=s.step(b'B:MARK ONE;B:MARK TWO\rZy',b'MARK: TWO');transcript.append(text)
    assert marks(text)==[b'ONE',b'TWO']
    base=s.ram[system_base+0x8c]|s.ram[system_base+0x8d]<<8
    count=base+symbols(out.parent/'ccp/ccp.lst')['CCP_COUNT']-0xbb00
    assert s.ram[count]==2 and bytes(s.ram[count+1:count+3])==b'Zy'
    transcript.append(s.step(b'\x15\r',b'A0>'))
    text=command(b'STAT MEM')
    assert b'57216 bytes' in text and b'MCL 128' in text
    # Saved startup is a distinct source, with literal semicolons/quotes.
    s=ComposedSession(library,out,[system,scratch],startup='B:MARK START;TAIL')
    assert marks(bytes(s.output))==[b'START;TAIL'],bytes(s.output)
    # True cold boot resets the owner; disabling keeps semicolons literal.
    s=ComposedSession(library,out,[system,scratch],enabled=False)
    text=command(b'B:MARK One;B:MARK Two')
    assert marks(text)==[b'One;B:MARK Two'],text
    return b'\n'.join(transcript)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('artifacts',type=Path)
    p.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    p.add_argument('--transcript',type=Path,required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory() as temporary:result=check(a.artifacts.resolve(),Path(temporary),a.z80pack)
    a.transcript.write_bytes(result)
    print('PASS emitted Model II MCL ordering, history, RET/JP0/Function0, known errors, SUBMIT/XSUB, cooked/raw abort semantics and disabled compatibility')
