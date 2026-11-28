        INCLUDE state.inc
; RomWBW HBIOS standard entry, never emulator-specific ports.
IO_COLD:
PL_INIT:
        LD A,095H
        LD (3),A
        XOR A
        LD (LY_RSTA),A
        LD BC,0F8E0H
        CALL 0FFF0H
        JP NZ,WB_HALT
        LD A,E
        OR A
        JP NZ,WB_HALT                  ; initial target is slice zero only
        LD A,D
        LD (WB_UNIT),A
        LD BC,0F8F2H
        CALL 0FFF0H
        JP NZ,WB_HALT
        LD A,D
        LD (WB_BANK),A
        LD B,0F3H
        CALL 0FFF0H
        LD A,C
        LD (WB_USER),A
        LD HL,512
        LD B,0F6H
        CALL 0FFF0H
        JP NZ,WB_HALT
        LD (WB_HEAP),HL
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
        PUSH BC
        PUSH DE
        LD E,C
        LD BC,0100H
        CALL 0FFF0H
        POP DE
        POP BC
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
WB_HALT:
        LD C,'!'
        CALL WB_OUT
        HALT
        JR WB_HALT
        INCLUDE checked-load.inc
