; Fixed 80 by 24 ANSI host renderer. The protocol grammar remains in the
; personality. Output is a leaf transport, never a recursive console call.
D_PRINT:
        LD A,C
        AND 127
        CP 32
        JR C,H_GLYPH
        CP 127
        JR C,H_PRINT
H_GLYPH:
        LD A,'?'
H_PRINT:
        PUSH AF
        IF TYPEVT EQ 0
        LD A,(D_REV)
        OR C
        AND 128
        CALL H_ATTR
        CALL H_POSITION
        ELSE
        CALL D_OFF
        ENDIF
        POP AF
        OUT (1),A
D_RIGHT:
        CALL D_GET
        IF TYPEVT EQ 1
        LD A,H
        CP 79
        JP Z,H_POSITION
        ENDIF
        INC H
        LD A,H
        CP 80
        JR C,D_SET
        LD H,0
        JR D_NEXTROW
D_LEFT:
        CALL D_GET
        LD A,H
        OR A
        IF TYPEVT EQ 1
        RET Z
        ELSE
        JR NZ,H_LEFT
        OR L
        RET Z
        DEC L
        LD H,80
        ENDIF
H_LEFT:
        DEC H
        JR D_SET
D_TAB:
        IF TYPEVT EQ 1
        CALL D_GET
        LD A,H
        CP 72
        JP NC,D_RIGHT
        AND 0F8H
        ADD A,8
        LD H,A
        JP D_SET
        ELSE
        CALL D_RIGHT
        LD A,(H_RC+1)
        AND 7
        JR NZ,D_TAB
        RET
        ENDIF
D_DOWN:
        CALL D_GET
        IF TYPEVT EQ 1
        LD A,L
        CP 23
        RET Z
        INC L
        JR D_SET
D_LF:
        CALL D_GET
        ENDIF
D_NEXTROW:
        INC L
        LD A,L
        CP 24
        JR C,D_SET
        LD L,23
        PUSH HL
        CALL D_SCROLL
        POP HL
        JR D_SET
D_UP:
        CALL D_GET
        LD A,L
        OR A
        RET Z
        DEC L
        JR D_SET
D_HOME:
        LD HL,0
        JR D_SET
D_CR:
        CALL D_GET
        LD H,0
D_SET:
        LD (H_RC),HL
H_POSITION:
        LD HL,H_CSI
        CALL H_STR
        LD A,(H_RC)
        INC A
        CALL H_DEC
        LD A,';'
        OUT (1),A
        LD A,(H_RC+1)
        INC A
        CALL H_DEC
        LD A,'H'
        OUT (1),A
        XOR A
        RET
H_DEC:
        LD B,'0'
H_TENS:
        CP 10
        JR C,H_UNIT
        SUB 10
        INC B
        JR H_TENS
H_UNIT:
        LD C,A
        LD A,B
        CP '0'
        JR Z,H_LAST
        OUT (1),A
H_LAST:
        LD A,C
        ADD A,'0'
        OUT (1),A
        RET
D_OFF:
        XOR A
        IF TYPEVT EQ 1
        LD HL,H_NORMAL
        JP H_STR
        ELSE
        JR D_REVERSE
D_ON:
        LD A,128
        JR D_REVERSE
D_TOGGLE:
        LD A,(D_REV)
        XOR 128
D_REVERSE:
        LD (D_REV),A
        CALL H_ATTR
        XOR A
        RET
H_ATTR:
        LD HL,H_STYLE
        CP (HL)
        RET Z
        LD (HL),A
        LD HL,H_NORMAL
        OR A
        JR Z,H_STR
        LD HL,H_REVERSE
        ENDIF
H_STR:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        OUT (1),A
        JR H_STR
        IF TYPEVT EQ 0
D_EOL:
        LD B,1
        JR H_ERASE
D_EOS:
        LD A,(H_RC)
        LD B,A
        LD A,24
        SUB B
        LD B,A
H_ERASE:
        CALL H_FILLATTR
        LD A,(H_RC+1)
        LD C,A
        LD A,80
        SUB C
        LD C,A
        LD A,32
H_ERLOOP:
        OUT (1),A
        DEC C
        JR NZ,H_ERLOOP
        DEC B
        JP Z,H_POSITION
        LD HL,H_NEXT
        CALL H_STR
        LD C,80
        LD A,32
        JR H_ERLOOP
H_FILLATTR:
        LD A,(D_REV)
        CALL H_ATTR
        XOR A
        RET
        ELSE
D_EOL:
        LD HL,H_K
        JR H_ERASE
D_EOS:
        LD HL,H_J
H_ERASE:
        PUSH HL
        CALL D_OFF
        POP HL
        JP H_STR
H_FILLATTR:
        JP D_OFF
        ENDIF
H_BLANK:
        LD A,13
        OUT (1),A
        LD B,80
H_SPACES:
        LD A,32
H_SPACE:
        OUT (1),A
        DJNZ H_SPACE
        XOR A
        RET
D_BELL:
        LD A,7
        OUT (1),A
        RET
        IF TYPEVT EQ 0
D_INSERT:
        LD HL,H_IL
        JR H_LINE
D_DELETE:
        LD HL,H_DL
        JR H_LINE
        ELSE
D_RSCROL:
        LD HL,H_TOP
        JR H_LINE
        ENDIF
D_SCROLL:
        LD HL,H_BOTTOM
H_LINE:
        PUSH HL
        CALL H_FILLATTR
        LD HL,H_MARGIN
        CALL H_STR
        CALL H_POSITION
        POP HL
        CALL H_STR
        IF TYPEVT EQ 0
        LD A,(HL)
        OR A
        JR NZ,H_LINEBOTTOM
        CALL H_BLANK
        JR H_RESTORE
H_LINEBOTTOM:
        LD HL,H_BOTPOS
        CALL H_STR
        CALL H_BLANK
        ELSE
        CALL H_BLANK
        ENDIF
H_RESTORE:
        LD HL,H_ALL
        CALL H_STR
        JP H_POSITION
        IF TYPEVT EQ 0
D_VISSET:
        LD A,(D_VIS)
        LD HL,H_HIDE
        OR A
        JP Z,H_STR
        LD HL,H_SHOW
        JP H_STR
        ENDIF
D_GET:
        LD HL,(H_RC)
        RET
H_CSI: DB 27,'[',0
        IF TYPEVT EQ 0
H_NEXT: DB 27,'[E',0
        ELSE
H_K: DB 27,'[K',0
H_J: DB 27,'[J',0
        ENDIF
H_NORMAL: DB 27,'[0m',0
        IF TYPEVT EQ 0
H_REVERSE: DB 27,'[7m',0
        ENDIF
        IF TYPEVT EQ 0
H_IL: DB 27,'[L',0,0
H_DL: DB 27,'[M',0,1
        ELSE
H_TOP: DB 27,'[H',27,'M',0,0
        ENDIF
H_BOTTOM: DB 27,'[24;1H',10,0,1
        IF TYPEVT EQ 0
H_BOTPOS: DB 27,'[24;1H',0
        ENDIF
H_MARGIN: DB 27,'[1;24r',0
H_ALL: DB 27,'[r',0
        IF TYPEVT EQ 0
H_HIDE: DB 27,'[?25l',0
H_SHOW: DB 27,'[?25h',0
        ENDIF
H_RC: DW 0
        IF TYPEVT EQ 0
H_STYLE: DB 255
        ENDIF
