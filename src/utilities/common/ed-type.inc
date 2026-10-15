; T selects the same signed line range as L, but restores the cursor before
; output. Logical byte lookup crosses the gap without flattening the buffer.
ET_TYPE:
        LD HL,(EB_FRONT)
        LD (ET_ORIG),HL
        CALL EL_MOVE
        LD HL,(EB_FRONT)
        LD DE,(ET_ORIG)
        LD A,(EC_NEG)
        OR A
        JP NZ,ET_RANGE
        EX DE,HL
ET_RANGE:
        LD (ET_PTR),HL
        LD (ET_LAST),DE
ET_RESTORE:
        LD HL,(EB_FRONT)
        LD DE,(ET_ORIG)
        OR A
        SBC HL,DE
        JP Z,ET_READY
        JP C,ET_RIGHT
        CALL EB_LEFT
        JP ET_RESTORE
ET_RIGHT:
        CALL EB_RIGHT
        JP ET_RESTORE
ET_READY:
        LD HL,(EB_BASE)
        LD (ET_LINE),HL
        LD A,10
        LD (ET_PREV),A
        LD HL,(EB_FIRST)
ET_SCAN:
        LD DE,(ET_PTR)
        OR A
        SBC HL,DE
        ADD HL,DE
        JP Z,ET_CHECK
        CALL ET_GET
        LD (ET_PREV),A
        CP 10
        JP NZ,ET_SCANADV
        PUSH HL
        LD HL,(ET_LINE)
        INC HL
        LD (ET_LINE),HL
        POP HL
ET_SCANADV:
        INC HL
        JP ET_SCAN
ET_CHECK:
        LD HL,(ET_PTR)
        LD DE,(ET_LAST)
        OR A
        SBC HL,DE
        JP Z,ET_DONE
        LD A,(ET_PREV)
        CP 10
        JP NZ,ET_LOOP
        LD A,(ET_COL)
        OR A
        JP Z,ET_LOOP
        LD A,13
        CALL ET_PRINT
        LD A,10
        CALL ET_PRINT
ET_LOOP:
        LD HL,(ET_PTR)
        LD DE,(ET_LAST)
        OR A
        SBC HL,DE
        JP Z,ET_DONE
        LD A,(ET_PREV)
        CP 10
        JP NZ,ET_BODY
        LD A,(EC_VERIFY)
        OR A
        CALL NZ,ET_NUMBER
        LD C,11
        CALL 5
        OR A
        JP Z,ET_BODY
        LD C,1
        CALL 5
        LD A,'#'
        SCF
        RET
ET_BODY:
        LD HL,(ET_PTR)
        CALL ET_GET
        LD (ET_PREV),A
        CALL ET_PRINT
        LD A,(ET_PREV)
        CP 10
        JP NZ,ET_ADV
        LD HL,(ET_LINE)
        INC HL
        LD (ET_LINE),HL
ET_ADV:
        LD HL,(ET_PTR)
        INC HL
        LD (ET_PTR),HL
        JP ET_LOOP
ET_DONE:
        OR A
        RET
ET_GET:
        PUSH HL
        LD DE,(EB_FRONT)
        OR A
        SBC HL,DE
        POP HL
        JP C,ET_DIRECT
        PUSH HL
        LD DE,(EB_BACK)
        ADD HL,DE
        LD DE,(EB_FRONT)
        OR A
        SBC HL,DE
        LD A,(HL)
        POP HL
        RET
ET_DIRECT:
        LD A,(HL)
        RET
; DRI ED's display convention: tabs expand, CR/LF pass, other C0 use ^X.
ET_PRINT:
        CP 9
        JP Z,ET_TAB
        CP 13
        JP Z,ET_TTY
        CP 10
        JP Z,ET_TTY
        CP 32
        JP NC,ET_TTY
        PUSH AF
        LD A,'^'
        CALL ET_TTY
        POP AF
        ADD A,'@'
        JP ET_TTY
ET_TAB:
        LD A,(ET_COL)
        AND 7
        LD B,A
        LD A,8
        SUB B
        LD B,A
ET_SPACE:
        LD A,' '
        CALL ET_TTY
        DJNZ ET_SPACE
        RET
ET_TTY:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        CP 10
        JP NZ,ET_COLUMN
        XOR A
        LD (ET_COL),A
        JP ET_EMIT
ET_COLUMN:
        CP 32
        JP C,ET_EMIT
        LD A,(ET_COL)
        INC A
        LD (ET_COL),A
ET_EMIT:
        LD A,(ET_MUTE)
        OR A
        JP NZ,ET_RETURN
        LD C,2
        CALL 5
ET_RETURN:
        POP HL
        POP DE
        POP BC
        POP AF
        RET
ET_NUMBER:
        CALL ET_DECIMAL
        LD A,':'
        CALL ET_TTY
        LD A,' '
        CALL ET_TTY
        LD A,(ET_LABEL)
        JP ET_TTY
ET_DECIMAL:
        LD HL,(ET_LINE)
        LD DE,ET_POWERS
        LD (ET_DIV),DE
        LD B,5
        XOR A
        LD (ET_LEAD),A
ET_DIGIT:
        PUSH HL
        LD HL,(ET_DIV)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD (ET_DIV),HL
        POP HL
        LD C,0
ET_SUB:
        OR A
        SBC HL,DE
        JP C,ET_DIGDONE
        INC C
        JP ET_SUB
ET_DIGDONE:
        ADD HL,DE
        LD A,C
        OR A
        JP NZ,ET_NONZERO
        LD A,(ET_LEAD)
        OR A
        LD A,' '
        JP Z,ET_DIGOUT
ET_NONZERO:
        LD A,1
        LD (ET_LEAD),A
        LD A,C
        ADD A,'0'
ET_DIGOUT:
        CALL ET_TTY
        DJNZ ET_DIGIT
        RET
ET_POWERS: DW 10000,1000,100,10,1
ET_ORIG: DW 0
ET_PTR: DW 0
ET_LAST: DW 0
ET_LINE: DW 0
ET_DIV: DW 0
ET_PREV: DB 0
ET_COL: DB 0
ET_LEAD: DB 0

ET_MUTE: DB 0

ET_LABEL: DB 32
