; Screen field renderer shared by compatibility and standard editors.
; Entry A=columns, D=already printed label length. Current row must be cleared;
; field begins just after label. Requires at least one cell for the caret.
; UR_PUT(A) and UR_MARK(A) preserve BC/DE/HL. UR_POS(C=column) positions on
; caller's prompt row and preserves DE/HL. UR_MARK draws a visible caret cell.
; Caller owns transport, geometry and row; this module emits no escape codes.
; Valid editor state required: START<=LEN, CUR<=LEN, LEN<=MAX<=255.
; Returns carry set/A=7 on invalid geometry before output/state changes.
; Otherwise carry clear; only EDITSTART may change. No allocated state.
UR_DRAW:
        SUB D
        JP C,UR_BAD
        OR A
        JP Z,UR_BAD
        DEC A
        LD E,A
        LD A,(EDITCUR)
        LD B,A
        LD A,(EDITSTART)
        CP B
        JR C,UR_VIS
        JR Z,UR_VIS
        LD A,B
        LD (EDITSTART),A
UR_VIS:
        LD A,(EDITSTART)
        LD C,A
        LD A,B
        SUB C
        CP E
        JR C,UR_SHOW
        JR Z,UR_SHOW
        LD A,B
        SUB E
        LD (EDITSTART),A
UR_SHOW:
        LD A,(EDITSTART)
        LD C,A
        LD A,(EDITLEN)
        SUB C
        LD B,A
        LD A,E
        CP B
        JR NC,UR_COUNT
        LD B,A
UR_COUNT:
        PUSH DE
        LD HL,EDITBUF
        LD E,C
        LD D,0
        ADD HL,DE
        LD A,B
        OR A
        JR Z,UR_CARET
UR_CHAR:
        LD A,(HL)
        CALL UR_PUT
        INC HL
        DJNZ UR_CHAR
UR_CARET:
        POP DE
        LD A,(EDITSTART)
        LD C,A
        LD A,(EDITCUR)
        SUB C
        ADD A,D
        LD C,A
        PUSH BC
        PUSH DE
        CALL UR_POS
        POP DE
        LD A,(EDITCUR)
        LD E,A
        LD D,0
        LD HL,EDITBUF
        ADD HL,DE
        LD A,(EDITLEN)
        CP E
        LD A,'_'
        JR Z,UR_GLYPH
        LD A,(HL)
UR_GLYPH:
        CALL UR_MARK
        POP BC
        CALL UR_POS
        OR A
        RET
UR_BAD:
        LD A,7
        SCF
        RET
