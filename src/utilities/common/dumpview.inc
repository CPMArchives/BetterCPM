; Callable SCRN discovery. Legacy descriptor gives actual callable cell geometry;
; SCX zero geometry means host-managed, not detected host terminal dimensions.
SCREENINIT:
        LD DE,REQ
        LD C,182
        CALL SERVICE
        OR A
        JP NZ,SINONE
        LD HL,(REQ+12)
        LD (BACKEND),HL
        LD A,H
        OR L
        JP Z,SINONE
        LD A,12
        CALL SCREENQUERY
        LD DE,SIGNATURE
        LD B,5
SICHECK:
        LD A,(DE)
        CP (HL)
        JP NZ,SINONE
        INC HL
        INC DE
        DJNZ SICHECK
        LD A,(HL)
        LD (HEIGHT),A
        CP 2
        JP C,SIGEOM
        DEC A
        LD (ROWS),A
        INC HL
        LD A,(HL)
        LD (WIDTH),A
        LD B,76
        LD A,(COMPACT)
        OR A
        JR Z,SIWIDTH
        LD B,37
SIWIDTH:
        LD A,(WIDTH)
        CP B
        JR C,SIGEOM
        INC HL
        LD A,(HL)
        AND 0C0H
        CP 0C0H
        JP NZ,SINONE
        INC HL
        LD A,(HL)
        AND 11H
        CP 11H
        JP NZ,SINONE
        LD HL,0
        LD A,(ROWBYTES)
        LD E,A
        LD D,0
        LD A,(ROWS)
        LD B,A
SICAP:
        ADD HL,DE
        DJNZ SICAP
        LD (PAGESIZE),HL
        OR A
        RET
SINONE:
        LD DE,MONMSG
        CALL MESSAGE
        SCF
        RET
SIGEOM:
        LD DE,GEOMMSG
        CALL MESSAGE
        LD HL,NUM76
        LD A,(COMPACT)
        OR A
        JR Z,SIGPRINT
        LD HL,NUM37
SIGPRINT:
        CALL TEXT
        LD DE,COLMSG
        CALL MESSAGE
        SCF
        RET
; Screen wrapper preserves general registers/flags. QUERY additionally returns HL.
SCREEN:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        CALL SCALL
        POP HL
        POP DE
        POP BC
        POP AF
        RET
SCREENQUERY:
        PUSH BC
        PUSH DE
        CALL SCALL
        POP DE
        POP BC
        RET
SCALL:
        PUSH HL
        LD HL,(BACKEND)
        EX (SP),HL
        RET
POSITION:
        LD A,6
        JP SCREEN
CLEARLINE:
        LD C,32
        LD A,8
        JP SCREEN
BOTTOM:
        LD A,(HEIGHT)
        DEC A
        LD B,A
        LD C,0
        CALL POSITION
        JP CLEARLINE
HINT:
        CALL BOTTOM
        LD HL,PAGEHINT
        LD A,(ACTIVE)
        OR A
        JR Z,HINTTEXT
        LD HL,FINDHINT
HINTTEXT:
        JP TEXT
STATUS:
        PUSH HL
        CALL BOTTOM
        POP HL
        JP TEXT
READSTATUS:
        LD HL,READMSG
        CALL STATUS
        LD HL,ERRPOS
        JP HEX32
SCREENEXIT:
        ; Restore routed console state through its clear/home operation before
        ; returning from direct typed-screen rendering to the CCP personality.
        LD HL,(1)
        LD DE,63
        ADD HL,DE
        LD A,4
        JP (HL)
RENDER:
        LD HL,PAGE
        LD DE,DISPLAYPOS
        CALL COPY32
        LD HL,PAGEBUF
        LD (RENDERPTR),HL
        LD HL,(PAGECOUNT)
        LD (REMAIN),HL
        XOR A
        LD (ROWNUM),A
RENDERLOOP:
        LD A,(ROWNUM)
        LD B,A
        LD C,0
        CALL POSITION
        CALL CLEARLINE
        LD HL,(REMAIN)
        LD A,H
        OR L
        JR Z,RENDERNEXT
        CALL ROWOUT
        LD HL,(REMAIN)
        LD A,(ROWBYTES)
        LD E,A
        LD D,0
        OR A
        SBC HL,DE
        LD (REMAIN),HL
RENDERNEXT:
        LD HL,ROWNUM
        INC (HL)
        LD A,(ROWS)
        CP (HL)
        JR NZ,RENDERLOOP
        JP HINT
VIEWLOOP:
        CALL WAITKEY
        CALL UPPER
        CP 'Q'
        JP Z,DEXIT
        CP 'F'
        JP Z,FIND
        CP 'G'
        JP Z,GOTO
        CP 3
        JP Z,PAGEDOWN
        CP ' '
        JP Z,PAGEDOWN
        CP 18
        JP Z,PAGEUP
        CP '.'
        JR Z,VLDOT
        CP ','
        JR Z,VLCOMMA
        JP VIEWLOOP
VLDOT:
        LD A,(ACTIVE)
        OR A
        JP Z,PAGEDOWN
        XOR A
        LD (DIRECTION),A
        JP CONTINUEFIND
VLCOMMA:
        LD A,(ACTIVE)
        OR A
        JP Z,PAGEUP
        LD A,1
        LD (DIRECTION),A
        JP CONTINUEFIND
PAGEDOWN:
        LD HL,PAGE
        LD DE,NEXT
        CALL COPY32
        LD HL,NEXT
        LD DE,(PAGESIZE)
        CALL ADD16
        LD DE,LENGTH
        CALL CMP32
        JR C,DOMOVE
        LD HL,ENDMSG
        CALL STATUS
        JP VIEWLOOP
PAGEUP:
        LD HL,PAGE
        CALL NONZERO
        JR NZ,PUMOVE
        LD HL,BEGMSG
        CALL STATUS
        JP VIEWLOOP
PUMOVE:
        LD HL,PAGE
        LD DE,NEXT
        CALL COPY32
        LD HL,(NEXT)
        LD DE,(PAGESIZE)
        OR A
        SBC HL,DE
        LD (NEXT),HL
        LD HL,(NEXT+2)
        LD DE,0
        SBC HL,DE
        LD (NEXT+2),HL
        JR NC,DOMOVE
        XOR A
        LD HL,NEXT
        LD (HL),A
        INC HL
        LD (HL),A
        INC HL
        LD (HL),A
        INC HL
        LD (HL),A
DOMOVE:
        CALL LOADPAGE
        JR C,MOVEERROR
        CALL COMMITPAGE
        CALL RESETANCHOR
        CALL RENDER
        JP VIEWLOOP
MOVEERROR:
        CALL READSTATUS
        JP VIEWLOOP
RESETANCHOR:
        LD HL,PAGE
        LD DE,ANCHOR
        CALL COPY32
        XOR A
        LD (MATCHED),A
        RET
GOTO:
        LD HL,GOPROMPT
        LD A,9
        CALL EDITNEW
        JP C,VIEWLOOP
GOCHECK:
        LD HL,EDITBUF
        LD A,(EDITLEN)
        LD B,A
        LD DE,NEXT
        CALL PARSEHEX
        JR C,GOBAD
        LD HL,NEXT
        LD DE,LENGTH
        CALL CMP32
        JR NC,GOBAD
        CALL ALIGNNEXT
        JP DOMOVE
GOBAD:
        LD HL,BADINPUT
        CALL STATUS
        CALL WAITEDIT
        JP C,VIEWLOOP
        JR GOCHECK
; Bind the shared editor to DUMP's keyboard and bottom-row renderer.
; @ui-input@
; DUMP positions/clears the shared bottom row and measures its label.
EDITDRAW:
        CALL BOTTOM
        LD HL,(EDITPROMPT)
        LD D,0
EDLABEL:
        LD A,(HL)
        OR A
        JR Z,EDFIELD
        CALL PUT
        INC HL
        INC D
        JR EDLABEL
EDFIELD:
        LD A,(WIDTH)
        JP UR_DRAW
UR_PUT EQU PUT
UR_POS:
        LD A,(HEIGHT)
        DEC A
        LD B,A
        JP POSITION
UR_MARK:
        PUSH BC
        OR 128
        LD C,A
        LD A,7
        CALL SCREEN
        POP BC
        RET
; @ui-screen@
SIGNATURE: DB 'SCR',1,0
NUM76: DB '76',0
NUM37: DB '37',0

; Unechoed input is essential: BDOS 1 would echo through a personality whose
; parser cursor is not the direct screen editor's cursor. Direct input also
; leaves Ctrl-C available as a viewer command rather than a cooked break.
WAITKEY:
        LD E,255
        LD C,6
        CALL SERVICE
        OR A
        JR Z,WAITKEY
        RET
WKEND:
