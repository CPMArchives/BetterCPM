; NOAH choice binding: immediate, case-insensitive Y/N/A/C; Enter defaults N.
; ESC/Ctrl-C cancel the whole operation. Protected questions offer only Y/N;
; /Y and ordinary All never authorize protection overrides.
NI_ASK:
        LD (NI_PROTECTED),A
        LD HL,NI_ORDINARY
        LD B,4
        OR A
        JR Z,NI_SETUP
        LD HL,NI_PROTECTION
        LD B,2
NI_SETUP:
        LD (UC_LIST),HL
        LD A,B
        LD (UC_COUNT),A
        LD A,'N'
        LD (UC_DEF),A
        LD A,1
        LD (NI_WAIT),A
        CALL UC_RUN
        LD B,A
        XOR A
        LD (NI_WAIT),A
        LD A,B
        CP UI_SEND
        JR Z,NI_ANSWER
        CP UI_DEF
        JR Z,NI_ANSWER
        JP NX_POLL_STOP
NI_ANSWER:
        LD A,(UC_VALUE)
        CP 'C'
        JP Z,NX_POLL_STOP
        CP 'A'
        JR NZ,NI_NOT_ALL
        LD A,1
        LD (NS_ALL),A
        OR A
        RET
NI_NOT_ALL:
        CP 'Y'
        JR Z,NI_YES
        XOR A
        RET
NI_YES:
        LD A,1
        OR A
        RET
; Safe source-preflight boundary only. No output/staging or live input may
; remain when called. /Y never waits; Enter defaults to Skip, not Retry.
NI_FAILURE:
        LD A,(NS_YES)
        OR A
        LD A,'S'
        RET NZ
        LD A,1
        LD (NI_FAILURE_MODE),A
        LD (NI_WAIT),A
        LD HL,NI_FAILURE_KEYS
        LD (UC_LIST),HL
        LD A,3
        LD (UC_COUNT),A
        LD A,'S'
        LD (UC_DEF),A
        CALL UC_RUN
        LD B,A
        XOR A
        LD (NI_WAIT),A
        LD (NI_FAILURE_MODE),A
        LD A,B
        CP UI_SEND
        JR Z,NI_FAILURE_VALUE
        CP UI_DEF
        JR NZ,NI_FAILURE_ABORT
NI_FAILURE_VALUE:
        LD A,(UC_VALUE)
        CP 'A'
        JR Z,NI_FAILURE_ABORT
        OR A
        RET
NI_FAILURE_ABORT:
        LD DE,NI_ABORT_TEXT
        CALL NH_PRINT
        JP NX_POLL_STOP
NI_READ:
        LD C,6
        LD E,0FFH
        CALL AC_BDOS
        OR A
        JR Z,NI_READ
        RET
NI_PAINT:
        LD A,(NI_FAILURE_MODE)
        OR A
        LD DE,NI_FAILURE_TEXT
        JP NZ,NH_PRINT
        LD A,(NW_PROMPT)
        OR A
        JP NZ,NW_PAINT
        LD HL,NX_FINAL
        CALL NX_PRINT_FCB
        LD A,(NI_PROTECTED)
        OR A
        LD DE,NI_NORMAL_TEXT
        JP Z,NH_PRINT
        LD DE,NI_RO_TEXT
        CP 1
        JP Z,NH_PRINT
        LD DE,NI_SYS_TEXT
        CP 2
        JP Z,NH_PRINT
        LD DE,NI_BOTH_TEXT
        JP NH_PRINT
NI_ERROR:
        LD DE,NI_INVALID_TEXT
        CALL NH_PRINT
        JP NI_PAINT
NI_VALID:
        OR A
        RET
NI_CLOSE:
        CP UI_SEND
        JR Z,NI_ECHO
        CP UI_DEF
        JR NZ,NI_NEWLINE
NI_ECHO:
        LD A,(UC_VALUE)
        LD E,A
        LD C,2
        CALL AC_BDOS
NI_NEWLINE:
        LD DE,NH_NEWLINE
        JP NH_PRINT
UIREAD EQU NI_READ
UI_VALID EQU NI_VALID
UI_CLOSE EQU NI_CLOSE
UC_PAINT EQU NI_PAINT
UC_ERROR EQU NI_ERROR
; @choice-modules@
NI_FAILURE_KEYS: DB 'RSA'
NI_FAILURE_TEXT: DB 'Retry/Skip/Abort? R/S/A [S]: ','$'
NI_ABORT_TEXT: DB 'NOAH: Cancelled; remaining work unprocessed.',13,10,'$'
NI_ORDINARY: DB 'YNAC'
NI_PROTECTION: DB 'YN'
NI_NORMAL_TEXT: DB ' exists. Replace? Y/N/A/C [N]: ','$'
NI_RO_TEXT: DB ' is protected [RO]. Replace? Y/N [N]: ','$'
NI_SYS_TEXT: DB ' is protected [SYS]. Replace? Y/N [N]: ','$'
NI_BOTH_TEXT: DB ' is protected [RO SYS]. Replace? Y/N [N]: ','$'
NI_INVALID_TEXT: DB 13,10,'Invalid choice. ','$'
NOAH_INPUT_DATA MACRO
NI_FAILURE_MODE: DB 0
NI_PROTECTED: DB 0
NI_WAIT: DB 0
UC_LIST: DW 0
UC_COUNT: DB 0
UC_DEF: DB 0
UC_VALUE: DB 0
        ENDM
