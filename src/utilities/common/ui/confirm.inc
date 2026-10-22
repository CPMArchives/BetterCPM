; One-key compatibility binding for the shared choice-only controller.
; Caller supplies KEY, which returns one uppercase-folded, unechoed key.
; Prompts are printed by the utility before entry.
; Preserve the specification: only Y authorizes; ANY other key declines.
; No default, retry, extra prompt, typeahead flush or editor/field buffer.
UI_ASK:
        CALL UC_RUN
        CP UI_SEND
        JR NZ,UY_NO
        LD A,(UC_VALUE)
        RET
UY_NO:
        XOR A
        RET
UY_READ:
        CALL KEY
        CP 'Y'
        RET Z
        CP 'N'
        RET Z
        LD A,27
        RET
UY_VALID:
        OR A
        RET
UY_IDLE:
        RET
UY_LIST: DB 'YN'
UC_LIST: DW UY_LIST
UC_COUNT: DB 2
UC_DEF: DB 0
UC_VALUE: DB 0
UIREAD EQU UY_READ
UI_VALID EQU UY_VALID
UI_CLOSE EQU UY_IDLE
UC_PAINT EQU UY_IDLE
UC_ERROR EQU UY_IDLE
; @choice-modules@
