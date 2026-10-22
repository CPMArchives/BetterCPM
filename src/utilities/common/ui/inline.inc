; Inline renderer for the legacy editor; caller supplies UI_COLUMNS.
; Caller binds UI_PUT (A, preserves BC/DE/HL) and UI_MARK (same, visible caret).
; CI_DRAW clears/replaces the current physical line; no CR/LF while editing.
CI_DRAW:
        LD A,13
        CALL UI_PUT
        LD HL,(EDITPROMPT)
        LD D,0
CI_LABEL:
        LD A,(HL)
        INC HL
        OR A
        JR Z,CI_WIDTH
        CALL UI_PUT
        INC D
        JR CI_LABEL
CI_WIDTH:
        LD A,UI_COLUMNS-1
        SUB D
        LD E,A
        LD A,(EDITCUR)
        LD B,A
        LD A,(EDITSTART)
        CP B
        JR C,CI_VISIBLE
        JR Z,CI_VISIBLE
        LD A,B
        LD (EDITSTART),A
CI_VISIBLE:
        LD A,(EDITSTART)
        ADD A,E
        CP B
        JR NC,CI_SHOW
        LD A,B
        SUB E
        LD (EDITSTART),A
CI_SHOW:
        LD A,(EDITSTART)
        LD C,A
        LD HL,EDITBUF
        LD B,0
        ADD HL,BC
        INC E
CI_CELL:
        LD A,(EDITLEN)
        CP C
        LD A,' '
        JR Z,CI_GLYPH
        JR C,CI_GLYPH
        LD A,(HL)
CI_GLYPH:
        LD B,A
        LD A,(EDITCUR)
        CP C
        LD A,B
        JR NZ,CI_PLAIN
        CP ' '
        JR NZ,CI_MARK
        LD A,'_'
CI_MARK:
        CALL UI_MARK
        JR CI_NEXT
CI_PLAIN:
        CALL UI_PUT
CI_NEXT:
        INC HL
        INC C
        DEC E
        JR NZ,CI_CELL
        LD A,13
        JP UI_PUT
