; Shared single-line editor, legacy extraction profile.
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
; Defaults, distinct event results, optional keys and other profiles are pending.
;
; Entry editor keeps raw case and ASCII spaces. 95 characters accommodate 32
; separated hex pairs. H/A validation separately enforces decoded length.
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
EDITKEY:
        CP 27
        JR Z,EDITCANCEL
        CP 13
        JR Z,EDITSUBMIT
        CP 19
        JR Z,EDITLEFT
        CP 4
        JR Z,EDITRIGHT
        CP 8
        JR Z,EDITBACK
        CP 7
        JP Z,EDITDELETE
        CP 32
        JR C,EDITREAD
        CP 127
        JR NC,EDITREAD
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
EDITLEFT:
        LD HL,EDITCUR
        LD A,(HL)
        OR A
        JP Z,EDITREAD
        DEC (HL)
        JP EDITLOOP
EDITRIGHT:
        LD A,(EDITCUR)
        LD HL,EDITLEN
        CP (HL)
        JP Z,EDITREAD
        LD HL,EDITCUR
        INC (HL)
        JP EDITLOOP
EDITBACK:
        LD A,(EDITCUR)
        OR A
        JP Z,EDITREAD
        DEC A
        LD (EDITCUR),A
EDITDELETE:
        LD A,(EDITCUR)
        LD B,A
        LD A,(EDITLEN)
        CP B
        JP Z,EDITREAD
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
