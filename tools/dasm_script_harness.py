"""Temporary native line-input harness; real CP/M handles every file operation.

The wrapper lowers the active TPA ceiling to its BDOS interceptor, restores the
original vector on return, and supplies only function-10 command lines. This
is not console/keyboard qualification. The DASM core differs only in its entry
jump; the wrapper calls that original entry after installing its interceptor.
"""
from pathlib import Path
import subprocess
import tempfile


def scripted(image, lines, assembler=Path.home()/'bin/z80asm'):
    assert image[0]==0xc3
    base=0xb800
    assert len(image)<base-0x100
    entry=int.from_bytes(image[1:3],'little')
    script=b''.join(bytes([len(line)])+line.encode('ascii') for line in lines)+b'\0'
    assert all(0<len(line)<=126 for line in lines)
    source=f''' ASEG
 ORG {base}
ENTRY: JP HOOK
START: LD (OLDSP),SP
 LD HL,(6)
 LD (OLDBDOS),HL
 LD (CHAIN+1),HL
 LD DE,0C180H
 OR A
 SBC HL,DE
 JR C,LOW_RAM
 LD HL,0C000H
 LD B,128
PAINT: LD (HL),0A5H
 INC HL
 DJNZ PAINT
 LD HL,ENTRY
 LD (6),HL
 LD HL,SCRIPT
 LD (CURSOR),HL
 CALL {entry}
 LD HL,(OLDBDOS)
 LD (6),HL
 LD HL,0C000H
 LD B,128
VERIFY: LD A,(HL)
 CP 0A5H
 JR NZ,CANARY_BAD
 INC HL
 DJNZ VERIFY
 LD DE,PASS_MSG
 JR REPORT
CANARY_BAD: LD DE,FAIL_MSG
 JR REPORT
LOW_RAM: LD DE,LOW_MSG
REPORT: LD C,9
 CALL CHAIN
 LD SP,(OLDSP)
 RET
HOOK: LD A,C
 CP 10
 JR Z,LINE
CHAIN: JP 0
LINE: LD HL,(CURSOR)
 LD A,(HL)
 OR A
 JR Z,EXHAUSTED
 INC HL
 INC DE
 LD (DE),A
 INC DE
 LD C,A
 LD B,0
 LDIR
 LD A,13
 LD (DE),A
 LD (CURSOR),HL
 XOR A
 RET
EXHAUSTED: HALT
 JR EXHAUSTED
OLDSP: DW 0
OLDBDOS: DW 0
CURSOR: DW SCRIPT
PASS_MSG: DB 'DASM RESIDENT CANARY PASS',13,10,'$'
FAIL_MSG: DB 'DASM RESIDENT CANARY FAIL',13,10,'$'
LOW_MSG: DB 'DASM HARNESS INSUFFICIENT ORIGINAL TPA',13,10,'$'
SCRIPT:
{chr(10).join(' DB '+','.join(str(x) for x in script[i:i+16]) for i in range(0,len(script),16))}
 END
'''
    with tempfile.TemporaryDirectory(prefix='dasm-script-') as folder:
        w=Path(folder);(w/'h.mac').write_text(source)
        subprocess.run([str(assembler),'-e32','-fb','-o'+str(w/'h.bin'),str(w/'h.mac')],
                       check=True,capture_output=True)
        wrapper=(w/'h.bin').read_bytes()
        if len(wrapper)>=base:wrapper=wrapper[base:]
    assert base+len(wrapper)<=0xc000, 'script harness exceeds its reserved region'
    return b'\xc3'+(base+3).to_bytes(2,'little')+image[3:]+bytes(base-0x100-len(image))+wrapper
