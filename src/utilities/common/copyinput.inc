; Transient COPY input binding. MOVE/resident RCP keep their existing contract.
; Choices use raw BDOS 6: 0/CR/LF wait, Ctrl-C aborts. Unknown bytes (including
; ESC) are echoed by the caller and take the existing help/repaint path.
; Map unknown input to the controller's explicit help member, retaining the
; original folded byte for the legacy caller. This is not silent filtering.
CU_OW:
        LD HL,CU_OLIST
        LD B,6
        JR CU_ASK
CU_VER:
        LD HL,CU_VLIST
        LD B,3
CU_ASK:
        LD (UC_LIST),HL
        LD A,B
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        CALL UC_RUN
        CP UI_SEND
        JR NZ,CU_ABORT
        LD A,(CU_RAW)
        RET
CU_ABORT:
        LD A,3
        RET
CU_READ:
        LD E,0FFH
        LD C,6
        CALL BDOS
        OR A
        JR Z,CU_READ
        CP 3
        RET Z
        CP 13
        JR Z,CU_READ
        CP 10
        JR Z,CU_READ
        CALL UC_UPPER
        LD (CU_RAW),A
        CALL UC_MATCH
        RET NC
        LD A,'?'
        RET
CU_VALID:
        OR A
        RET
CU_IDLE:
        RET
CU_OLIST: DB 'YNORS?'
CU_VLIST: DB 'RS?'
CU_RAW: DB 0
UC_LIST: DW 0
UC_COUNT: DB 0
UC_DEF: DB 0
UC_VALUE: DB 0
UIREAD EQU CU_READ
UI_VALID EQU CU_VALID
UI_CLOSE EQU CU_IDLE
UC_PAINT EQU CU_IDLE
UC_ERROR EQU CU_IDLE
; @choice-modules@

; COPY has no Ctrl-U clear key. UA_PUT supplies literal append for that byte;
; CR/LF, Ctrl-C, BS/DEL and ordinary echo remain caller-specific decisions.
CU_EDIT:
        LD A,(CTRLEN)
        LD (CU_OLDL),A
        LD A,(CTRCHAR)
        CP 21
        JR Z,CU_LIT
        CALL UA_KEY
        JR CU_EVENT
CU_LIT:
        CALL UA_PUT
CU_EVENT:
        OR A
        RET NZ                      ; submit, abort and overflow never echo here
        LD A,(CTRCHAR)
        CP 8
        JR Z,CU_BACK
        CP 127
        JR Z,CU_BACK
        CALL BC_PCHAR
        XOR A
        RET
CU_BACK:
        LD A,(CU_OLDL)
        OR A
        RET Z
        LD DE,CTRERASE
        CALL BC_PRINT
        XOR A
        RET
CU_OLDL: DB 0
UA_BUF EQU CTRBUF
UA_LEN EQU CTRLEN
UA_FULL EQU CTROVER
UA_MAX: DB 0
; @append-module@
