; DRI wildcard copy: restart and skip directory entries after each transaction.
PW_START:
        LD A,(PP_COUNT)
        CP 2
        JP NZ,PT_UNSUP
        LD A,(OP_DATA)
        CP 1
        JP Z,PW_ONEXT
        CP 7
        JP Z,PW_ONEXT
        CP 8
        JP Z,PW_ONEXT
        CP 4
        JP Z,PW_ONEXT
        CP 13
        JP Z,PW_ONEXT
        CP 15
        JP Z,PW_ONEXT
        CP 3
        JP NZ,PT_UNSUP
        LD A,(OP_DATA+2)
        CP 4
        JP NC,PT_DRIVEERR
        LD A,(OP_DATA+82)
        CP 4
        JP NC,PT_DRIVEERR
        LD HL,OP_DATA+82
        LD A,(OP_DATA+2)
        CP (HL)
        JR NZ,PW_VALID
        INC HL
        LD A,(OP_DATA+3)
        CP (HL)
        JR NZ,PW_VALID
        LD DE,P_INVALID
        JP P_ERROR
PW_VALID:
        LD HL,OP_DATA+124
        LD B,26
        LD C,0
PW_OPT:
        LD A,(HL)
        OR A
        JP Z,PW_ONEXT
        LD A,C
        CP 3
        JP Z,PW_ONEXT
        CP 5
        JP Z,PW_ONEXT
        CP 19
        JP Z,PW_ONEXT
        CP 16
        JP Z,PW_ONEXT
        CP 18
        JP Z,PW_ONEXT
        CP 11
        JP Z,PW_ONEXT
        CP 20
        JP Z,PW_ONEXT
        CP 25
        JP Z,PW_ONEXT
        CP 6
        JP Z,PW_ONEXT
        CP 14
        JP Z,PW_ONEXT
        CP 17
        JP Z,PW_ONEXT
        CP 21
        JP Z,PW_ONEXT
        CP 22
        JP NZ,PT_UNSUP
PW_ONEXT:
        INC HL
        INC C
        DJNZ PW_OPT
        LD HL,OP_DATA+80
        LD DE,PW_REC
        LD BC,80
        LDIR
        LD HL,OP_DATA+88
        LD DE,PW_FCB
        LD BC,36
        LDIR
        LD A,'?'
        LD (PW_FCB+12),A
        XOR A
        LD (PW_COPIED),A
        LD HL,0
        LD (PW_NEXT),HL
        LD A,1
        LD (PW_ACTIVE),A
PW_SCAN:
        LD A,(PW_REC+2)
        LD D,A
        LD A,(PW_REC+3)
        CALL PT_SETDU
        LD C,31
        CALL 5
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        LD (PW_EXM),A
        LD DE,PW_DMA
        LD C,26
        CALL 5
        LD HL,0
        LD (PW_INDEX),HL
        LD DE,PW_FCB
        LD C,17
        CALL 5
PW_RESULT:
        CP 0FFH
        JP Z,PW_END
        LD (PW_SLOT),A
        LD HL,(PW_INDEX)
        LD DE,(PW_NEXT)
        LD A,L
        CP E
        JR NZ,PW_SNEXT
        LD A,H
        CP D
        JR Z,PW_FOUND
PW_SNEXT:
        LD HL,(PW_INDEX)
        INC HL
        LD (PW_INDEX),HL
        LD C,18
        CALL 5
        JR PW_RESULT
PW_FOUND:
        INC HL
        LD (PW_NEXT),HL
        LD A,(PW_SLOT)
        AND 3
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,PW_DMA
        ADD HL,DE
        LD (PW_ENTRY),HL
        LD DE,14
        ADD HL,DE
        LD A,(HL)
        AND 3FH
        JP NZ,PW_SCAN
        DEC HL
        DEC HL
        LD A,(HL)
        AND 1FH
        LD B,A
        LD A,(PW_EXM)
        CP B
        JP C,PW_SCAN
        DEC HL
        DEC HL
        LD A,(HL)
        AND 80H
        JR Z,PW_ADMIT
        LD A,(PW_REC+61)
        OR A
        JP Z,PW_SCAN
PW_ADMIT:
        LD HL,(PW_ENTRY)
        LD DE,9
        ADD HL,DE
        LD DE,PW_ATTR
        LD B,3
PW_FLAGS:
        LD A,(HL)
        AND 80H
        LD (DE),A
        INC HL
        INC DE
        DJNZ PW_FLAGS
        LD HL,(PW_ENTRY)
        LD DE,11
        ADD HL,DE
        LD A,(HL)
        AND 80H
        LD (PW_ARC),A
        LD HL,PW_REC
        LD DE,OP_DATA+80
        LD BC,80
        LDIR
        XOR A
        LD (OP_DATA+84),A
        LD HL,(PW_ENTRY)
        INC HL
        LD DE,OP_DATA+89
        LD B,11
PW_NAME:
        LD A,(HL)
        AND 7FH
        LD (DE),A
        INC HL
        INC DE
        DJNZ PW_NAME
        LD A,(PW_COPIED)
        OR A
        JR NZ,PW_PRINT
        LD DE,PW_MSG
        CALL PT_PRINT
        LD A,1
        LD (PW_COPIED),A
PW_PRINT:
        LD DE,P_NL
        CALL PT_PRINT
        LD HL,OP_DATA+89
        LD B,11
PW_CHAR:
        LD A,(HL)
        CP ' '
        JR Z,PW_SKIP
        LD A,B
        CP 3
        JR NZ,PW_LETTER
        LD A,'.'
        CALL PW_PUTC
PW_LETTER:
        LD A,(HL)
        CALL PW_PUTC
PW_SKIP:
        INC HL
        DJNZ PW_CHAR
        CALL PT_COPY
        LD A,(PT_STATUS)
        OR A
        JP Z,PW_SCAN
        JR PW_EXIT
PW_PUTC:
        PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL 5
        POP BC
        POP HL
        RET
PW_END:
        LD A,(PW_COPIED)
        OR A
        JR NZ,PW_NL
        LD DE,PW_NONE
        CALL P_ERROR
        JR PW_EXIT
PW_NL:
        LD DE,P_NL
        CALL PT_PRINT
PW_EXIT:
        XOR A
        LD (PW_ACTIVE),A
        JP PT_RESTORE
PW_ACTIVE: DB 0
PW_ARC: DB 0
PW_ATTR: DS 3
PW_EXM: DB 0
PW_COPIED: DB 0
PW_SLOT: DB 0
PW_NEXT: DW 0
PW_INDEX: DW 0
PW_ENTRY: DW 0
PW_REC: DS 80
PW_FCB: DS 36
PW_DMA: DS 128
PW_MSG: DB 'COPYING -$'
PW_NONE: DB 'NOT FOUND',13,10,'$'
