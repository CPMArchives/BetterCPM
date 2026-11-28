        INCLUDE state.inc
; RomWBW HBIOS standard entry, never emulator-specific ports.
IO_COLD:
PL_INIT:
        LD A,(WB_IOBYTE)
        LD (3),A
        XOR A
        LD (LY_RSTA),A
        RET
PL_CONST:
        PUSH BC
        LD BC,0200H
        CALL 0FFF0H
        POP BC
        OR A
        RET
PL_CONIN:
        PUSH BC
        PUSH DE
        LD BC,0
        CALL 0FFF0H
        LD A,E
        POP DE
        POP BC
        RET
PL_CONOT:
        LD A,C
        CP 28
        JR Z,WB_CLEAR
WB_OUT:
        LD A,C
; Raw A-byte leaf for checked display modules. Preserve all caller registers.
; This does not call BDOS, translate controls, or re-enter the monitor router.
WB_TXA:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD BC,0100H
        CALL 0FFF0H
        POP HL
        POP DE
        POP BC
        POP AF
        RET
WB_CLEAR:
        PUSH HL
        LD HL,WB_CLS
WB_CLOOP:
        LD C,(HL)
        INC HL
        LD A,C
        OR A
        JR Z,WB_CDONE
        CALL WB_OUT
        JR WB_CLOOP
WB_CDONE:
        POP HL
        RET
PL_CURSOR:
        XOR A
        RET
WB_CLS: DB 27,'[2J',27,'[H',0
        INCLUDE checked-load.inc
