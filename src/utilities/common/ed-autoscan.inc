; N searches current suffix, writes the whole buffer on miss, reads a half
; buffer of whole lines and retries at its beginning. No overlap is retained
; between batches: follow DRI autoscan, not a redesigned streaming matcher.
GN_RUN:
        CALL EG_PREP
        RET C
        CALL EG_COLLECT
        RET C
        LD A,(EG_LEN)
        LD (EG_PATTERN),A
GN_REPEAT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (EC_COUNT),HL
GN_FIND:
        CALL EG_FIND
        JP NC,GN_REPEAT
        LD C,11
        CALL 5
        OR A
        JP Z,GN_REFILL
        LD C,1
        CALL 5
        JP EG_MISS
GN_REFILL:
        LD HL,(EC_COUNT)
        LD (GN_COUNT),HL
        LD HL,0FFFFH
        LD (EC_COUNT),HL
        XOR A
        LD (EC_NEG),A
        CALL EX_RUN
        RET C
        LD HL,0
        LD (EC_COUNT),HL
        CALL EA_RUN
        RET C
        CALL EB_TOP
        LD HL,(GN_COUNT)
        LD (EC_COUNT),HL
        LD HL,(EB_BACK)
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        JP Z,EG_MISS
        JP GN_FIND
GN_COUNT: DW 0
