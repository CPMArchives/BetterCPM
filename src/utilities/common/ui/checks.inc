; Shared validation and completion, no editing or display dependency.
; Candidate: A=UI_SEND/UI_DEF, HL=data, B=length (may be zero).
; UI_VALID is read-only: carry clear=valid, carry set with HL=error text.
; Hooks may clobber all general registers, but must balance the stack.
UI_CHECK:
        PUSH AF
        PUSH HL
        PUSH BC
        CALL UI_VALID
        JR C,UI_CBAD
        POP BC
        POP HL
        POP AF
        OR A
        RET
UI_CBAD:
        POP DE
        POP DE
        POP DE
        SCF
        RET
UI_FIN:
        PUSH AF
        PUSH HL
        PUSH BC
        CALL UI_CLOSE
        POP BC
        POP HL
        POP AF
        OR A
        RET
UI_CRET:
        LD A,UI_ABORT
        LD HL,0
        LD B,0
        JP UI_FIN
UI_BRET:
        LD A,UI_BAD
        LD HL,0
        LD B,0
        SCF
        RET
