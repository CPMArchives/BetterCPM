; Save data preparation, before close/rename/publication. Caller initializes
; source/output streams and calls EF_INIT once per editing session.
; EF_DRAIN empties memory, copies unread source verbatim, and pads output.
; Carry A=raw read/write status. No close, delete or rename occurs here.
EF_INIT:
        XOR A
        LD (EF_HAVE),A
        LD (EF_DONE),A
        LD (EF_ERROR),A
        RET
EF_DRAIN:
        LD A,(EF_DONE)
        OR A
        JP NZ,EF_OK
        LD HL,0FFFFH
        LD (EC_COUNT),HL
        XOR A
        LD (EC_NEG),A
        CALL EX_RUN
        JP NC,EF_SOURCE
        LD A,(EX_ERROR)
        JP EF_FAIL
EF_SOURCE:
        LD A,(EF_HAVE)
        OR A
        JP NZ,EF_WRITE
        CALL ES_GET
        JP NC,EF_HOLD
        CP 1
        JP Z,EF_FINAL
        JP EF_FAIL
EF_HOLD:
        LD (EF_BYTE),A
        LD A,1
        LD (EF_HAVE),A
EF_WRITE:
        LD A,(EF_BYTE)
        LD C,A
        CALL EW_PUT
        JP C,EF_FAIL
        XOR A
        LD (EF_HAVE),A
        JP EF_SOURCE
EF_FINAL:
        CALL EW_FIN
        JP C,EF_FAIL
        LD A,1
        LD (EF_DONE),A
EF_OK:
        XOR A
        RET
EF_FAIL:
        LD (EF_ERROR),A
        SCF
        RET
EF_HAVE: DB 0
EF_BYTE: DB 0
EF_DONE: DB 0
EF_ERROR: DB 0
