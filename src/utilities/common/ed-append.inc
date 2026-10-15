; A reads at buffer end and restores the original cursor on normal completion.
; On overflow/error, successful reads remain applied and cursor stays at end.
; Source must have been opened and ES_INIT called by the file owner.
EA_RUN:
        LD A,(EC_NEG)
        OR A
        JP Z,EA_START
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP NZ,EC_BAD
EA_START:
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        LD (EA_SAVED),HL
        CALL EB_END
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        LD (EA_HALF),A
EA_LOOP:
        LD A,(EA_HALF)
        OR A
        JP NZ,EA_COUNT
        LD HL,(EB_LIMIT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        SRL H
        RR L
        LD DE,(EB_FIRST)
        ADD HL,DE
        LD DE,(EB_FRONT)
        OR A
        SBC HL,DE
        JP C,EA_DONE
        JP Z,EA_DONE
        JP EA_LINE
EA_COUNT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,EA_DONE
        DEC HL
        LD (EC_COUNT),HL
EA_LINE:
        LD HL,(EB_FRONT)
        LD DE,(EB_BACK)
        OR A
        SBC HL,DE
        JP Z,EC_FULL              ; do not consume the byte that cannot fit
        CALL ES_GET
        JP NC,EA_CHAR
        CP 1
        JP Z,EA_DONE
        LD (EA_ERROR),A
        LD A,'?'
        SCF
        RET
EA_CHAR:
        LD C,A
        LD A,(EC_UPPER)
        OR A
        LD A,C
        CALL NZ,EI_UP
        LD C,A
        CALL EB_PUT
        LD A,C
        CP 10
        JP NZ,EA_LINE
        JP EA_LOOP
EA_DONE:
        LD HL,(EB_FIRST)
        LD DE,(EA_SAVED)
        ADD HL,DE
        LD (EA_TARGET),HL
EA_BACK:
        LD HL,(EB_FRONT)
        LD DE,(EA_TARGET)
        OR A
        SBC HL,DE
        RET Z
        CALL EB_LEFT
        JP EA_BACK
EA_SAVED: DW 0
EA_TARGET: DW 0
EA_HALF: DB 0
EA_ERROR: DB 0
