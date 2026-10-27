; Four independent streaming accumulators. Numerical state is little endian.
; CINIT resets, CUPDATE consumes A (destroys AF/BC/DE/HL), CFINISH finalizes.
; Always calculate all four: checking can discover the recorded subset later.
CINIT:
        LD HL,CVALUES
        LD B,6
        XOR A
CI16:
        LD (HL),A
        INC HL
        DJNZ CI16
        LD B,4
        DEC A
CI32:
        LD (HL),A
        INC HL
        DJNZ CI32
        RET
CUPDATE:
        LD (CBYTE),A
        LD HL,(CVALUES)
        ADD HL,HL
        PUSH AF
        LD A,(CBYTE)
        ADD A,L
        LD L,A
        POP AF
        JR NC,CUOLD
        LD A,H
        XOR 0A0H
        LD H,A
        LD A,L
        XOR 097H
        LD L,A
CUOLD:
        LD (CVALUES),HL
        LD HL,(CVALUES+2)
        LD DE,0A097H
        CALL CU16
        LD (CVALUES+2),HL
        LD HL,(CVALUES+4)
        LD DE,01021H
        CALL CU16
        LD (CVALUES+4),HL
        LD HL,CVALUES+6
        LD A,(CBYTE)
        XOR (HL)
        LD (HL),A
        LD B,8
CU32:
        LD HL,CVALUES+9
        SRL (HL)
        DEC HL
        RR (HL)
        DEC HL
        RR (HL)
        DEC HL
        RR (HL)
        JR NC,CU32NEXT
        LD A,(HL)
        XOR 020H
        LD (HL),A
        INC HL
        LD A,(HL)
        XOR 083H
        LD (HL),A
        INC HL
        LD A,(HL)
        XOR 0B8H
        LD (HL),A
        INC HL
        LD A,(HL)
        XOR 0EDH
        LD (HL),A
CU32NEXT:
        DJNZ CU32
        RET
CU16:
        LD A,(CBYTE)
        XOR H
        LD H,A
        LD B,8
CU16BIT:
        ADD HL,HL
        JR NC,CU16NEXT
        LD A,H
        XOR D
        LD H,A
        LD A,L
        XOR E
        LD L,A
CU16NEXT:
        DJNZ CU16BIT
        RET
CFINISH:
        LD HL,CVALUES+6
        LD B,4
CF32:
        LD A,(HL)
        CPL
        LD (HL),A
        INC HL
        DJNZ CF32
        RET
CVALUES: DS 10
CBYTE: DB 0
