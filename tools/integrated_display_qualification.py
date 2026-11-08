"""Shared disposable guest programs for the integrated TCAP 2.0 campaign."""
from pathlib import Path
import re
from build_ccp import assemble
from tcap_test_support import PRINTER

ROOT=Path(__file__).resolve().parents[1]


def fixtures(out,maximum,assembler=None,handshake=False,personality='ADM3A'):
    assembler=assembler or Path.home()/'bin/z80asm'
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True)
    result={}
    def program(name,text):
        result[name+'.COM']=assemble(assembler,'        ASEG\n        ORG 0100H\n'+text+'\n        END\n',
            out/(name+'.bin'),out/(name+'.lst'),0x100)
    program('BOUND',"""        LD DE,MSG
        LD C,9
        CALL 5
        LD HL,(6)
        LD A,H
        CALL HEX
        LD A,L
        CALL HEX
        LD DE,NL
        LD C,9
        CALL 5
        JP 0
MSG: DB 'BOUNDARY $'
NL: DB 13,10,'$'
"""+PRINTER)
    program('MAXCOM',"""        LD DE,MSG
        LD C,9
        CALL 5
        JP 0
MSG: DB 'MAXIMUM COM PASS',13,10,'$'
""")
    result['MAXCOM.COM']=result['MAXCOM.COM'].ljust(maximum,b'\0')
    program('ABSENT',"""        LD DE,LOOK
        LD C,182
        CALL 5
        CP 1
        LD DE,FAIL
        JR NZ,DONE
        LD DE,PASS
DONE:   LD C,9
        CALL 5
        JP 0
LOOK: DB 1,20,0,0,'TCAP',2,0,0,0
      DS 8,0
PASS: DB 'INTEGRATED ABSENT PASS',13,10,'$'
FAIL: DB 'INTEGRATED ABSENT FAIL',13,10,'$'
""")
    demo="""        CALL T2_OPEN
        OR A
        JR NZ,FAIL
        LD A,6
        CALL T2_EMIT
        LD A,1
        CALL T2_EMIT
        LD B,4
        LD C,9
        LD A,2
        CALL T2_EMIT
        OR A
        JR NZ,FAIL
        LD A,3
        CALL T2_EMIT
        OR A
        JR NZ,FAIL
        LD A,4
        CALL T2_EMIT
        LD DE,TEXT
        LD C,9
        CALL 5
        LD A,5
        CALL T2_EMIT
        LD A,7
        CALL T2_EMIT
        LD DE,READY
        LD C,9
        CALL 5
        LD A,(82H)
        LD E,A
        LD C,2
        CALL 5
        LD C,1
        CALL 5
        LD DE,PASS
        JR DONE
FAIL:   LD DE,ERROR
DONE:   LD C,9
        CALL 5
        JP 0
TEXT: DB 'TCAP TEXT$'
READY: DB 13,10,'INTEGRATED READY $'
PASS: DB 'INTEGRATED DEMO PASS',13,10,'$'
ERROR: DB 'INTEGRATED DEMO FAIL',13,10,'$'
"""
    if handshake:
        demo=demo.replace('        LD C,1\n        CALL 5\n','''READ:   LD C,1
        CALL 5
        LD HL,82H
        CP (HL)
        JR NZ,READ
''')
    program('DEMO',demo+(ROOT/'src/utilities/common/tcap2.inc').read_text())
    legacy="""        LD HL,CONTROL
        LD B,7
LOOP:   PUSH HL
        PUSH BC
        LD E,(HL)
        LD C,2
        CALL 5
        POP BC
        POP HL
        INC HL
        DJNZ LOOP
        LD DE,TEXT
        LD C,9
        CALL 5
        JP 0
CONTROL: DB 14,26,27,'=',36,41,15
TEXT: DB 'LEGACY TEXT',14,13,10
      DB 'INTEGRATED LEGACY PASS',13,10,'$'
"""
    if personality=='VT52':
        legacy=legacy.replace('        LD B,7','        LD B,8').replace(
            "CONTROL: DB 14,26,27,'=',36,41,15","CONTROL: DB 27,'H',27,'J',27,'Y',36,41")
    if personality=='ANSI':
        legacy=legacy.replace('        LD B,7','        LD B,CONTROL_END-CONTROL').replace(
            "CONTROL: DB 14,26,27,'=',36,41,15",
            "CONTROL: DB 27,'[0m',27,'[2J',27,'[5;10H',27,'[7m'\nCONTROL_END:")
        legacy=legacy.replace("TEXT: DB 'LEGACY TEXT',14,13,10", "TEXT: DB 'LEGACY TEXT',27,'[0m',13,10")
    program('LEGACY',legacy)
    helper=(ROOT/'src/utilities/common/tcap2.inc').read_text()
    for name,want,caption in (('ADMIT',0,'ADMISSION'),('REFUSE',1,'OWNER REFUSAL')):
        program(name,f'''        CALL T2_OPEN
        CP {want}
        LD DE,BAD
        JR NZ,SHOW
        LD DE,GOOD
SHOW:   LD C,9
        CALL 5
        JP 0
GOOD: DB 'TCAP {caption} PASS',13,10,'$'
BAD: DB 'TCAP {caption} FAIL',13,10,'$'
'''+helper)
    program('ROUTE','''        LD A,(3)
        PUSH AF
        AND 0FCH
        OR 2
        LD (3),A
        CALL T2_OPEN
        LD (RESULT),A
        POP AF
        LD (3),A
        LD A,(RESULT)
        CP 1
        JR NZ,FAILED
        CALL T2_OPEN
        OR A
        JR NZ,FAILED
        LD DE,GOOD
        JR SHOW
FAILED: LD DE,BAD
SHOW:   LD C,9
        CALL 5
        JP 0
RESULT: DB 0
GOOD: DB 'TCAP ROUTE REFUSAL PASS',13,10,'$'
BAD: DB 'TCAP ROUTE REFUSAL FAIL',13,10,'$'
'''+helper)
    return result


def commands(personality='ADM3A'):
    result=['BOUND','MAXCOM','ABSENT','RSX LOAD ECHO','RSX LOAD ADM3A','REFUSE','RSX UNLOAD ECHO','BOUND','ADMIT','ROUTE','LEGACY','DEMO 1',
        'RSX LOAD HELLO','DEMO 2','RSX UNLOAD HELLO','DEMO 3','RSX LIST',
        'RSX UNLOAD ADM3A','BOUND','MAXCOM','ABSENT',
        'RSX LOAD ADM3A','DEMO 4','RSX UNLOAD ADM3A','BOUND','MAXCOM','ABSENT']
    return [c.replace('ADM3A',personality) for c in result]


def audit(commands,frames,budgets,baseline):
    records=[];boundaries=[];active=None
    for command,text in zip(commands,frames):
        assert 'FAIL' not in text and 'error' not in text.lower(),(command,text)
        item={'command':command}
        if command.startswith('RSX LOAD ') and command.split()[-1] in budgets:active=command.split()[-1]
        if command.startswith('RSX UNLOAD ') and command.split()[-1] in budgets:active=None
        if command=='BOUND':
            boundary=int(re.findall(r'BOUNDARY ([0-9A-F]{4})',text)[-1],16)
            expected=baseline if active is None else baseline-1024-budgets[active]['resident_profile_bytes']
            assert boundary==expected,(command,active,boundary,expected)
            boundaries.append(boundary);item['boundary']=boundary
        for cmd,caption in [('MAXCOM','MAXIMUM COM PASS'),('ABSENT','INTEGRATED ABSENT PASS'),
            ('ADMIT','TCAP ADMISSION PASS'),('REFUSE','TCAP OWNER REFUSAL PASS'),('ROUTE','TCAP ROUTE REFUSAL PASS'),
            ('DEMO','INTEGRATED DEMO PASS'),('LEGACY','INTEGRATED LEGACY PASS')]:
            if command==cmd or (cmd=='DEMO' and command.startswith('DEMO ')) or (cmd=='LEGACY' and command.startswith('L') and command[1:] in budgets):
                assert caption in text,(command,text)
        records.append(item)
    assert len(frames)==len(commands)
    assert boundaries[0]==boundaries[-1]==baseline and active is None
    return records


def collection(workspace,out,platform,maximum,personalities,inline_cache=False,handshake=False):
    from build_integrated_display import build
    out=Path(out);files={};budgets={};sequence=[]
    for name in personalities:
        carrier,budget=build(workspace,out/'profiles'/name,platform,name,inline_cache=inline_cache)
        programs=fixtures(out/'fixtures'/name,maximum,handshake=handshake,personality=name)
        programs['L'+name+'.COM']=programs.pop('LEGACY.COM')
        files.update(programs);files[name+'.RSX']=carrier;budgets[name]=budget
        sequence.extend('L'+name if c=='LEGACY' else c for c in commands(name))
    files['ECHO.RSX']=owner_refusal_fixture(workspace)
    return files,budgets,sequence


def owner_refusal_fixture(workspace):
    from build_rsx_module import make_module
    from checked_carriers import rsx_metadata
    from checked_build_contract import load_contract
    carrier=make_module(name='ECHO',version=(1,0),services=[],linked_base=0x8000,
                        code=bytes.fromhex('05000880000000002a0080e93e01c9'),relocations=[2,9],
                        callable_services=[(b'TCAP',2,0,12,0)],cache_footer_inline=True)
    context=Path(workspace)/'build/profile/context.json'
    if context.exists() and carrier[4]==2:
        item=bytearray(carrier);at=int.from_bytes(item[30:32],'little');item[4]=3
        carrier=bytes(item[:at])+rsx_metadata('ECHO',bytes(item[at:]),load_contract(Path(workspace),Path.home()/'bin/z80asm'))
    return carrier
