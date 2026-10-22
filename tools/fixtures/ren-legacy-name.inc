; REN Build 007 input loop before shared append-engine extraction.
; From PR 439 commit 711c3da (Build 007). Assemble at R_NEWPROM context.
        XOR A
        LD (R_ILEN),A
        LD (R_IFULL),A
R_INCHAR:
        LD C,1
        CALL BDOS
        CP 3
        JP Z,R_ABORT
        CP 13
        JR Z,R_INEND
        CP 8
        JR Z,R_BACK
        CP 127
        JR Z,R_BACK
        CP 21
        JR Z,R_RELINE
        LD E,A
        LD A,(R_ILEN)
        CP 31
        JR NC,R_OVER
        LD L,A
        LD H,0
        LD BC,R_IBUF
        ADD HL,BC
        LD A,E
        CP 'a'
        JR C,R_ISTORE
        CP 'z'+1
        JR NC,R_ISTORE
        AND 5FH
R_ISTORE:
        LD (HL),A
        LD A,(R_ILEN)
        INC A
        LD (R_ILEN),A
        JR R_INCHAR
R_OVER:
        LD A,1
        LD (R_IFULL),A
        JR R_INCHAR
R_BACK:
        LD A,(R_ILEN)
        OR A
        JR Z,R_INCHAR
        DEC A
        LD (R_ILEN),A
        JR R_INCHAR
R_RELINE:
        XOR A
        LD (R_ILEN),A
        LD (R_IFULL),A
        JR R_INCHAR
