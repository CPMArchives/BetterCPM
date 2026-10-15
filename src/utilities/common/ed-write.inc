; W removes accepted bytes from buffer start; source stream is unaffected.
; Restore surviving portion of original cursor on success. On failure remain
; at the first unaccepted byte, with earlier output retained by EW stream.
EX_RUN:
        LD A,(EC_NEG)
        OR A
        JP Z,EX_START
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP NZ,EC_BAD
EX_START:
        XOR A
        LD (EX_ERROR),A
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        LD (EX_CURSOR),HL
        CALL EB_TOP
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        LD (EX_HALF),A
EX_LINE:
        LD A,(EX_HALF)
        OR A
        JP NZ,EX_COUNT
        LD HL,(EB_LIMIT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        SRL H
        RR L
        LD B,H
        LD C,L
        LD HL,(EB_LIMIT)
        LD DE,(EB_BACK)
        OR A
        SBC HL,DE
        OR A
        SBC HL,BC
        JP C,EX_DONE
        JP Z,EX_DONE
        JP EX_BYTE
EX_COUNT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,EX_DONE
        DEC HL
        LD (EC_COUNT),HL
EX_BYTE:
        LD HL,(EB_BACK)
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        JP Z,EX_DONE
        LD HL,(EB_BACK)
        LD C,(HL)
        LD A,C
        LD (EX_CHAR),A
        CALL EW_PUT
        JP C,EX_FAIL
        CALL EB_DEL
        LD HL,(EX_CURSOR)
        LD A,H
        OR L
        JP Z,EX_NEXT
        DEC HL
        LD (EX_CURSOR),HL
EX_NEXT:
        LD A,(EX_CHAR)
        CP 10
        JP NZ,EX_BYTE
        LD HL,(EB_BASE)
        INC HL
        LD (EB_BASE),HL
        JP EX_LINE
EX_DONE:
        LD HL,(EX_CURSOR)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (EX_CURSOR),HL
        CALL EB_RIGHT
        JP C,EX_OK
        JP EX_DONE
EX_OK:
        XOR A
        RET
EX_FAIL:
        LD (EX_ERROR),A
        LD A,'?'
        SCF
        RET
EX_CURSOR: DW 0
EX_HALF: DB 0
EX_CHAR: DB 0
EX_ERROR: DB 0
