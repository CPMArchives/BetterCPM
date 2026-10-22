; Optional standard-profile word actions. No storage or console dependencies.
; A word is a run of non-space characters. All positions are byte indices.
UW_LEFT:
        LD A,(EDITCUR)
        LD B,A
UW_LSP:
        LD A,B
        OR A
        JP Z,UW_SET
        DEC A
        LD E,A
        LD D,0
        LD HL,EDITBUF
        ADD HL,DE
        LD A,(HL)
        CP ' '
        JR NZ,UW_LWORD
        DEC B
        JR UW_LSP
UW_LWORD:
        DEC B
        LD A,B
        OR A
        JR Z,UW_SET
        DEC HL
        LD A,(HL)
        CP ' '
        JR NZ,UW_LWORD
        JR UW_SET
UW_RIGHT:
        LD A,(EDITCUR)
        LD B,A
        LD E,A
        LD D,0
        LD HL,EDITBUF
        ADD HL,DE
        LD A,(EDITLEN)
        LD C,A
UW_RWORD:
        LD A,B
        CP C
        JR Z,UW_SET
        LD A,(HL)
        CP ' '
        JR Z,UW_RSP
        INC B
        INC HL
        JR UW_RWORD
UW_RSP:
        LD A,B
        CP C
        JR Z,UW_SET
        LD A,(HL)
        CP ' '
        JR NZ,UW_SET
        INC B
        INC HL
        JR UW_RSP
UW_SET:
        LD A,B
        LD (EDITCUR),A
        JP EDITLOOP
UW_CLEAR:
        XOR A
        LD (EDITLEN),A
        LD (EDITCUR),A
        LD (EDITSTART),A
        JP EDITLOOP
