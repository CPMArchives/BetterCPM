; Interactive B..D selection shares the confirmation controller, not its policy.
; KEY folding and the caller's invalid-key / Ctrl-C dispatch remain unchanged.
SG_DRIVE:
        LD A,1
        LD (SG_MODE),A
        LD HL,SG_LIST
        LD (UC_LIST),HL
        LD A,4
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        CALL UC_RUN
        CP UI_SEND
        JR Z,SG_RESET
        LD A,3                      ; fail closed, never dispatch a stale drive
        LD (SG_RAW),A
SG_RESET:
        LD HL,UY_LIST
        LD (UC_LIST),HL
        LD A,2
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        LD (SG_MODE),A
        LD A,(SG_RAW)
        RET
SG_READ:
        LD A,(SG_MODE)
        OR A
        JP Z,UY_READ
        CALL KEY
        LD (SG_RAW),A
        CALL UC_MATCH
        RET NC
        LD A,'?'
        RET
SG_LIST: DB 'BCD?'
SG_MODE: DB 0
SG_RAW: DB 0
; Approval must not silently repair malformed confirmation configuration.
SG_ASK:
        XOR A
        LD (SG_MODE),A
; @confirmation@
