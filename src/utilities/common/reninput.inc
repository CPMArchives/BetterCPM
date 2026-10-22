; REN choice compatibility binding. Keep BDOS 1 echo and legacy folding.
; The replacement-filename editor is separate and deliberately unchanged.
; Enter/ESC are invalid, Ctrl-C aborts, and invalid choices retry without
; consuming a second acknowledgment key. No implicit default or input flush.
RU_YN:
        XOR A
        JR RU_ASK
RU_COL:
        LD A,1
        JR RU_ASK
RU_FAIL:
        LD A,2
RU_ASK:
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        LD (RU_MODE),A
        OR A
        LD HL,RU_YLIST
        LD B,2
        JR Z,RU_SETUP
        LD HL,RU_CLIST
        DEC A
        JR Z,RU_FOUR
        LD HL,RU_FLIST
RU_FOUR:
        LD B,4
RU_SETUP:
        LD (UC_LIST),HL
        LD A,B
        LD (UC_COUNT),A
        XOR A
        LD (UC_DEF),A
        CALL UC_RUN
        CP UI_SEND
        JR NZ,RU_ABORT
        LD A,(UC_VALUE)
        JR RU_DONE
RU_ABORT:
        LD A,3
RU_DONE:
        POP IX
        POP HL
        POP DE
        POP BC
        RET
RU_READ:
        LD C,1
        CALL BDOS
        CP 3
        RET Z
        CP '?'
        RET Z
        CP 27
        JR Z,RU_SKIP
        CP 13
        JR Z,RU_SKIP
        ; Preserve historical AND 5F, including high-bit input aliases.
        AND 5FH
        CP 3
        JR Z,RU_SKIP
        CP 27
        JR Z,RU_SKIP
        CP 13
        RET NZ
RU_SKIP:
        XOR A
        RET
RU_PAINT:
        LD A,(RU_MODE)
        OR A
        RET Z
        DEC A
        JR NZ,RU_FPAINT
        CALL R_MAPPING
        LD DE,R_COLMSG
        JP BC_PRINT
RU_FPAINT:
        LD DE,R_FPRE
        CALL BC_PRINT
        LD HL,RF_BEST
        CALL R_NAME
        LD DE,R_FAILASK
        JP BC_PRINT
RU_VALID:
        OR A
        RET
RU_IDLE:
        RET
RU_YLIST: DB 'YN'
RU_CLIST: DB 'NSA?'
RU_FLIST: DB 'RSA?'
RU_MODE: DB 0
UC_LIST: DW 0
UC_COUNT: DB 0
UC_DEF: DB 0
UC_VALUE: DB 0
UIREAD EQU RU_READ
UI_VALID EQU RU_VALID
UI_CLOSE EQU RU_IDLE
UC_PAINT EQU RU_PAINT
UC_ERROR EQU RU_IDLE
; @choice-modules@
