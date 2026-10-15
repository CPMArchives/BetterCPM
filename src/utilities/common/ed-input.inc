; Interactive insert core. Driver obtains echoed characters with BDOS 1,
; then calls IN_FEED with C. Return A=0 continue, A=1 Ctrl-Z completion;
; carry means command error/overflow. Text edits remain on failure.
IN_START:
        CALL IN_LINE
        CALL IN_PREFIX
        LD A,(ET_COL)
        LD (IN_SCOL),A
        XOR A
        RET
IN_FEED:
        LD A,C
        LD D,A
        LD A,(EC_TRANS)
        OR A
        LD A,D
        CALL NZ,EI_UP
        LD C,A
        LD (EC_WHERE),A
        CP 26
        JP Z,IN_END
        OR A
        RET Z
        CP 21
        JP Z,IN_WIPE
        CP 24
        JP Z,IN_CLEAR
        CP 18
        JP Z,IN_RETYPE
        CP 8
        JP Z,IN_BSP
        CP 127
        JP Z,IN_RUB
        CP 13
        JP Z,IN_ENTER
        CP 12
        JP Z,IN_FORM
        CP 10
        JP Z,IN_LF
        CP 9
        JP Z,IN_TAB
        CP 32
        JP C,IN_CONTROL
        LD A,(ET_COL)
        INC A
        LD (ET_COL),A
        LD A,C
        LD D,A
        LD A,(EC_TRANS)
        OR A
        LD A,D
        CALL NZ,EI_UP
        LD C,A
        JP IN_PUT
IN_TAB:
        LD A,(ET_COL)
        OR 7
        INC A
        LD (ET_COL),A
        JP IN_PUT
IN_CONTROL:
        PUSH BC
        LD A,'^'
        CALL ET_TTY
        POP BC
        LD A,C
        ADD A,'@'
        CALL ET_TTY
        JP IN_PUT
IN_FORM:
        LD A,'^'
        CALL ET_TTY
        LD A,'L'
        CALL ET_TTY
        LD C,13
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD C,10
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        JP IN_NEWLINE
IN_ENTER:
        LD C,13
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD A,10
        CALL ET_TTY
IN_LF:
        LD C,10
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
IN_NEWLINE:
        CALL IN_LINE
        CALL IN_PREFIX
        XOR A
        RET
IN_PUT:
        CALL EB_PUT
        JP C,EC_FULL
        XOR A
        RET
IN_RANGE:
        LD HL,0
        LD (EC_COUNT),HL
        LD A,1
        LD (EC_NEG),A
        RET
IN_WIPE:
        CALL IN_RANGE
        CALL EL_KILL
        CALL IN_CRLF
        CALL IN_LINE
        CALL IN_PREFIX
        XOR A
        RET
IN_CLEAR:
        CALL IN_RANGE
        CALL EL_KILL
IN_BACKLOOP:
        LD A,(IN_SCOL)
        LD B,A
        LD A,(ET_COL)
        CP B
        JP C,IN_CONT
        JP Z,IN_CONT
        CALL IN_BACKSPACE
        JP IN_BACKLOOP
IN_RETYPE:
        CALL IN_CRLF
        CALL IN_RANGE
        CALL ET_TYPE
        RET C
IN_CONT:
        XOR A
        RET
IN_RUB:
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        JP Z,EC_BAD
        LD HL,(EB_FRONT)
        DEC HL
        LD A,(HL)
        PUSH AF
        CALL EB_ERASE
        POP AF
        CALL ET_PRINT
        JP IN_CONT
IN_BSP:
        LD A,(ET_COL)
        LD (IN_OLD),A
        OR A
        JP Z,IN_CONT
        LD A,' '
        CALL ET_TTY
        LD A,(IN_SCOL)
        LD B,A
        LD A,(IN_OLD)
        CP B
        JP C,IN_BDONE
        JP Z,IN_BDONE
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        JP Z,IN_BDONE
        LD HL,(EB_FRONT)
        DEC HL
        LD A,(HL)
        CP 10
        JP Z,IN_BDONE
        CALL EB_ERASE
        XOR A
        LD (ET_COL),A
        INC A
        LD (ET_MUTE),A
        CALL IN_RANGE
        CALL ET_TYPE
        PUSH AF
        XOR A
        LD (ET_MUTE),A
        POP AF
        RET C
        LD A,(ET_COL)
        LD B,A
        LD A,(IN_SCOL)
        CP B
        JP C,IN_QSET
        LD B,A
IN_QSET:
        LD A,B
        LD (IN_QCOL),A
        LD A,(IN_OLD)
        LD (ET_COL),A
IN_BLOOP:
        LD A,(IN_QCOL)
        LD B,A
        LD A,(ET_COL)
        CP B
        JP C,IN_BKEEP
        JP Z,IN_BKEEP
        CALL IN_BACKSPACE
        JP IN_BLOOP
IN_BKEEP:
        LD A,(ET_COL)
        LD (IN_OLD),A
IN_BDONE:
        LD A,(IN_OLD)
        LD (ET_COL),A
        JP IN_CONT
IN_BACKSPACE:
        LD A,8
        CALL ET_TTY
        LD A,' '
        CALL ET_TTY
        LD A,8
        CALL ET_TTY
        LD A,(ET_COL)
        SUB 2
        LD (ET_COL),A
        RET
IN_END:
        LD A,(EC_VERIFY)
        OR A
        CALL NZ,IN_CRLF
        LD A,1
        OR A
        RET
IN_CRLF:
        LD A,13
        CALL ET_TTY
        LD A,10
        JP ET_TTY
IN_LINE:
        LD HL,1
        LD (ET_LINE),HL
        LD HL,(EB_FIRST)
IN_SCAN:
        LD DE,(EB_FRONT)
        OR A
        SBC HL,DE
        ADD HL,DE
        RET Z
        LD A,(HL)
        CP 10
        JP NZ,IN_SCANADV
        PUSH HL
        LD HL,(ET_LINE)
        INC HL
        LD (ET_LINE),HL
        POP HL
IN_SCANADV:
        INC HL
        JP IN_SCAN
IN_PREFIX:
        LD A,(EC_VERIFY)
        OR A
        RET Z
        JP ET_NUMBER
IN_SCOL: DB 0
IN_OLD: DB 0
IN_QCOL: DB 0
