; DRI PUTDEST/PUTDESTC/PUTDCHAR subset: F, T and D.
; The byte column count survives source changes; CR alone resets it.
PF_PUT:
        LD (PF_CHAR),A
        CP 12
        JR NZ,PF_TAB
        LD A,(OP_DATA+129)
        OR A
        JR Z,PF_PASS
        XOR A
        RET
PF_TAB:
        CP 9
        JR NZ,PF_PASS
        LD A,(OP_DATA+143)
        OR A
        JR Z,PF_PASS
        LD B,A
        LD A,(PF_COL)
PF_MOD:
        CP B
        JR C,PF_WIDTH
        SUB B
        JR PF_MOD
PF_WIDTH:
        LD E,A
        LD A,B
        SUB E
        LD (PF_LEFT),A
PF_SPACES:
        LD A,' '
        CALL PF_OUT
        OR A
        RET NZ
        LD HL,PF_LEFT
        DEC (HL)
        JR NZ,PF_SPACES
        XOR A
        RET
PF_PASS:
        LD A,(PF_CHAR)
        CALL PF_OUT
        OR A
        RET NZ
        LD A,(PF_CHAR)
        CP 13
        JR NZ,PF_OK
        XOR A
        LD (PF_COL),A
PF_OK:
        XOR A
        RET
PF_OUT:
        LD E,A
        CP ' '
        JR C,PF_SEND
        LD HL,PF_COL
        INC (HL)
        LD A,(OP_DATA+127)
        OR A
        JR Z,PF_SEND
        CP (HL)
        JR NC,PF_SEND
        XOR A
        RET
PF_SEND:
        LD A,E
        JP PI_PUT
PF_COL: DB 0
PF_CHAR: DB 0
PF_LEFT: DB 0
