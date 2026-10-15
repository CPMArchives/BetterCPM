; J finds first string, inserts middle string, deletes up to retained last
; string. All three strings share DRI's bounded scratch region.
GJ_RUN:
        CALL EG_PREP
        RET C
        CALL EG_COLLECT
        RET C
        LD A,(EG_LEN)
        LD (GJ_FIRST),A
        CALL EG_COLLECT
        RET C
        LD A,(EG_LEN)
        LD (GJ_MIDDLE),A
        CALL EG_COLLECT
        RET C
GJ_REPEAT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (EC_COUNT),HL
        XOR A
        LD (EG_OFFSET),A
        LD A,(GJ_FIRST)
        LD (EG_PATTERN),A
        CALL EG_FIND
        RET C
        LD A,(GJ_FIRST)
        LD (GJ_POS),A
GJ_INSERT:
        LD A,(GJ_POS)
        LD B,A
        LD A,(GJ_MIDDLE)
        CP B
        JP Z,GJ_LAST
        LD E,B
        LD D,0
        LD HL,EG_TEXT
        ADD HL,DE
        LD C,(HL)
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD A,(GJ_POS)
        INC A
        LD (GJ_POS),A
        JP GJ_INSERT
GJ_LAST:
        LD HL,(EB_FRONT)
        LD (GJ_ANCHOR),HL
        LD A,(GJ_MIDDLE)
        LD (EG_OFFSET),A
        LD B,A
        LD A,(EG_LEN)
        SUB B
        LD (EG_PATTERN),A
        CALL EG_FIND
        RET C
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        LD A,(EG_PATTERN)
        LD E,A
        LD D,0
        OR A
        SBC HL,DE
        LD (EG_FIRST),HL
        LD A,1
        LD (EG_REVERSE),A
        CALL EG_BACKMODE
GJ_DELETE:
        LD HL,(GJ_ANCHOR)
        LD (EB_FRONT),HL
        JP GJ_REPEAT
GJ_FIRST: DB 0
GJ_MIDDLE: DB 0
GJ_POS: DB 0
GJ_ANCHOR: DW 0
