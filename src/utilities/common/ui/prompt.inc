; Synchronous standard text controller. Call UE_INIT first.
; Caller owns UP_MODE byte, UP_DPTR pointer and UP_DLEN byte.
; Bind UIREAD, UIDRAW, UIMESSAGE, UILIMITMSG, UI_NEED, UI_VALID,
; UI_CLOSE. Rendering shows the separate default from the caller's config.
; No nested prompts. Application state is committed by the caller after return.
UP_RUN:
        LD A,(UP_MODE)
        CP 4
        JP NC,UI_BRET
        CP UP_DEF
        JR NZ,UP_DRAW
        LD A,(EDITLEN)
        OR A
        JP NZ,UI_BRET
        LD HL,(UP_DPTR)
        LD A,H
        OR L
        JP Z,UI_BRET
        LD A,(UP_DLEN)
        OR A
        JP Z,UI_BRET
        LD B,A
        LD A,(EDITMAX)
        CP B
        JP C,UI_BRET
        CALL UE_ASCII
        JP C,UI_BRET
UP_DRAW:
        CALL UIDRAW
UP_READ:
        CALL UIREAD
        CALL UE_KEY
        CP UI_SKIP
        JR Z,UP_READ
        CP UI_LIMIT
        JR Z,UP_LIMIT
        CP UI_ABORT
        JP Z,UI_CRET
        CP UI_SEND
        JR NZ,UP_DRAW
        LD A,(EDITLEN)
        OR A
        JR NZ,UP_TYPED
        LD A,(UP_MODE)
        CP UP_CAN
        JP Z,UI_CRET
        CP UP_NEED
        JR Z,UP_REQ
        CP UP_DEF
        JR Z,UP_DFLT
UP_TYPED:
        LD HL,EDITBUF
        LD A,(EDITLEN)
        LD B,A
        LD A,UI_SEND
        JR UP_CHECK
UP_DFLT:
        LD HL,(UP_DPTR)
        LD A,(UP_DLEN)
        LD B,A
        LD A,UI_DEF
UP_CHECK:
        CALL UI_CHECK
        JP NC,UI_FIN
        JR UP_MSG
UP_REQ:
        LD HL,UI_NEED
        JR UP_MSG
UP_LIMIT:
        LD HL,UILIMITMSG
UP_MSG:
        CALL UIMESSAGE
        JR UP_READ
