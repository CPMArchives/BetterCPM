; Shared single-line editor: event engine and legacy compatibility adapter.
; Caller owns EDITBUF and EDITLEN/CUR/START/MAX/PROMPT. No allocation or I/O.
; Bind UIREAD (A=character), UIDRAW, UICANCEL, UIMESSAGE (HL=text),
; UILIMITMSG (text address). Hooks must preserve stack; UIDRAW may clobber
; general registers. UIREAD returns A. Core clobbers AF/BC/DE/HL.
; EDITNEW: A=capacity (1..255), HL=opaque prompt pointer; starts empty.
; Return carry=cancel (ESC or empty Enter), carry clear=submitted nonempty.
; WAITEDIT: resume after caller validation error; preserve text/cursor/scroll,
; redraw and process the first key exactly once. No utility validation here.
; EDITBUF is length-counted, not terminated. Caller provides capacity bytes.
; This compatibility profile deliberately retains DUMP Build 002 key behavior.
; UISTD=0 retains the legacy bytes; UISTD=1 exports the event engine.
; Select through tools/shared_ui.py. Standard mode does no console I/O.
;
        IF UISTD EQ 0
; Compatibility entry keeps raw case/spaces and caller-provided limits.
EDITNEW:
        LD (EDITMAX),A
        LD (EDITPROMPT),HL
        XOR A
        LD (EDITLEN),A
        LD (EDITCUR),A
        LD (EDITSTART),A
        JP EDITLOOP
WAITEDIT:
        ; Keep invalid input editable; one key dismisses message and is handled
        ; as an editor key rather than being lost.
        CALL UIREAD
        PUSH AF
        CALL UIDRAW
        POP AF
        JP EDITKEY
EDITLOOP:
        CALL UIDRAW
EDITREAD:
        CALL UIREAD
        ELSE
; A=capacity, B=initial length, HL=opaque prompt; caller preloads EDITBUF.
UE_INIT:
        OR A
        JR Z,UE_BAD
        CP B
        JR C,UE_BAD
        PUSH AF
        PUSH HL
        LD HL,EDITBUF
        CALL UE_ASCII
        POP HL
        JR C,UE_TXBAD
        POP AF
        LD (EDITMAX),A
        LD (EDITPROMPT),HL
        LD A,B
        LD (EDITLEN),A
        LD (EDITCUR),A
        XOR A
        LD (EDITSTART),A
        RET
UE_TXBAD:
        POP AF
UE_BAD:
        LD A,UI_BAD
        SCF
        RET
; One logical key in A; return an event without reading, drawing or allocating.
UE_KEY:
        ENDIF
EDITKEY:
        IF UISTD EQ 1
        CP 3
        JP Z,EDITCANCEL
        CP 127
        JP Z,EDITBACK
        IF UI_WORDS EQ 1
        CP 1
        JP Z,UW_LEFT
        CP 6
        JP Z,UW_RIGHT
        CP 25
        JP Z,UW_CLEAR
        ENDIF
        ENDIF
        CP 27
        IF UISTD EQ 1
        JP Z,EDITCANCEL
        ELSE
        JR Z,EDITCANCEL
        ENDIF
        CP 13
        IF UISTD EQ 1
        JP Z,EDITSUBMIT
        ELSE
        JR Z,EDITSUBMIT
        ENDIF
        CP 19
        IF UISTD EQ 1
        JP Z,EDITLEFT
        ELSE
        JR Z,EDITLEFT
        ENDIF
        CP 4
        IF UISTD EQ 1
        JP Z,EDITRIGHT
        ELSE
        JR Z,EDITRIGHT
        ENDIF
        CP 8
        IF UISTD EQ 1
        JP Z,EDITBACK
        ELSE
        JR Z,EDITBACK
        ENDIF
        CP 7
        JP Z,EDITDELETE
        CP 32
        IF UISTD EQ 1
        JP C,EDITREAD
        ELSE
        JR C,EDITREAD
        ENDIF
        CP 127
        IF UISTD EQ 1
        JP NC,EDITREAD
        ELSE
        JR NC,EDITREAD
        ENDIF
        LD E,A
        LD A,(EDITLEN)
        LD B,A
        LD A,(EDITMAX)
        CP B
        JR Z,EDITLIMIT
        LD A,(EDITCUR)
        LD C,A
        LD HL,EDITBUF
        LD A,B
        LD D,0
        PUSH DE
        LD E,A
        ADD HL,DE
        POP DE
EDITSHIFT:
        LD A,B
        CP C
        JR Z,EDITINSERT
        DEC HL
        LD A,(HL)
        INC HL
        LD (HL),A
        DEC HL
        DEC B
        JR EDITSHIFT
EDITINSERT:
        LD (HL),E
        LD HL,EDITCUR
        INC (HL)
        LD HL,EDITLEN
        INC (HL)
        JP EDITLOOP
        IF UISTD EQ 1
EDITLOOP:
        XOR A
        RET
EDITREAD:
        LD A,UI_SKIP
        OR A
        RET
EDITLIMIT:
        LD A,UI_LIMIT
        OR A
        RET
EDITCANCEL:
        LD A,UI_ABORT
        OR A
        RET
EDITSUBMIT:
        LD A,UI_SEND
        OR A
        RET
        ELSE
EDITLIMIT:
        LD HL,UILIMITMSG
        CALL UIMESSAGE
        JR EDITREAD
EDITCANCEL:
        CALL UICANCEL
        SCF
        RET
EDITSUBMIT:
        LD A,(EDITLEN)
        OR A
        JR Z,EDITCANCEL
        OR A
        RET
        ENDIF
EDITLEFT:
        LD HL,EDITCUR
        LD A,(HL)
        OR A
        IF UISTD EQ 1
        JP Z,EDITLOOP
        ELSE
        JP Z,EDITREAD
        ENDIF
        DEC (HL)
        JP EDITLOOP
EDITRIGHT:
        LD A,(EDITCUR)
        LD HL,EDITLEN
        CP (HL)
        IF UISTD EQ 1
        JP Z,EDITLOOP
        ELSE
        JP Z,EDITREAD
        ENDIF
        LD HL,EDITCUR
        INC (HL)
        JP EDITLOOP
EDITBACK:
        LD A,(EDITCUR)
        OR A
        IF UISTD EQ 1
        JP Z,EDITLOOP
        ELSE
        JP Z,EDITREAD
        ENDIF
        DEC A
        LD (EDITCUR),A
EDITDELETE:
        LD A,(EDITCUR)
        LD B,A
        LD A,(EDITLEN)
        CP B
        IF UISTD EQ 1
        JP Z,EDITLOOP
        ELSE
        JP Z,EDITREAD
        ENDIF
        SUB B
        DEC A
        LD C,A
        LD HL,EDITBUF
        LD E,B
        LD D,0
        ADD HL,DE
        LD D,H
        LD E,L
        INC HL
        LD B,0
        LD A,C
        OR A
        JR Z,EDITDECDONE
        LDIR
EDITDECDONE:
        LD HL,EDITLEN
        DEC (HL)
        JP EDITLOOP

        IF UISTD EQ 1
; Verify a caller-provided prefill/default before a renderer can emit it.
; HL=data, B=length; preserve HL/BC, carry on nonprintable input.
UE_ASCII:
        PUSH HL
        PUSH BC
        LD A,B
        OR A
        JR Z,UE_TXOK
UE_TXLP:
        LD A,(HL)
        CP 32
        JR C,UE_TXERR
        CP 127
        JR NC,UE_TXERR
        INC HL
        DJNZ UE_TXLP
UE_TXOK:
        POP BC
        POP HL
        OR A
        RET
UE_TXERR:
        POP BC
        POP HL
        SCF
        RET
        ENDIF
