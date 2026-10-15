; Open source stream: HL=caller-owned 36-byte FCB, A=user area.
; The FCB includes its drive. Owner handles open/close and final DU/DMA restore.
; ES_GET: carry clear A=byte; carry A=1 text/physical EOF, A>1 BDOS error.
; EOF is sticky. Errors retain an empty record buffer for an explicit retry.
; No case translation: DRI GETSOURCE preserves bytes; command consumers decide.
ES_INIT:
        LD (ES_FCB),HL
        LD (ES_USER),A
        XOR A
        LD (ES_EOF),A
        LD A,128
        LD (ES_POS),A
        RET
ES_GET:
        LD A,(ES_EOF)
        OR A
        JP NZ,ES_END
        LD A,(ES_POS)
        CP 128
        JP C,ES_BYTE
        LD A,(ES_USER)
        LD E,A
        LD C,32
        CALL 5
        LD DE,ES_DATA
        LD C,26
        CALL 5
        LD DE,(ES_FCB)
        LD C,20
        CALL 5
        OR A
        JP Z,ES_READY
        CP 1
        JP Z,ES_MARK
        SCF
        RET
ES_READY:
        XOR A
        LD (ES_POS),A
ES_BYTE:
        LD E,A
        LD D,0
        LD HL,ES_DATA
        ADD HL,DE
        LD A,(HL)
        CP 26
        JP Z,ES_MARK
        PUSH AF
        LD A,(ES_POS)
        INC A
        LD (ES_POS),A
        POP AF
        OR A
        RET
ES_MARK:
        LD A,1
        LD (ES_EOF),A
ES_END:
        LD A,1
        SCF
        RET
ES_FCB: DW 0
ES_USER: DB 0
ES_EOF: DB 0
ES_POS: DB 128
ES_DATA: DS 128
