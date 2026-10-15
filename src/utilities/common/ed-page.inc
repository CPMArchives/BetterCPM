; P moves 23 lines in its direction and types 23 forward lines per page,
; with a CPU-timed WAIT after every page. Zero P only types from the cursor.
GP_RUN:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,GP_CURRENT
        LD (GP_LEFT),HL
        LD A,(EC_NEG)
        LD (GP_NEG),A
GP_LOOP:
        LD HL,(GP_LEFT)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (GP_LEFT),HL
        LD HL,23
        LD (EC_COUNT),HL
        LD A,(GP_NEG)
        LD (EC_NEG),A
        CALL EL_MOVE
        LD HL,(EB_FRONT)
        LD (GP_START),HL
        XOR A
        LD (EC_NEG),A
        LD HL,23
        LD (EC_COUNT),HL
        CALL ET_TYPE
        RET C
        LD HL,(GP_START)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        JP Z,GP_LIMIT
        LD HL,(EB_LIMIT)
        LD DE,(EB_BACK)
        OR A
        SBC HL,DE
        LD DE,(EB_FRONT)
        ADD HL,DE
        LD DE,(ET_LAST)
        OR A
        SBC HL,DE
        JP NZ,GP_PAUSE
GP_LIMIT:
        LD HL,0
        LD (GP_LEFT),HL
GP_PAUSE:
        CALL GZ_WAIT
        RET C
        JP GP_LOOP
GP_CURRENT:
        XOR A
        LD (EC_NEG),A
        LD HL,23
        LD (EC_COUNT),HL
        JP ET_TYPE
GP_LEFT: DW 0
GP_NEG: DB 0
GP_START: DW 0
