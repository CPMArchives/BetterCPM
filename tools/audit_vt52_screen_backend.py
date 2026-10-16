#!/usr/bin/env python3
"""Measure and exercise an isolated Model 4 screen-primitive backend candidate.

Audit only: never patches a production BIOS or installs the candidate. These
operations would live behind MONRAW, leaving hardware addresses out of VT52.
The proposed ABI is not established by this measurement.
"""
import json
from pathlib import Path
from build_ccp import assemble
from test_bios import Z80
from test_vt52_foundation import symbols
from system_layout import LAYOUT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/audit/vt52-screen-backend'
SOURCE='''        ASEG
        ORG 07000H
SB_ENTRY:
        CP 6
        JP C,MC_RAW
        SUB 6
        CP 7
        JR NC,SB_BAD
        ADD A,A
        LD E,A
        LD D,0
        LD HL,SB_TABLE
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        JP (HL)
SB_BAD:
        LD A,0FFH
        RET
SB_TABLE:
        DW SB_POS,SB_PUT,SB_EOL,SB_EOS,SB_UP,SB_DOWN,SB_QUERY
SB_QUERY:
        LD HL,SB_DESC
        RET
SB_DESC:
        DB 'SCR',1,24,80,03FH
SB_POS:
        LD A,B
        CP 24
        JR NC,SB_BAD
        LD A,C
        CP 80
        JR NC,SB_BAD
        LD L,B
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD D,H
        LD E,L
        ADD HL,HL
        ADD HL,HL
        ADD HL,DE
        LD E,C
        LD D,0
        ADD HL,DE
        LD DE,0F800H
        ADD HL,DE
        LD (M4CURSOR),HL
        LD A,C
        LD (M4COLUMN),A
        RET
SB_PUT:
        LD HL,(M4CURSOR)
        LD (HL),C
        RET
SB_EOL:
        LD A,(M4COLUMN)
        LD B,A
        LD A,80
        SUB B
        LD C,A
        LD B,0
        LD HL,(M4CURSOR)
        JR SB_FILL
SB_EOS:
        LD HL,0FF80H
        LD DE,(M4CURSOR)
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        EX DE,HL
        JR SB_FILL
SB_UP:
        LD HL,0F850H
        LD DE,0F800H
        LD BC,1840
        LDIR
        LD HL,0FF30H
        JR SB_LINE
SB_DOWN:
        LD HL,0FF2FH
        LD DE,0FF7FH
        LD BC,1840
        LDDR
        LD HL,0F800H
SB_LINE:
        LD BC,80
SB_FILL:
        LD (HL),32
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,SB_FILL
        RET
        END
'''


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    syms=symbols(ROOT/'build/bios/bios.lst')
    bindings=''.join(f'{name} EQU 0{syms[name]:04X}H\n' for name in ['MC_RAW','M4CURSOR','M4COLUMN'])
    text=bindings+SOURCE
    (OUT/'candidate.mac').write_text(text)
    code=assemble(Path.home()/'bin/z80asm',text,OUT/'candidate.bin',OUT/'candidate.lst',0x7000)
    cpu=Z80((ROOT/'build/bios/bios.bin').read_bytes())
    cpu.mem[0x7000:0x7000+len(code)]=code
    def call(op,row=0,col=0,char=0):
        sp=cpu.sp
        cpu.a=op;cpu.b=row;cpu.c=col if op==6 else char
        cpu.run(0x7000,limit=100000)
        assert cpu.sp==sp
    cases=0
    for row in range(24):
        for col in range(80):
            cpu.mem[0xF7FF]=0xA5;cpu.mem[0xFF80]=0x5A
            initial=bytes((i%95)+32 for i in range(1920))
            at=row*80+col
            call(6,row,col)
            assert cpu.word(syms['M4CURSOR'])==0xF800+at
            assert cpu.mem[syms['M4COLUMN']]==col
            for op in [7,8,9,10,11]:
                cpu.mem[0xF800:0xFF80]=initial
                expected=bytearray(initial)
                if op==7:expected[at]=ord('X')
                elif op==8:expected[at:(row+1)*80]=b' '* (80-col)
                elif op==9:expected[at:]=b' '*(1920-at)
                elif op==10:expected[:]=initial[80:]+b' '*80
                elif op==11:expected[:]=b' '*80+initial[:-80]
                call(op,char=ord('X'))
                assert cpu.mem[0xF800:0xFF80]==expected,(row,col,op)
                assert cpu.word(syms['M4CURSOR'])==0xF800+at
                assert cpu.mem[syms['M4COLUMN']]==col
                assert cpu.mem[0xF7FF]==0xA5 and cpu.mem[0xFF80]==0x5A
                cases+=1
    before=bytes(cpu.mem)
    for row,col in [(24,0),(255,0),(0,80),(0,255)]:
        call(6,row,col);assert cpu.a==255
        assert cpu.mem[0xF800:0xFF80]==before[0xF800:0xFF80]
        assert cpu.word(syms['M4CURSOR'])==int.from_bytes(before[syms['M4CURSOR']:syms['M4CURSOR']+2],'little')
    call(12)
    assert bytes(cpu.mem[cpu.hl:cpu.hl+7])==b'SCR\x01\x18\x50\x3f'
    call(13);assert cpu.a==255
    # Check legacy basic-console fallback at an ordinary position.
    call(6,2,3);call(0,char=ord('Q'))
    assert cpu.mem[0xF800+163]==ord('Q')
    bios_bytes=len((ROOT/'build/bios/bios.bin').read_bytes())
    capacity=LAYOUT['FILE']-LAYOUT['BIOS']
    report=dict(candidate_bytes=len(code),screen_cases=cases,bios_bytes=bios_bytes,
                bios_capacity=capacity,bios_spare=capacity-bios_bytes,
                standalone_addition_before_integration=len(code),
                integration_note='Standalone dispatcher replaces the raw entry route; final integration/metadata and new ports are not costed.',
                production_modified=False)
    (OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
