; F string collection/search. Literal bytes only; no wildcard or regex grammar.
; Scratch capacity follows DRI's 100-byte overflow threshold (99 usable bytes).
EG_RUN:
        CALL EG_PREP
        RET C
        CALL EG_COLLECT
        RET C
        LD A,(EG_LEN)
        LD (EG_PATTERN),A
        JP EG_REPEAT
EG_PREP:
        LD A,(EC_NEG)
        OR A
        JP Z,EG_SETUP
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP NZ,EC_BAD
EG_SETUP:
        LD A,(EC_RAW)
        CP 'a'
        JP C,EG_UPCASE
        CP 'z'+1
        JP C,EG_LOWCASE
EG_UPCASE:
        LD A,1
        JP EG_CASE
EG_LOWCASE:
        LD A,(EC_UPPER)
EG_CASE:
        LD (EG_UPPER),A
        XOR A
        LD (EG_LEN),A
        LD (EG_OFFSET),A
        LD (EG_REVERSE),A
        RET
EG_COLLECT:
        CALL EC_GET
        LD (EC_WHERE),A
        CP 26
        JP Z,EG_ENDSTR
        CP 13
        JP Z,EG_ENDSTR
        OR A
        JP Z,EC_BAD
        CP 12
        JP Z,EG_CRLF
        LD C,A
        LD A,(EG_UPPER)
        OR A
        LD A,C
        CALL NZ,EI_UP
        CALL EG_PUT
        RET C
        JP EG_COLLECT
EG_CRLF:
        LD A,13
        CALL EG_PUT
        RET C
        LD A,10
        CALL EG_PUT
        RET C
        JP EG_COLLECT
EG_ENDSTR:
        XOR A
        RET
EG_PUT:
        LD (EC_WHERE),A
        LD C,A
        LD A,(EG_LEN)
        LD E,A
        LD D,0
        LD HL,EG_TEXT
        ADD HL,DE
        LD (HL),C
        INC A
        LD (EG_LEN),A
        CP 100
        JP NC,EC_FULL
        XOR A
        RET
EG_REPEAT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (EC_COUNT),HL
        CALL EG_FIND
        RET C
        JP EG_REPEAT
; Nonmoving failed search. On success move through the complete match.
EG_FIND:
        LD HL,(EB_BACK)
EG_CAND:
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        JP NC,EG_MISS
        ADD HL,DE
        LD (EG_START),HL
        PUSH HL
        LD A,(EG_OFFSET)
        LD L,A
        LD H,0
        LD DE,EG_TEXT
        ADD HL,DE
        EX DE,HL
        POP HL
        LD A,(EG_PATTERN)
        LD B,A
        OR A
        JP Z,EG_FOUND
EG_COMPARE:
        PUSH DE
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        POP DE
        JP NC,EG_ADVANCE
        PUSH DE
        LD DE,(EB_LIMIT)
        ADD HL,DE
        POP DE
        LD A,(DE)
        CP (HL)
        JP NZ,EG_ADVANCE
        INC DE
        INC HL
        DJNZ EG_COMPARE
EG_FOUND:
        LD (EG_TARGET),HL
        LD A,(EG_REVERSE)
        OR A
        JP NZ,EG_BACKMODE
EG_MOVE:
        LD HL,(EB_BACK)
        LD DE,(EG_TARGET)
        OR A
        SBC HL,DE
        RET Z
        CALL EB_RIGHT
        JP EG_MOVE
; DRI counted J deliberately retains DIRECTION/FIRST between FIND calls.
; FIRST is a logical unsigned offset; preserve its wraparound semantics.
EG_BACKMODE:
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        LD DE,(EG_FIRST)
        OR A
        SBC HL,DE
        JP C,EG_BACKDONE
        JP Z,EG_BACKDONE
        CALL EB_LEFT
        JP EG_BACKMODE
EG_BACKDONE:
        XOR A
        RET
EG_ADVANCE:
        LD HL,(EG_START)
        INC HL
        JP EG_CAND
EG_MISS:
        LD A,'#'
        SCF
        RET
EG_UPPER: DB 0
EG_LEN: DB 0
EG_PATTERN: DB 0
EG_OFFSET: DB 0
EG_REVERSE: DB 0
EG_FIRST: DW 0
EG_START: DW 0
EG_TARGET: DW 0
EG_TEXT: DS 100
