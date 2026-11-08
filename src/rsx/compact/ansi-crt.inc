; ANSI controller owns wrap, margins, and rendition. These are fixed-cell atoms.
D_VISSET:
D_SAVEATTR:
D_RESTATTR:
        RET
D_PRINT:
        LD A,(D_REV)
        AND 128
        OR C
        LD HL,(CRT_POS)
        LD (HL),A
        XOR A
        RET
D_HOME:
        LD HL,0
        JR D_SET
D_CR:
        CALL D_GET
        LD H,0
D_SET:
        LD A,H
        LD (CRT_COL),A
        LD C,H
        LD E,L
        LD D,0
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,DE
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD E,C
        ADD HL,DE
        LD DE,0F800H
        ADD HL,DE
        LD (CRT_POS),HL
        XOR A
        LD (A_WRAP),A
        RET
D_OFF:
        XOR A
        JR D_REVERSE
D_ON:
        LD A,128
D_REVERSE:
        LD (D_REV),A
        XOR A
        RET
D_EOL:
        LD HL,(CRT_POS)
        LD A,(CRT_COL)
        LD C,A
        LD A,80
        SUB C
        LD C,A
        LD B,0
        JP D_FILL
D_EOS:
        LD HL,0FF80H
        LD DE,(CRT_POS)
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        EX DE,HL
        JP D_FILL
D_BELL:
        IF M2BANK EQ 0
        LD C,0
D_TONE:
        LD A,1
        LD B,100
D_HIGH:
        OUT (090H),A
        DJNZ D_HIGH
        XOR A
        LD B,100
D_LOW:
        OUT (090H),A
        DJNZ D_LOW
        DEC C
        JR NZ,D_TONE
        ENDIF
        RET
; Compute region addresses from the existing canonical cursor, retaining the
; original position on the bounded private/caller stack. BC = height - one row.
D_REGION:
        CALL D_GET
        POP DE
        PUSH HL
        PUSH DE
        LD A,(A_TOP)
        LD L,A
        LD H,0
        CALL D_SET
        LD HL,(CRT_POS)
        PUSH HL
        LD A,(A_BOTTOM)
        LD L,A
        LD H,0
        CALL D_SET
        LD HL,(CRT_POS)
        POP DE
        PUSH HL
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        POP HL
        RET
D_RSCROL:
        CALL D_REGION
        PUSH DE
        LD DE,79
        ADD HL,DE
        LD D,H
        LD E,L
        PUSH DE
        LD DE,80
        OR A
        SBC HL,DE
        POP DE
        LDDR
        POP HL
        JR D_BLANK
D_SCROLL:
        CALL D_REGION
        PUSH HL
        LD H,D
        LD L,E
        PUSH DE
        LD DE,80
        ADD HL,DE
        POP DE
        LDIR
        POP HL
D_BLANK:
        LD BC,80
        CALL D_FILL
        POP HL
        JP D_SET
D_FILL:
        LD A,(D_REV)
        AND 128
        OR 32
        LD (HL),A
        DEC BC
        LD A,B
        OR C
        RET Z
        LD D,H
        LD E,L
        INC DE
        LDIR
        XOR A
        RET
D_GET:
        LD HL,(CRT_POS)
        LD DE,0F800H
        OR A
        SBC HL,DE
        LD B,255
        LD DE,80
D_DIV:
        INC B
        OR A
        SBC HL,DE
        JR NC,D_DIV
        ADD HL,DE
        LD H,L
        LD L,B
        RET
        IF M2BANK EQ 1
D_MAP:
        LD (D_OP),A
        LD A,I
        DI
        PUSH AF
        LD (D_SP),SP
        LD SP,D_TOP
        LD A,081H
        OUT (0FFH),A
        LD A,(D_OP)
        CALL D_DISPATCH
D_UNMAP:
        LD (D_RESULT),A
        LD A,1
        OUT (0FFH),A
        LD SP,(D_SP)
        POP AF
        JP PO,D_NOEI
        EI
D_NOEI:
        PUSH HL
        LD HL,0
        LD (D_SP),HL
        POP HL
        LD A,(D_RESULT)
        OR A
        RET
D_SP: DW 0
D_OP: DB 0
D_RESULT: DB 0
D_GUARD: DB 0A5H
D_STACK: DS 20,0
D_TOP:
        ENDIF
