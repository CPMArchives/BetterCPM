; CONFIG's legacy menu/approval callers own accepted keys, retries and defaults.
; A single printable transport token lets the shared controller complete one
; KEY event, retaining the original folded byte for the existing caller policy.
; No menu/approval mode switch or mutable context list is needed.
CC_PICK:
CC_ASK:
        CALL UC_RUN
        CP UI_SEND
        JR NZ,CC_BAD
        LD A,(CC_RAW)
        RET
CC_BAD:
        LD A,3                       ; malformed input configuration fails closed
        RET
CC_READ:
        CALL KEY
        LD (CC_RAW),A
        LD A,'?'
        RET
CC_IDLE:
        RET
CC_VALID:
        OR A
        RET
CC_TOKEN: DB '?'
CC_RAW: DB 0
UC_LIST: DW CC_TOKEN
UC_COUNT: DB 1
UC_DEF: DB 0
UC_VALUE: DB 0
CC_INPUT EQU CC_READ
UI_VALID EQU CC_VALID
UI_CLOSE EQU CC_IDLE
UC_PAINT EQU CC_IDLE
UC_ERROR EQU CC_IDLE
; @choice-modules@
