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
    assert len(image)<0x9f00
    entry=int.from_bytes(image[1:3],'little')
    script=b''.join(bytes([len(line)])+line.encode('ascii') for line in lines)+b'\0'
    assert all(0<len(line)<=126 for line in lines)
    source=f''' ASEG
 ORG 0A000H
START: LD (OLDSP),SP
 LD HL,(6)
 LD (OLDBDOS),HL
 LD (CHAIN+1),HL
 LD HL,HOOK
 LD (6),HL
 LD HL,SCRIPT
 LD (CURSOR),HL
 CALL {entry}
 LD HL,(OLDBDOS)
 LD (6),HL
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
SCRIPT:
{chr(10).join(' DB '+','.join(str(x) for x in script[i:i+16]) for i in range(0,len(script),16))}
 END
'''
    with tempfile.TemporaryDirectory(prefix='dasm-script-') as folder:
        w=Path(folder);(w/'h.mac').write_text(source)
        subprocess.run([str(assembler),'-e32','-fb','-o'+str(w/'h.bin'),str(w/'h.mac')],
                       check=True,capture_output=True)
        wrapper=(w/'h.bin').read_bytes()
        if len(wrapper)>=0xa000:wrapper=wrapper[0xa000:]
    return b'\xc3\x00\xa0'+image[3:]+bytes(0x9f00-len(image))+wrapper
