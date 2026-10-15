; Work-file record stream. HL=opened caller-owned FCB, A=output user.
; EW_PUT C=byte, EW_FIN pads only a partial final record with Ctrl-Z.
; Carry denotes raw BDOS write status (or 255 for a sealed-stream misuse).
; Write failures are latched: no automatic retry of a possibly advanced FCB.
; Owner handles create/close/publication and final DU/DMA restoration.
EW_INIT:
        LD (EW_FCB),HL
        LD (EW_USER),A
        XOR A
        LD (EW_POS),A
        LD (EW_BAD),A
        LD (EW_SEAL),A
        LD (EW_PAD),A
        RET
EW_CHECK:
        LD A,(EW_BAD)
        OR A
        RET Z
        SCF
        RET
EW_PUT:
        CALL EW_CHECK
        RET C
        LD A,(EW_SEAL)
        OR A
        JP NZ,EW_CLOSED
        PUSH BC
        LD A,(EW_POS)
        CP 128
        JP NZ,EW_SPACE
        CALL EW_FLUSH
        POP BC
        RET C
        JP EW_STORE
EW_SPACE:
        POP BC
EW_STORE:
        LD A,(EW_POS)
        LD E,A
        LD D,0
        LD HL,EW_DATA
        ADD HL,DE
        LD (HL),C
        INC A
        LD (EW_POS),A
        XOR A
        RET
EW_FIN:
        CALL EW_CHECK
        RET C
        LD A,(EW_SEAL)
        OR A
        RET NZ                      ; repeated successful finish is harmless
        LD A,(EW_POS)
        OR A
        JP Z,EW_DONE
        CP 128
        JP Z,EW_LAST
        LD E,A
        LD D,0
        LD HL,EW_DATA
        ADD HL,DE
        LD A,128
        SUB E
        LD (EW_PAD),A              ; owner may need historical unused count
        LD B,A
EW_FILL:
        LD (HL),26
        INC HL
        DJNZ EW_FILL
        LD A,128
        LD (EW_POS),A
EW_LAST:
        CALL EW_FLUSH
        RET C
EW_DONE:
        LD A,1
        LD (EW_SEAL),A
        XOR A
        RET
EW_FLUSH:
        LD A,(EW_USER)
        LD E,A
        LD C,32
        CALL 5
        LD DE,EW_DATA
        LD C,26
        CALL 5
        LD DE,(EW_FCB)
        LD C,21
        CALL 5
        OR A
        JP NZ,EW_FAIL
        LD (EW_POS),A
        RET
EW_FAIL:
        LD (EW_BAD),A
        SCF
        RET
EW_CLOSED:
        LD A,255
        SCF
        RET
EW_FCB: DW 0
EW_USER: DB 0
EW_POS: DB 0
EW_BAD: DB 0
EW_SEAL: DB 0
EW_PAD: DB 0
EW_DATA: DS 128
