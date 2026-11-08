; TCAP 2.0 direct-operation client. All persistent caller state belongs to the transient.
; OPEN returns HL -> eight immutable facts; rediscover after layout changes.
; EMIT calls the selected provider's direct operation, A=1..7, B/C=coordinates.
; No string interpreter, copied templates, session or recovery engine.
T2_OPEN:
        LD DE,T2_LOOK
        LD C,182
        CALL 5
        OR A
        JR NZ,T2_NONE
        LD (T2_ENTRY),HL
        LD DE,T2_MCON
        LD C,182
        CALL 5
        OR A
        JR NZ,T2_NONE
        LD A,(T2_LOOK+18)
        LD HL,T2_MCON+18
        CP (HL)
        JR NZ,T2_NONE
        CALL T2_ROUTE
        JR NZ,T2_NONE
        LD HL,(T2_ENTRY)
        LD DE,T2_GOT
        PUSH DE
        XOR A
        JP (HL)
T2_GOT:
        OR A
        JR NZ,T2_NONE
        PUSH HL
        LD DE,T2_HEAD
        LD B,4
T2_CHECK:
        LD A,(DE)
        CP (HL)
        JR NZ,T2_BAD
        INC DE
        INC HL
        DJNZ T2_CHECK
        POP HL
        XOR A
        RET
T2_BAD:
        POP HL
T2_NONE:
        LD HL,0
        LD (T2_ENTRY),HL
        LD A,1
        RET
T2_EMIT:
        PUSH AF
        CALL T2_ROUTE
        JR NZ,T2_NOEMIT
        LD HL,(T2_ENTRY)
        LD A,H
        OR L
        JR Z,T2_NOEMIT
        POP AF
        JP (HL)
T2_NOEMIT:
        POP AF
        LD A,1
        RET
T2_ROUTE:
        LD A,(3)
        AND 3
        JR NZ,T2_CRT
        LD A,(T2_MCON+16)
        CP 2
        RET
T2_CRT:
        CP 1
        RET
T2_CODE_END:
T2_ENTRY: DW 0
T2_HEAD: DB 'TC',2,8
T2_LOOK: DB 1,20,0,0,'TCAP',2,0,0,0
        DS 8,0
T2_MCON: DB 1,20,0,0,'MCON',1,0,0,0
        DS 8,0
T2_END:
