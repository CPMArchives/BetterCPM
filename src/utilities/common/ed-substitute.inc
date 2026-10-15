; S uses one shared scratch area for pattern and replacement, as DRI COLLECT.
; A failed later match retains previous substitutions. Overflow retains the
; matched-text removal and replacement bytes that fitted, without rollback.
GS_RUN:
        CALL EG_PREP
        RET C
        CALL EG_COLLECT
        RET C
        LD A,(EG_LEN)
        LD (EG_PATTERN),A
        CALL EG_COLLECT
        RET C
GS_REPEAT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (EC_COUNT),HL
        CALL EG_FIND
        RET C
        LD A,(EG_PATTERN)
        LD B,A
        OR A
        JP Z,GS_REPLACE
GS_REMOVE:
        PUSH BC
        CALL EB_ERASE
        POP BC
        DJNZ GS_REMOVE
GS_REPLACE:
        LD A,(EG_PATTERN)
        LD (GS_POS),A
GS_INSERT:
        LD A,(GS_POS)
        LD B,A
        LD A,(EG_LEN)
        CP B
        JP Z,GS_REPEAT
        LD E,B
        LD D,0
        LD HL,EG_TEXT
        ADD HL,DE
        LD C,(HL)
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD A,(GS_POS)
        INC A
        LD (GS_POS),A
        JP GS_INSERT
GS_POS: DB 0
