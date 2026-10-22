; SYSGEN's compatibility binding for the choice-only shared controller.
; Prompts are printed by the existing installation/export paths before entry.
; Preserve the specification: only Y authorizes; ANY other key declines.
; No default, retry, extra prompt, typeahead flush or editor/field buffer.
SG_ASK:
        CALL UC_RUN
        CP UI_SEND
        JR NZ,SG_NO
        LD A,(UC_VALUE)
        RET
SG_NO:
        XOR A
        RET
SG_READ:
        CALL KEY
        CP 'Y'
        RET Z
        CP 'N'
        RET Z
        LD A,27
        RET
SG_VALID:
        OR A
        RET
SG_IDLE:
        RET
SG_LIST: DB 'YN'
UC_LIST: DW SG_LIST
UC_COUNT: DB 2
UC_DEF: DB 0
UC_VALUE: DB 0
UIREAD EQU SG_READ
UI_VALID EQU SG_VALID
UI_CLOSE EQU SG_IDLE
UC_PAINT EQU SG_IDLE
UC_ERROR EQU SG_IDLE
; @choice-modules@
