; Expanded PIP source scopes. OP_REC+7 marks a selector operand.
; Ordinary operands retain the historical parser. Only brackets before the
; location colon invoke DU_PARSE; trailing S/Q strings remain literal data.
PS_PARSE:
        LD (PS_INPUT),HL
        LD A,B
        LD (PS_LENGTH),A
PS_PREFIX:
        LD A,B
        OR A
        JP Z,PS_PLAIN
        LD A,(HL)
        CP ':'
        JP Z,PS_PLAIN
        CP '.'
        JP Z,PS_PLAIN
        CP ' '
        JP Z,PS_PLAIN
        CP '['
        JR Z,PS_BRACKET
        INC HL
        DJNZ PS_PREFIX
PS_PLAIN:
        LD HL,(PS_INPUT)
        LD A,(PS_LENGTH)
        LD B,A
        JP PO_PARSE
PS_BRACKET:
        ; A filename before '[' means historical parameters, not a selector.
        ; Legal selector prefixes are empty or a single drive letter.
        LD DE,(PS_INPUT)
        OR A
        SBC HL,DE
        LD A,H
        OR A
        JP NZ,PS_PLAIN
        LD A,L
        CP 2
        JP NC,PS_PLAIN
        OR A
        JR Z,PS_SCOPE
        ; A one-character filename may also precede historical parameters.
        LD HL,(PS_INPUT)
        INC HL
        INC HL
        LD A,(HL)
        CP '-'
        JR Z,PS_SCOPE
        CP '0'
        JP C,PS_PLAIN
        CP '9'+1
        JP NC,PS_PLAIN
PS_SCOPE:
        LD HL,(PS_INPUT)
        LD A,(PS_LENGTH)
        LD B,A
        LD A,(P_DRIVE)
        LD D,A
        LD A,(P_USER)
        LD E,A
        CALL DU_PARSE
        RET C
        LD (PS_FILE),HL
        LD A,B
        LD (PS_FLEN),A
        LD BC,0
        CALL DU_NEXT
        RET C
        ; Parse the remainder with the selected DU, without changing caller defaults.
        LD HL,(PS_FILE)
        LD A,(PS_FLEN)
        LD B,A
        CALL PO_PARSE
        RET C
        LD A,(OP_REC)
        CP 2
        JP NZ,PO_BAD
        ; G cannot redirect an explicitly selected source scope, even G0.
        ; PS_GSEEN records parameter presence even when its value is zero.
        LD BC,0
        CALL DU_NEXT
        LD A,D
        LD (OP_REC+2),A
        INC A
        LD (OP_REC+8),A
        LD A,E
        LD (OP_REC+3),A
        LD A,(PS_GSEEN)
        OR A
        JP NZ,PO_BAD
        LD A,1
        LD (OP_REC+5),A
        LD (OP_REC+7),A
        OR A
        RET
PS_PLAN:
        LD A,(OP_DATA+7)
        OR A
        JR NZ,PS_BAD
        LD A,(PP_COUNT)
        DEC A
        LD B,A
        LD HL,OP_DATA+87
PS_FLAGS:
        LD A,(HL)
        OR A
        JR NZ,PS_SELECTED
        LD DE,80
        ADD HL,DE
        DJNZ PS_FLAGS
        OR A
        RET
PS_SELECTED:
        LD A,(PP_COUNT)
        CP 2
        JR NZ,PS_BAD
        LD A,(OP_DATA)
        CP 3
        JR NZ,PS_BAD
        OR A
        RET
PS_BAD:
        SCF
        RET

; Freeze at most 64 admitted sources before any transfer-file mutation.
; The unused operand slots hold records: drive,user,name[11],attributes[3].
PS_START:
        XOR A
        LD (PS_COUNT),A
        LD (PW_ACTIVE),A
        LD (PB_COUNT),A
        LD (PB_ABORT),A
        LD HL,OP_DATA+80
        LD DE,PS_REC
        LD BC,80
        LDIR
        LD BC,0
PS_DOMAIN:
        CALL DU_NEXT
        JR C,PS_DOMDONE
        LD A,D
        CP 4
        JP NC,PS_DRIVE
        JR PS_DOMAIN
PS_DOMDONE:
        ; Reuse parameter validation without comparing uninitialized per-file FCBs.
        ; Identity is checked against every admitted file by PS_ADD instead.
        XOR A
        LD (OP_DATA+84),A
        LD (PI_ACTIVE),A
        LD (PD_ACTIVE),A
        LD (PF_COL),A
        CALL PN_INIT
        LD A,1
        LD (PS_CHECK),A
        CALL PC_CHECK
        PUSH AF
        XOR A
        LD (PS_CHECK),A
        POP AF
        OR A
        JP NZ,PS_FORMAT
        LD A,(OP_DATA+2)
        CP 4
        JP NC,PS_DRIVE
        CALL PT_DEST
        LD C,29
        CALL 5
        LD A,(OP_DATA+2)
        LD B,A
        INC B
PS_RO:
        LD A,L
        RRCA
        LD L,A
        DJNZ PS_RO
        AND 80H
        JP NZ,PS_READONLY
        LD BC,0
PS_LOCATION:
        CALL DU_NEXT
        JP C,PS_READY
        LD (PS_NEXT),BC
        LD A,D
        LD (PS_REC+2),A
        INC A
        LD (PS_REC+8),A
        LD A,E
        LD (PS_REC+3),A
        CALL PT_SETDU
        LD C,31
        CALL 5
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        LD (PW_EXM),A
        LD HL,PS_REC+8
        LD DE,PW_FCB
        LD BC,36
        LDIR
        LD A,'?'
        LD (PW_FCB+12),A
        LD DE,PW_DMA
        LD C,26
        CALL 5
        LD DE,PW_FCB
        LD C,17
        CALL 5
PS_RESULT:
        CP 0FFH
        JR Z,PS_NEXTDU
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
        LD (PS_ENTRY),HL
        LD DE,14
        ADD HL,DE
        LD A,(HL)
        AND 3FH
        JR NZ,PS_SEARCH
        DEC HL
        DEC HL
        LD A,(HL)
        AND 1FH
        LD B,A
        LD A,(PW_EXM)
        CP B
        JR C,PS_SEARCH
        DEC HL
        DEC HL
        LD A,(HL)
        AND 80H
        JR Z,PS_ADMIT
        LD A,(PS_REC+61)
        OR A
        JR Z,PS_SEARCH
PS_ADMIT:
        CALL PS_ADD
        JP C,PS_ABORT
PS_SEARCH:
        LD C,18
        CALL 5
        JR PS_RESULT
PS_NEXTDU:
        LD BC,(PS_NEXT)
        JP PS_LOCATION

PS_ADD:
        LD A,(PS_REC+2)
        LD (PS_ITEM),A
        LD A,(PS_REC+3)
        LD (PS_ITEM+1),A
        LD HL,(PS_ENTRY)
        INC HL
        LD DE,PS_ITEM+2
        LD B,11
PS_NAME:
        LD A,(HL)
        AND 7FH
        LD (DE),A
        INC HL
        INC DE
        DJNZ PS_NAME
        LD HL,(PS_ENTRY)
        LD DE,9
        ADD HL,DE
        LD DE,PS_ITEM+13
        LD B,3
PS_ATTR:
        LD A,(HL)
        AND 80H
        LD (DE),A
        INC HL
        INC DE
        DJNZ PS_ATTR
        ; Same DU implies a self-copy for a bare-DU destination.
        LD A,(PS_ITEM)
        LD HL,OP_DATA+2
        CP (HL)
        JR NZ,PS_STAGE
        LD A,(PS_ITEM+1)
        INC HL
        CP (HL)
        JP Z,PS_IDENT
PS_STAGE:
        LD HL,PS_ITEM+10
        LD B,3
PS_DOLLAR:
        LD A,(HL)
        CP '$'
        JR NZ,PS_UNIQUE
        INC HL
        DJNZ PS_DOLLAR
        JP PS_IDENT
PS_UNIQUE:
        LD A,(PS_COUNT)
        LD B,A
        LD HL,OP_DATA+160
PS_COMPARE:
        LD A,B
        OR A
        JR Z,PS_APPEND
        PUSH BC
        PUSH HL
        INC HL
        INC HL
        LD DE,PS_ITEM+2
        CALL PT_EQUAL
        POP HL
        POP BC
        JP Z,PS_DUPLICATE
        LD DE,16
        ADD HL,DE
        DJNZ PS_COMPARE
PS_APPEND:
        LD A,(PS_COUNT)
        CP 64
        JR NC,PS_LIMIT
        LD DE,PS_ITEM
        EX DE,HL
        LD BC,16
        LDIR
        LD HL,PS_COUNT
        INC (HL)
        OR A
        RET
PS_IDENT:
        LD DE,PT_IDMSG
        JR PS_ADDERR
PS_LIMIT:
        LD DE,PS_FULLMSG
PS_ADDERR:
        CALL PT_PRINT
        SCF
        RET
PS_DUPLICATE:
        PUSH HL
        LD DE,PS_DUPMSG
        CALL PT_PRINT
        LD HL,PS_ITEM
        CALL PS_SHOW
        LD DE,PS_ANDMSG
        CALL PT_PRINT
        POP HL
        CALL PS_SHOW
        LD DE,P_NL
        CALL PT_PRINT
        SCF
        RET
; Show one source record, preserving no registers. Fixed-width 8.3 is intentional.
PS_SHOW:
        LD (PS_SHOWPTR),HL
        LD A,(HL)
        ADD A,'A'
        CALL PS_PUTC
        LD HL,(PS_SHOWPTR)
        INC HL
        LD A,(HL)
        LD B,'0'
PS_TENS:
        CP 10
        JR C,PS_DIGITS
        SUB 10
        INC B
        JR PS_TENS
PS_DIGITS:
        PUSH AF
        LD A,B
        CP '0'
        CALL NZ,PS_PUTC
        POP AF
        ADD A,'0'
        CALL PS_PUTC
        LD A,':'
        CALL PS_PUTC
        LD HL,(PS_SHOWPTR)
        INC HL
        INC HL
        LD B,11
PS_LETTERS:
        LD A,B
        CP 3
        LD A,'.'
        CALL Z,PS_PUTC
        LD A,(HL)
        CP ' '
        CALL NZ,PS_PUTC
        INC HL
        DJNZ PS_LETTERS
        RET
PS_PUTC:
        PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL 5
        POP BC
        POP HL
        RET

PS_READY:
        LD A,(PS_COUNT)
        OR A
        JP Z,PS_EMPTY
        ; Probe every staging file before copying, so a later RO staging file
        ; cannot cause an avoidable partial operation. Writable staging follows PIP.
        LD HL,OP_DATA+160
        LD (PS_CURSOR),HL
        LD A,(PS_COUNT)
        LD (PS_LEFT),A
PS_PROBE:
        CALL PS_LOAD
        LD HL,OP_DATA+89
        LD DE,PT_TFCB+1
        LD BC,11
        LDIR
        LD A,(OP_DATA+8)
        LD (PT_TFCB),A
        LD HL,PT_TFCB+9
        LD B,3
PS_TEMPEXT:
        LD (HL),'$'
        INC HL
        DJNZ PS_TEMPEXT
        LD B,24
        XOR A
PS_TEMPZERO:
        LD (HL),A
        INC HL
        DJNZ PS_TEMPZERO
        CALL PT_DEST
        LD DE,PT_TFCB
        LD C,15
        CALL 5
        CP 0FFH
        JR Z,PS_PDONE
        LD A,(PT_TFCB+9)
        AND 80H
        JP NZ,PS_TEMPFAIL
PS_PDONE:
        CALL PS_ADVANCE
        JR NZ,PS_PROBE
        LD HL,OP_DATA+160
        LD (PS_CURSOR),HL
        LD A,(PS_COUNT)
        LD (PS_LEFT),A
        LD DE,PW_MSG
        CALL PT_PRINT
        LD DE,P_NL
        CALL PT_PRINT
PS_COPY:
        CALL PS_LOAD
        LD HL,(PS_CURSOR)
        CALL PS_SHOW
        LD DE,P_NL
        CALL PT_PRINT
        LD A,1
        LD (PW_ACTIVE),A
        CALL PT_COPY
        LD A,(PT_STATUS)
        OR A
        JR NZ,PS_FINISH
        CALL PS_ADVANCE
        JR NZ,PS_COPY
PS_FINISH:
        XOR A
        LD (PW_ACTIVE),A
        JP PT_RESTORE
PS_LOAD:
        LD HL,PS_REC
        LD DE,OP_DATA+80
        LD BC,80
        LDIR
        LD HL,(PS_CURSOR)
        LD A,(HL)
        LD (OP_DATA+82),A
        INC A
        LD (OP_DATA+88),A
        INC HL
        LD A,(HL)
        LD (OP_DATA+83),A
        INC HL
        LD DE,OP_DATA+89
        LD BC,11
        LDIR
        INC HL
        INC HL
        LD A,(HL)
        LD (PW_ARC),A
        DEC HL
        DEC HL
        LD DE,PW_ATTR
        LD BC,3
        LDIR
        XOR A
        LD (OP_DATA+84),A
        LD (OP_DATA+87),A
        RET
PS_ADVANCE:
        LD HL,(PS_CURSOR)
        LD DE,16
        ADD HL,DE
        LD (PS_CURSOR),HL
        LD HL,PS_LEFT
        DEC (HL)
        RET
PS_FORMAT:
        LD DE,P_INVALID
        JR PS_FAIL
PS_DRIVE:
        LD DE,PT_DRM
        JR PS_FAIL
PS_READONLY:
        LD DE,PT_ROMSG
        JR PS_FAIL
PS_TEMPFAIL:
        LD DE,PT_TMPMSG
        JR PS_FAIL
PS_EMPTY:
        LD DE,PW_NONE
PS_FAIL:
        CALL PT_PRINT
PS_ABORT:
        LD DE,PS_NOCOPY
        CALL PT_PRINT
        CALL P_CANCEL
        JP PS_FINISH
PS_INPUT: DW 0
PS_LENGTH: DB 0
PS_FILE: DW 0
PS_FLEN: DB 0
PS_GSEEN: DB 0
PS_CHECK: DB 0
PS_NEXT: DW 0
PS_ENTRY: DW 0
PS_COUNT: DB 0
PS_LEFT: DB 0
PS_CURSOR: DW 0
PS_SHOWPTR: DW 0
PS_REC: DS 80
PS_ITEM: DS 16
DU_MAP: DS 64
DU_WORK: DS 12
PS_DUPMSG: DB 'DUPLICATE DESTINATION NAME: $'
PS_ANDMSG: DB ' conflicts with $'
PS_FULLMSG: DB 'TOO MANY SOURCE FILES (maximum 64)',13,10,'$'
PS_NOCOPY: DB 'No files copied.',13,10,'$'
