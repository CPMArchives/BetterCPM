; ERA's choice-only compatibility binding. It does not change erase policy.
; E_KEY returns one raw unechoed byte and preserves caller registers.
; Y/N: silent retry on invalid input. Recovery: repeat R/S/A/? on invalid input.
; Enter/ESC remain invalid responses, NOT defaults or cancellation aliases.
; Ctrl-C cancels both contexts; callers retain echo/help/skip/retry/abort logic.
EU_YN:
        XOR A
        JR EU_ASK
EU_RCHO:
        LD A,1
EU_ASK:
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        LD (EU_MODE),A
        OR A
        LD HL,EU_YLIST
        LD B,2
        JR Z,EU_SETUP
        LD HL,EU_RLIST
        LD B,4
EU_SETUP:
        LD (UC_LIST),HL
        LD A,B
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        CALL UC_RUN
        CP UI_SEND
        JR NZ,EU_ABORT
        LD A,(UC_VALUE)
        JR EU_DONE
EU_ABORT:
        LD A,3
EU_DONE:
        POP IX
        POP HL
        POP DE
        POP BC
        RET
EU_READ:
        CALL E_KEY
        CP 27
        JR Z,EU_SKIP
        CP 13
        RET NZ
EU_SKIP:
        XOR A
        RET
EU_PAINT:
        LD A,(EU_MODE)
        OR A
        RET Z
        LD DE,E_RECOV
        JP E_PRINT
EU_VALID:
        OR A
        RET
EU_IDLE:
        RET
EU_YLIST: DB 'YN'
EU_RLIST: DB 'RSA?'
EU_MODE: DB 0
UC_LIST: DW 0
UC_COUNT: DB 0
UC_DEF: DB 0
UC_VALUE: DB 0
UIREAD EQU EU_READ
UI_VALID EQU EU_VALID
UI_CLOSE EQU EU_IDLE
UC_PAINT EQU EU_PAINT
UC_ERROR EQU EU_IDLE
; @choice-modules@
