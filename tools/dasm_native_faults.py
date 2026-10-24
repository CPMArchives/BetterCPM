"""Test-only real-filesystem setup inside the resident line-input wrapper."""
def setup(kind):
    if kind not in ('directory','data','file-ro','media-ro'):raise ValueError(kind)
    header='DIR00000TMP' if kind=='directory' else 'FULLDATATMP' if kind=='data' else 'KEEP    ASM'
    if kind=='media-ro':
        body=''' LD C,28
 CALL HF_BDOS
 JP HF_READY
'''
    elif kind=='file-ro':
        body=''' LD A,(HF_FCB+9)
 OR 128
 LD (HF_FCB+9),A
 LD DE,HF_FCB
 LD C,30
 CALL HF_BDOS
 CP 255
 JP Z,HF_FAILED
 JP HF_READY
'''
    else:
        body='''HF_CREATE:
 LD HL,HF_FCB+12
 LD DE,HF_FCB+13
 LD BC,23
 LD (HL),0
 LDIR
 LD DE,HF_BUFFER
 LD C,26
 CALL HF_BDOS
 LD DE,HF_FCB
 LD C,17
 CALL HF_BDOS
 CP 255
 JP NZ,HF_FAILED
 LD DE,HF_FCB
 LD C,22
 CALL HF_BDOS
 CP 255
'''
        if kind=='directory':
            body+=''' JP Z,HF_READY
 LD DE,HF_FCB
 LD C,16
 CALL HF_BDOS
 CP 255
 JP Z,HF_FAILED
 LD HL,HF_FCB+8
 LD B,5
HF_DIGIT:
 INC (HL)
 LD A,(HL)
 CP '9'+1
 JP C,HF_CREATE
 LD (HL),'0'
 DEC HL
 DJNZ HF_DIGIT
 JP HF_FAILED
'''
        else:
            body+=''' JP Z,HF_FAILED
 LD HL,HF_BUFFER
 LD B,128
HF_PATTERN:
 LD (HL),0A5H
 INC HL
 DJNZ HF_PATTERN
HF_WRITE:
 LD DE,HF_FCB
 LD C,21
 CALL HF_BDOS
 OR A
 JR Z,HF_WRITE
 LD DE,HF_FCB
 LD C,16
 CALL HF_BDOS
 CP 255
 JP Z,HF_FAILED
 JP HF_READY
'''
    return '''HF_START:
 LD HL,HF_FCB
 LD DE,HF_FCB+1
 LD BC,35
 LD (HL),0
 LDIR
 LD HL,HF_NAME
 LD DE,HF_FCB+1
 LD BC,11
 LDIR
'''+body+'''HF_READY:
 LD DE,HF_READY_MSG
 JR HF_REPORT
HF_FAILED:
 LD DE,HF_FAILED_MSG
HF_REPORT:
 LD C,9
 CALL HF_BDOS
 LD DE,80H
 LD C,26
 CALL HF_BDOS
 RET
HF_BDOS:
 PUSH BC
 PUSH DE
 PUSH HL
 PUSH IX
 PUSH IY
 CALL CHAIN
 POP IY
 POP IX
 POP HL
 POP DE
 POP BC
 RET
HF_READY_MSG: DB 'DASM FILESYSTEM FIXTURE READY',13,10,'$'
HF_FAILED_MSG: DB 'DASM FILESYSTEM FIXTURE FAILED',13,10,'$'
HF_NAME: DB '''+repr(header)+'''
HF_FCB: DS 36
HF_BUFFER: DS 128
'''
