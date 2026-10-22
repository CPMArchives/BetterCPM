; Choice-only controller: independent of editor, buffer, word and text modules.
; UC_LIST pointer, UC_COUNT byte, UC_DEF byte (0=none), UC_VALUE byte
; are caller-owned. Choices must be printable ASCII; case-insensitive letters
; return uppercase. Repeated choices are harmless set members.
; Bind UIREAD, UC_PAINT, UC_ERROR, UI_VALID, UI_CLOSE.
; UC_ERROR displays HL's message while keeping choices/default visible.
UC_RUN:
        LD HL,(UC_LIST)
        LD A,H
        OR L
        JP Z,UI_BRET
        LD A,(UC_COUNT)
        OR A
        JP Z,UI_BRET
        LD B,A
UC_CFG:
        LD A,(HL)
        CP 32
        JP C,UI_BRET
        CP 127
        JP NC,UI_BRET
        INC HL
        DJNZ UC_CFG
        LD A,(UC_DEF)
        OR A
        JR Z,UC_DRAW
        CALL UC_MATCH
        JP C,UI_BRET
UC_DRAW:
        CALL UC_PAINT
UC_READ:
        CALL UIREAD
        CP 27
        JP Z,UI_CRET
        CP 3
        JP Z,UI_CRET
        CP 13
        JR Z,UC_DFLT
        LD D,UI_SEND
        JR UC_PICK
UC_DFLT:
        LD A,(UC_DEF)
        OR A
        JP Z,UI_CRET
        LD D,UI_DEF
UC_PICK:
        PUSH DE
        CALL UC_MATCH
        POP DE
        JR C,UC_DRAW
        LD (UC_VALUE),A
        LD A,D
        LD HL,UC_VALUE
        LD B,1
        CALL UI_CHECK
        JP NC,UI_FIN
        CALL UC_ERROR
        JR UC_READ
UC_MATCH:
        CALL UC_UPPER
        LD E,A
        LD HL,(UC_LIST)
        LD A,(UC_COUNT)
        LD B,A
UC_SCAN:
        LD A,(HL)
        CALL UC_UPPER
        CP E
        JR Z,UC_FOUND
        INC HL
        DJNZ UC_SCAN
        SCF
        RET
UC_FOUND:
        LD A,E
        OR A
        RET
UC_UPPER:
        CP 'a'
        RET C
        CP 'z'+1
        RET NC
        AND 05FH
        RET
