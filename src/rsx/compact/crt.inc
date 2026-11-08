; Native fixed-cell renderer. No terminal byte grammar is interpreted here.
        IF TYPEVT EQ 0
D_VISSET:
        RET
        ENDIF
D_PRINT:
        IF TYPEVT EQ 1
        LD A,C
        ELSE
        LD A,(D_REV)
        OR C
        ENDIF
        LD HL,(CRT_POS)
        LD (HL),A
D_RIGHT:
        CALL D_GET
        IF TYPEVT EQ 1
        LD A,H
        CP 79
        RET Z
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
        JR NZ,D_PREVCOL
        OR L
        RET Z
        DEC L
        LD H,80
        ENDIF
D_PREVCOL:
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
        LD A,(CRT_COL)
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
        LD A,H
        LD (CRT_COL),A
        LD E,L
        LD D,0
        LD L,A
        LD H,D
        PUSH HL
        LD H,D
        LD L,E
        ADD HL,HL
        ADD HL,HL
        ADD HL,DE
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        POP DE
        ADD HL,DE
        LD DE,0F800H
        ADD HL,DE
        LD (CRT_POS),HL
        XOR A
        RET
D_OFF:
        XOR A
        IF TYPEVT EQ 1
        RET
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
        XOR A
        RET
        ENDIF
D_EOL:
        LD HL,(CRT_POS)
        LD A,(CRT_COL)
        LD C,A
        LD A,80
        SUB C
        LD C,A
        LD B,0
        JP D_FILL
D_EOS:
        LD HL,0FF80H
        LD DE,(CRT_POS)
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        EX DE,HL
        JP D_FILL
D_BELL:
        IF M2BANK EQ 0
        LD C,0
D_TONE:
        LD A,1
        LD B,100
D_HIGH:
        OUT (090H),A
        DJNZ D_HIGH
        XOR A
        LD B,100
D_LOW:
        OUT (090H),A
        DJNZ D_LOW
        DEC C
        JR NZ,D_TONE
        ENDIF
        RET
        IF TYPEVT EQ 0
D_INSERT:
        CALL D_LINE
        PUSH HL
        CALL D_REMAIN
        JR Z,D_INBLANK
        LD HL,0FF2FH
        LD DE,0FF7FH
        LDDR
D_INBLANK:
        POP HL
        JR D_BLANK
D_DELETE:
        CALL D_LINE
        CALL D_REMAIN
        JR Z,D_BOTTOM
        LD D,H
        LD E,L
        PUSH DE
        LD DE,80
        ADD HL,DE
        POP DE
        LDIR
D_BOTTOM:
        LD HL,0FF30H
D_BLANK:
        LD BC,80
        JR D_FILL
        ELSE
D_RSCROL:
        LD HL,0FF2FH
        LD DE,0FF7FH
        LD BC,1840
        LDDR
        LD HL,0F800H
        JR D_BLANK
D_BOTTOM:
        LD HL,0FF30H
D_BLANK:
        LD BC,80
        JR D_FILL
        ENDIF
D_SCROLL:
        LD HL,0F850H
        LD DE,0F800H
        LD BC,1840
        LDIR
        JR D_BOTTOM
        IF TYPEVT EQ 0
D_LINE:
        LD HL,(CRT_POS)
        LD A,(CRT_COL)
        LD E,A
        LD D,0
        OR A
        SBC HL,DE
        RET
D_REMAIN:
        PUSH HL
        LD DE,0FF30H
        EX DE,HL
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        LD A,B
        OR C
        POP HL
        RET
        ENDIF
D_FILL:
        IF TYPEVT EQ 1
        LD A,32
        ELSE
        LD A,(D_REV)
        OR 32
        ENDIF
        LD (HL),A
        DEC BC
        LD A,B
        OR C
        RET Z
        LD D,H
        LD E,L
        INC DE
        LDIR
        XOR A
        RET
D_GET:
        LD HL,(CRT_POS)
        LD DE,0F800H
        OR A
        SBC HL,DE
        LD B,255
        LD DE,80
D_DIV:
        INC B
        OR A
        SBC HL,DE
        JR NC,D_DIV
        ADD HL,DE
        LD H,L
        LD L,B
        RET
; Private direct portable operations, with no transaction/session machinery.
; A=0 facts; 1 clear, 2 position B/C, 3 erase line, 4/5 strong on/off,
; 6/7 initialize/deinitialize normal rendition. Status 0 success, 3 bad args.
        IF M2BANK EQ 1
; Model II maps VRAM over the ordinary protected stack. Switch to a bounded
; resident stack before mapping, and restore bank/IFF/SP before returning.
; Raw keyboard operations above never enter this mapped interval.
D_MAP:
        LD (D_OP),A
        LD A,I
        DI
        PUSH AF
        LD (D_SP),SP
        LD SP,D_TOP
        LD A,081H
        OUT (0FFH),A
        LD A,(D_OP)
        CALL D_DISPATCH
D_UNMAP:
        LD (D_RESULT),A
        LD A,1
        OUT (0FFH),A
        LD SP,(D_SP)
        POP AF
        JP PO,D_NOEI
        EI
D_NOEI:
        PUSH HL
        LD HL,0
        LD (D_SP),HL
        POP HL
        LD A,(D_RESULT)
        OR A
        RET
D_SP: DW 0
D_OP: DB 0
D_RESULT: DB 0
D_GUARD: DB 0A5H
D_STACK: DS 20,0
D_TOP:
        ENDIF
