; One PIP operand. HL/B span; capture defaults in P_DRIVE/P_USER.
; Result is OP_REC: type/device/drive/user/ambiguous/explicit-user/parameters,
; then a 36-byte FCB, 26 parameter bytes and S/Q pointer/length descriptors.
PO_PARSE:
        LD (PO_PTR),HL
        LD A,B
        LD (PO_LEFT),A
        LD HL,OP_REC
        LD B,80
        XOR A
PO_ZERO:
        LD (HL),A
        INC HL
        DJNZ PO_ZERO
        LD HL,OP_REC+9
        LD B,11
        LD A,' '
PO_PAD:
        LD (HL),A
        INC HL
        DJNZ PO_PAD
        LD A,(P_DRIVE)
        LD (OP_REC+2),A
        LD A,(P_USER)
        LD (OP_REC+3),A
        LD HL,(PO_PTR)
        LD A,(PO_LEFT)
        LD B,A
        LD C,0
PO_PREFIX:
        LD A,B
        OR A
        JR Z,PO_UNQUAL
        LD A,(HL)
        CP ':'
        JR Z,PO_COLON
        CP '.'
        JR Z,PO_UNQUAL
        CP '['
        JR Z,PO_UNQUAL
        INC C
        INC HL
        DJNZ PO_PREFIX
PO_UNQUAL:
        LD HL,(PO_PTR)
        LD A,(PO_LEFT)
        LD B,A
        JP PO_FILE
PO_COLON:
        LD A,C
        CP 3
        JR NZ,PO_DU
        PUSH HL
        PUSH BC
        LD DE,PO_DEVS
        LD A,0
        LD (PO_DEVNO),A
PO_DEVICE:
        LD HL,(PO_PTR)
        LD B,3
PO_DEVCMP:
        LD A,(HL)
        CALL PO_UP
        LD C,A
        LD A,(DE)
        CP C
        JR NZ,PO_DEVMISS
        INC HL
        INC DE
        DJNZ PO_DEVCMP
        POP BC
        POP HL
        LD A,(PO_DEVNO)
        LD (OP_REC+1),A
        LD A,4
        LD (OP_REC),A
        INC HL
        DEC B
        JP PO_PARAMS
PO_DEVMISS:
        ; DE may have advanced zero, one or two bytes.
        LD A,B
        LD C,A
        LD B,0
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD HL,PO_DEVNO
        INC (HL)
        LD A,(HL)
        CP 21
        JR NZ,PO_DEVICE
        POP BC
        POP HL
PO_DU:
        PUSH HL
        PUSH BC
        LD HL,(PO_PTR)
        LD B,C
        LD A,B
        OR A
        JP Z,PO_BADPOP
        LD A,(HL)
        CALL PO_UP
        CP 'A'
        JR C,PO_USER
        CP 'P'+1
        JP NC,PO_BADPOP
        SUB 'A'
        LD (OP_REC+2),A
        INC HL
        DEC B
        JR Z,PO_DUDONE
PO_USER:
        LD A,B
        CP 3
        JP NC,PO_BADPOP
        XOR A
        LD (PO_NUMBER),A
PO_UNUM:
        LD A,(HL)
        SUB '0'
        CP 10
        JP NC,PO_BADPOP
        LD C,A
        LD A,(PO_NUMBER)
        ADD A,A
        LD E,A
        ADD A,A
        ADD A,A
        ADD A,E
        ADD A,C
        CP 32
        JP NC,PO_BADPOP
        LD (PO_NUMBER),A
        INC HL
        DJNZ PO_UNUM
        LD (OP_REC+3),A
        LD A,1
        LD (OP_REC+5),A
PO_DUDONE:
        POP BC
        POP HL
        INC HL
        DEC B
PO_FILE:
        CALL PO_SPACE
        LD A,3
        LD (OP_REC),A
        LD A,B
        OR A
        JP Z,PO_FINISH
        LD A,(HL)
        CP '['
        JP Z,PO_PARAMS
        LD A,2
        LD (OP_REC),A
        LD IX,OP_REC+9
        LD C,8
        CALL PO_FIELD
        RET C
        LD A,(PO_NLEN)
        OR A
        JP Z,PO_BAD
        LD A,B
        OR A
        JP Z,PO_FINISH
        LD A,(HL)
        CP '.'
        JR NZ,PO_PARAMS
        INC HL
        DEC B
        LD IX,OP_REC+17
        LD C,3
        CALL PO_FIELD
        RET C
        JP PO_PARAMS
PO_FIELD:
        XOR A
        LD (PO_NLEN),A
PO_FCHAR:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        CP ' '
        RET Z
        CP '['
        RET Z
        CP '.'
        RET Z
        LD E,A
        LD A,C
        OR A
        JP Z,PO_BAD
        LD A,E
        CP '*'
        JR Z,PO_STAR
        CALL PO_UP
        CP ':'
        JP Z,PO_BAD
        CP ']'
        JP Z,PO_BAD
        LD (IX+0),A
        CP '?'
        JR NZ,PO_FNEXT
        LD A,1
        LD (OP_REC+4),A
PO_FNEXT:
        INC IX
        INC HL
        DEC B
        DEC C
        LD A,(PO_NLEN)
        INC A
        LD (PO_NLEN),A
        JR PO_FCHAR
PO_STAR:
        LD A,1
        LD (OP_REC+4),A
PO_FILL:
        LD (IX+0),'?'
        INC IX
        LD A,(PO_NLEN)
        INC A
        LD (PO_NLEN),A
        DEC C
        JR NZ,PO_FILL
        INC HL
        DEC B
        JR PO_FCHAR
PO_PARAMS:
        LD A,B
        OR A
        JP Z,PO_FINISH
        LD A,(HL)
        CP ' '
        JR NZ,PO_PATT
        CALL PO_SPACE
        LD A,B
        OR A
        JP Z,PO_FINISH
        LD A,(OP_REC)
        CP 3
        JP NZ,PO_BAD
PO_PATT:
        CALL PO_SPACE
        LD A,B
        OR A
        JP Z,PO_FINISH
        LD A,(HL)
        CP '['
        JP NZ,PO_BAD
        LD A,1
        LD (OP_REC+6),A
        INC HL
        DEC B
PO_PLOOP:
        CALL PO_SPACE
        LD A,B
        OR A
        JP Z,PO_BAD
        LD A,(HL)
        CP ']'
        JP Z,PO_PEND
        CALL PO_UP
        SUB 'A'
        CP 26
        JP NC,PO_BAD
        LD (PO_OPT),A
        INC HL
        DEC B
        CP 'S'-'A'
        JR Z,PO_STRING
        CP 'Q'-'A'
        JR Z,PO_STRING
        LD E,1
        LD A,B
        OR A
        JR Z,PO_VALUE
        LD A,(HL)
        SUB '0'
        CP 10
        JR NC,PO_VALUE
        LD E,0
PO_NUM:
        LD A,(HL)
        SUB '0'
        CP 10
        JR NC,PO_VALUE
        LD C,A
        LD A,(PO_OPT)
        CP 'G'-'A'
        JR NZ,PO_NCALC
        LD A,E
        CP 3
        JP C,PO_NCALC
        JP NZ,PO_BAD
        LD A,C
        CP 2
        JP NC,PO_BAD
PO_NCALC:
        LD A,E
        ADD A,A
        LD D,A
        ADD A,A
        ADD A,A
        ADD A,D
        ADD A,C
        LD E,A
        ; G is bounded, so it cannot wrap an invalid user into a valid one.
        LD A,(PO_OPT)
        CP 'G'-'A'
        JR NZ,PO_NADV
        LD A,E
        CP 32
        JP NC,PO_BAD
PO_NADV:
        INC HL
        DEC B
        JR NZ,PO_NUM
PO_VALUE:
        LD A,(PO_OPT)
        CP 'G'-'A'
        JR NZ,PO_SET
        LD A,(OP_REC+5)
        OR A
        JP NZ,PO_BAD
        LD A,E
        CP 32
        JP NC,PO_BAD
        LD (OP_REC+3),A
PO_SET:
        PUSH HL
        LD A,(PO_OPT)
        LD C,A
        LD D,0
        PUSH BC
        LD B,0
        LD HL,OP_REC+44
        ADD HL,BC
        LD (HL),E
        POP BC
        POP HL
        JP PO_PLOOP
PO_STRING:
        LD A,(PO_OPT)
        CP 'S'-'A'
        LD IX,OP_REC+70
        JR Z,PO_SBEGIN
        LD IX,OP_REC+73
PO_SBEGIN:
        LD (IX+0),L
        LD (IX+1),H
        LD C,0
PO_SCHAR:
        LD A,B
        OR A
        JP Z,PO_BAD
        LD A,(HL)
        CP 01AH
        JR Z,PO_SEND
        INC C
        INC HL
        DEC B
        JR PO_SCHAR
PO_SEND:
        LD A,C
        LD (IX+2),A
        INC HL
        DEC B
        LD E,1
        JR PO_SET
PO_PEND:
        INC HL
        DEC B
        CALL PO_SPACE
        LD A,B
        OR A
        JR NZ,PO_BAD
PO_FINISH:
        LD A,(OP_REC+2)
        INC A
        LD (OP_REC+8),A
        OR A
        RET
PO_BADPOP:
        POP BC
        POP HL
PO_BAD:
        XOR A
        LD (OP_REC),A
        SCF
        RET
PO_SPACE:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        CP ' '
        RET NZ
        INC HL
        DJNZ PO_SPACE
        RET
PO_UP:
        CP 'a'
        RET C
        CP 'z'+1
        RET NC
        AND 05FH
        RET
PO_DEVS: DB 'INPIRDPTRUR1UR2RDROUTLPTUL1PRNLSTPTPUP1UP2PUNTTYCRTUC1CONNULEOF'
PO_PTR: DW 0
PO_LEFT: DB 0
PO_DEVNO: DB 0
PO_NUMBER: DB 0
PO_NLEN: DB 0
PO_OPT: DB 0
OP_REC: DS 80
; Validate and retain every operand before a later transfer engine can act.
OP_PLAN:
        LD A,(PP_COUNT)
        LD (OP_LEFT),A
        LD HL,PP_SPANS
        LD (OP_SCAN),HL
        LD HL,OP_DATA
        LD (OP_OUT),HL
OP_NEXT:
        LD HL,(OP_SCAN)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD (OP_SCAN),HL
        EX DE,HL
        CALL PO_PARSE
        JP C,PP_BAD
        LD HL,OP_REC
        LD DE,(OP_OUT)
        LD BC,80
        LDIR
        LD (OP_OUT),DE
        LD HL,OP_LEFT
        DEC (HL)
        JR NZ,OP_NEXT
        ; Destination restrictions follow DRI PIP's operation dispatch.
        LD A,(OP_DATA)
        CP 4
        JR Z,OP_SINK
        LD A,(OP_DATA+6)
        OR A
        JP NZ,PP_BAD
        LD A,(OP_DATA+4)
        OR A
        JP NZ,PP_BAD
        LD A,(OP_DATA)
        CP 3
        JR NZ,OP_SRCS
        LD A,(PP_COUNT)
        CP 2
        JP NZ,PP_BAD
        LD A,(OP_DATA+80)
        CP 2
        JP NZ,PP_BAD
        JR OP_SRCS
OP_SINK:
        LD A,(OP_DATA+1)
        CP 6
        JP C,PP_BAD
        CP 19
        JP NC,PP_BAD
OP_SRCS:
        LD A,(PP_COUNT)
        DEC A
        LD (OP_LEFT),A
        LD HL,OP_DATA+80
OP_SOURCE:
        LD (OP_SCAN),HL
        LD A,(HL)
        CP 4
        JR Z,OP_DEVICE
        CP 3
        JR Z,OP_LOC
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        OR A
        JR Z,OP_SADV
        LD A,(OP_DATA)
        CP 3
        JP NZ,PP_BAD
        LD A,(PP_COUNT)
        CP 2
        JP NZ,PP_BAD
        JR OP_SADV
OP_LOC:
        LD A,(PP_COUNT)
        CP 2
        JP NZ,PP_BAD
        LD A,(OP_DATA)
        CP 2
        JP NZ,PP_BAD
        ; DEST=DRIVE: inherits the destination's exact filename.
        LD HL,(OP_SCAN)
        LD (HL),2
        LD DE,9
        ADD HL,DE
        EX DE,HL
        LD HL,OP_DATA+9
        LD BC,11
        LDIR
        JR OP_SADV
OP_DEVICE:
        INC HL
        LD A,(HL)
        CP 6
        JR C,OP_SADV
        CP 15
        JP C,PP_BAD
OP_SADV:
        LD HL,(OP_SCAN)
        LD DE,80
        ADD HL,DE
        PUSH HL
        LD HL,OP_LEFT
        DEC (HL)
        POP HL
        JR NZ,OP_SOURCE
        OR A
        RET
OP_LEFT: DB 0
OP_SCAN: DW 0
OP_OUT: DW 0
OP_DATA: DS 5120
