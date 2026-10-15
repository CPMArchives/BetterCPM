; Initial L/K line ranges, using the same logical cursor as character commands.
; Forward N reaches after N LFs, backward N reaches N prior line starts.
; Zero (backward) reaches the current line start. Edges saturate.
EL_MOVE:
        LD A,(EC_NEG)
        OR A
        JP NZ,EL_BACK
EL_FLINE:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
EL_FCHAR:
        CALL EB_RIGHT
        JP C,EL_DONE
        CP 10
        JP NZ,EL_FCHAR
        LD HL,(EC_COUNT)
        DEC HL
        LD (EC_COUNT),HL
        JP EL_FLINE
EL_BACK:
        CALL EL_START
EL_BLINE:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
        CALL EB_LEFT
        JP C,EL_DONE
        CALL EL_START
        LD HL,(EC_COUNT)
        DEC HL
        LD (EC_COUNT),HL
        JP EL_BLINE
EL_START:
        CALL EB_LEFT
        JP C,EL_DONE
        CP 10
        JP NZ,EL_START
        CALL EB_RIGHT
EL_DONE:
        OR A
        RET
EL_KILL:
        LD HL,(EB_FRONT)
        LD (EL_ORIG),HL
        CALL EL_MOVE
        LD A,(EC_NEG)
        OR A
        JP NZ,EL_KBACK
        LD HL,(EL_ORIG)
        LD (EB_FRONT),HL
        OR A
        RET
EL_KBACK:
        LD HL,(EL_ORIG)
        LD DE,(EB_FRONT)
        OR A
        SBC HL,DE
        LD DE,(EB_BACK)
        ADD HL,DE
        LD (EB_BACK),HL
        OR A
        RET
EL_ORIG: DW 0
