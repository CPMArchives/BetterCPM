; DRI PUTDEST/PUTDESTC/PUTDCHAR subset: F, T and D.
; The byte column count survives source changes; CR alone resets it.
PF_CPUT:
        LD (PF_CHAR),A
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

; Line numbering and pagination share PUTDESTC tab/column behavior.
PN_INIT:
        LD HL,PN_COUNT
        LD B,6
PN_ZERO:
        LD (HL),'0'
        INC HL
        DJNZ PN_ZERO
        LD A,1
        LD (PN_READY),A
        LD A,254
        LD (PN_LINE),A
        RET
PF_PUT:
        LD (PN_CHAR),A
        CP 12
        JR NZ,PN_START
        LD A,(OP_DATA+129)
        OR A
        JP Z,PN_SEND
        XOR A
        RET
PN_START:
        LD A,(PN_READY)
        OR A
        JP Z,PN_SEND
        LD A,(OP_DATA+139)
        OR A
        JR Z,PN_NUMBER
        CP 1
        JR NZ,PN_PAGE
        LD A,60
PN_PAGE:
        LD B,A
        LD HL,PN_LINE
        INC (HL)
        LD A,(HL)
        CP B
        JR C,PN_NUMBER
        XOR A
        LD (HL),A
        LD A,12
        CALL PF_CPUT
        OR A
        RET NZ
PN_NUMBER:
        LD A,(OP_DATA+137)
        OR A
        JR Z,PN_MARK
        LD HL,PN_COUNT+5
        LD B,6
PN_INC:
        INC (HL)
        LD A,(HL)
        CP '9'+1
        JR C,PN_PRINT
        LD (HL),'0'
        DEC HL
        DJNZ PN_INC
PN_PRINT:
        LD A,(OP_DATA+137)
        CP 1
        LD A,0
        JR NZ,PN_MODE
        INC A
PN_MODE:
        LD (PN_SUP),A
        LD A,6
        LD (PN_LEFT),A
        LD HL,PN_COUNT
        LD (PN_PTR),HL
PN_LOOP:
        LD HL,(PN_PTR)
        LD A,(HL)
        INC HL
        LD (PN_PTR),HL
        LD E,A
        LD A,(PN_SUP)
        OR A
        LD A,E
        JR Z,PN_DIGIT
        CP '0'
        JR NZ,PN_VISIBLE
        LD A,' '
        JR PN_DIGIT
PN_VISIBLE:
        XOR A
        LD (PN_SUP),A
        LD A,E
PN_DIGIT:
        CALL PF_CPUT
        OR A
        RET NZ
        LD HL,PN_LEFT
        DEC (HL)
        JR NZ,PN_LOOP
        LD A,(OP_DATA+137)
        CP 1
        LD A,9
        JR NZ,PN_SUFFIX
        LD A,':'
        CALL PF_CPUT
        OR A
        RET NZ
        LD A,' '
PN_SUFFIX:
        CALL PF_CPUT
        OR A
        RET NZ
PN_MARK:
        XOR A
        LD (PN_READY),A
PN_SEND:
        LD A,(PN_CHAR)
        CP 12
        JR NZ,PN_OUTPUT
        XOR A
        LD (PN_LINE),A
PN_OUTPUT:
        LD A,(PN_CHAR)
        CALL PF_CPUT
        OR A
        RET NZ
        LD A,(PN_CHAR)
        CP 10
        JR NZ,PN_OK
        LD A,1
        LD (PN_READY),A
PN_OK:
        XOR A
        RET
PN_CHAR: DB 0
PN_READY: DB 0
PN_LINE: DB 0
PN_SUP: DB 0
PN_LEFT: DB 0
PN_PTR: DW 0
PN_COUNT: DB '000000'
