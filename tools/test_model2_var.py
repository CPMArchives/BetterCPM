#!/usr/bin/env python3
"""Execute VAR on emitted Model II code with controlled physical transfers."""
import argparse
import json
import tempfile
from pathlib import Path
from test_model2_external import Session,WINDOW,KEYS,ADVANCE,cpu_library,SHIM,disk
from test_submit_xsub import marker
from startup_record import build as startup_record
from build_ccp import assemble


class VarSession(Session):
    def __init__(self,library,out,media,variables=3,startup='VAR BOOT=START'):
        self.record=startup_record(startup,system_base=json.loads((out.parent/'profile/context.json').read_text())['symbols']['LY_SYS'],mcl=1,variables=variables)
        self.composed=False
        super().__init__(library,out,media)
    def step(self,keys,witness):
        if not self.composed:
            self.drives[0][128:384]=self.record;self.composed=True
        return super().step(keys,witness)


def check(out,work,z80pack):
    window=WINDOW.replace('int enable =','if(port!=0xff)return;\n    int enable =')
    library=cpu_library(work,z80pack,SHIM[:SHIM.index('BYTE io_in')]+window+KEYS+SHIM[SHIM.index('void end_bus_request'):]+ADVANCE)
    system=(out/'Model-II-System-candidate.imd').read_bytes()
    probe=assemble(Path.home()/'bin/z80asm','''        ORG 0100H
        LD DE,BUFFER
        LD C,10
        CALL 5
        LD HL,BUFFER+1
        LD B,(HL)
        INC HL
LOOP:   LD E,(HL)
        PUSH HL
        PUSH BC
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ LOOP
        RET
BUFFER: DB 32,0
        DS 34
        END
''',work/'INPUT.COM',work/'INPUT.lst',0x100)
    full=(bytes.fromhex('1109010e09cd0500c9')+b'VAR FULL FIT\r\n$').ljust(56704,b'\x76')
    files=[('MARK.COM',marker(work)),('JPZERO.COM',b'\xc3\0\0'),('FULL.COM',full),('OVER.COM',full+bytes(128)),
           ('DATA.DAT',b'Z'*36864),('INPUT.COM',probe),
           ('JOB.SUB',b'VAR S=JOB\r\nB:MARK %BOOT%\r\nB:MARK %S%;LITERAL\r\n'),
           ('BAD.SUB',b'B:MARK %MISSING%\r\nB:MARK NEVER\r\n'),
           ('IN.SUB',b'B:XSUB B:\r\nB:INPUT\r\n%MISSING%\r\nB:MARK %BOOT%\r\n'),
           ('XSUB.COM',(out.parent/'utilities/XSUB.COM').read_bytes()),
           ('BATCHIO.RSX',(out.parent/'rsx/BATCHIO.RSX').read_bytes())]
    media=disk(files);s=VarSession(library,out,[system,media]);transcript=[]
    def command(text):
        result=s.step(text+b'\r',b'A0>');transcript.append(result);return result
    def marks(text):
        import re
        return [x.removeprefix(b' ') for x in re.findall(rb'(?:^|[A-P][0-9]{1,2}> )MARK:([^\r\n]*)',text.replace(b'\r',b''),re.M)]
    assert marks(command(b'B:MARK %BOOT%'))==[b'START']
    assert marks(command(b'VAR X=One;B:MARK %x%;VAR X=Two;B:MARK %X%'))==[b'One',b'Two']
    assert marks(command(b'VAR EMPTY=;B:MARK A%EMPTY%B'))==[b'AB']
    assert marks(command(b'VAR P=%%X%%;B:MARK %P%'))==[b'%X%']
    assert marks(command(b'VAR Q="A;B";B:MARK %Q%'))==[b'"A;B"']
    assert marks(command(b'B:JPZERO;B:MARK %X%'))==[b'Two']
    text=command(b'VAR /D X;B:MARK %X%;B:MARK NEVER')
    assert b'VAR undefined.' in text and not marks(text),text
    for bad in (b'VAR 1X=bad',b'B:MARK %',b'B:MARK %BAD-NAME%'):
        text=command(bad+b';B:MARK NEVER');assert b'VAR invalid.' in text and not marks(text),text
    text=command(b'VAR LONG='+b'x'*100);assert b'VAR full.' not in text
    text=command(b'B:MARK '+b'y'*25+b'%LONG%;B:MARK NEVER')
    assert b'exceeds 127' in text and not marks(text),text
    assert marks(command(b'B:FULL;B:MARK %BOOT%'))==[b'START']
    text=command(b'B:OVER;B:MARK NEVER');assert b'FILE WILL NOT FIT' in text and not marks(text)
    assert marks(command(b'VAR TARGET=WORK:;RSX LOAD NDR;NDR WORK B0:;%TARGET%MARK NAMED;RSX UNLOAD NDR;B:MARK %BOOT%'))==[b'NAMED',b'START']
    assert marks(command(b'VAR HERE=B0:;PATH %HERE%;MARK PATH;A:PATH /DEFAULT'))==[b'PATH']
    command(b'GET B:DATA.DAT;POKE 1700 41;SAVE 144 B:SAVED.DAT')
    expected=bytearray(b'Z'*36864);expected[0x1700-0x100]=65
    assert bytes(s.ram[0x100:0x9100])==expected
    assert marks(command(b'B:MARK %BOOT%'))==[b'START']
    assert marks(command(b'SUBMIT B:JOB;B:MARK %S%'))==[b'START',b'JOB;LITERAL',b'JOB']
    text=command(b'SUBMIT B:BAD;B:MARK NEVER');assert b'VAR undefined.' in text and not marks(text)
    text=command(b'SUBMIT B:IN;B:MARK %BOOT%')
    assert b'%MISSING%' in text and b'VAR undefined.' not in text and marks(text)==[b'START',b'START'],text
    command(b'RSX UNLOAD BATCHIO')
    text=command(b'STAT MEM');assert b'VAR 512' in text and b'56704 bytes' in text
    # A new true cold session has an empty owner, with no startup assignment.
    s=VarSession(library,out,[system,media],startup='')
    text=command(b'B:MARK %BOOT%');assert b'VAR undefined.' in text and not marks(text)
    s=VarSession(library,out,[system,media],variables=0,startup='')
    assert marks(command(b'B:MARK %BOOT% %%'))==[b'%BOOT% %%']
    assert b'VAR disabled;' in command(b'VAR')
    return b'\n'.join(transcript)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('artifacts',type=Path)
    p.add_argument('--z80pack',type=Path,default=Path.home()/'projects/git/z80pack')
    p.add_argument('--transcript',type=Path,required=True);a=p.parse_args()
    with tempfile.TemporaryDirectory() as temporary:result=check(a.artifacts.resolve(),Path(temporary),a.z80pack)
    a.transcript.write_bytes(result)
    print('PASS emitted Model II VAR startup/MCL/SUBMIT/XSUB, warm/cold, exact fit/overflow, NDR/PATH, GET/POKE and disabled behavior')
