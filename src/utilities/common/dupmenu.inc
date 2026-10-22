; DUP menu and drive-selection binding. Keep the common CHOICE presentation.
; Callers own invalid-choice dispatch; all original bytes are returned folded
; exactly as KEY supplies them. The controller's ? member carries unknown keys.
; Ctrl-C is returned to the caller rather than reinterpreted by the controller.
DP_MENU:
        LD A,1
        JR DU_SHOW
DP_DRIVE:
        LD A,2
DU_SHOW:
        LD (DU_MODE),A
        JP CHOICE
; CHOICE's selected input hook, only in expanded DUP source.
DU_PICK:
        LD HL,DU_MLIST
        LD B,4
        LD A,(DU_MODE)
        CP 1
        JR Z,DU_SETUP
        LD HL,DU_DLIST
        LD B,5
DU_SETUP:
        LD (UC_LIST),HL
        LD A,B
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        CALL UC_RUN
        CP UI_SEND
        JR Z,DU_RESET
        LD A,3                      ; malformed configuration cannot dispatch stale A
        LD (DU_RAW),A
DU_RESET:
        ; Restore strict confirmation context on every menu return, before
        ; FORMAT/COPY can ask permission. Do not reset it inside DP_ASK: its
        ; malformed-config guard must continue failing closed without input.
        LD HL,UY_LIST
        LD (UC_LIST),HL
        LD A,2
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        LD (DU_MODE),A
        LD A,(DU_RAW)
        RET
DU_READ:
        LD A,(DU_MODE)
        OR A
        JP Z,UY_READ
        CALL KEY
        LD (DU_RAW),A
        CALL UC_MATCH
        RET NC
        LD A,'?'
        RET
DU_MLIST: DB 'ABC?'
DU_DLIST: DB 'ABCD?'
DU_MODE: DB 0
DU_RAW: DB 0
