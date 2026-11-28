        INCLUDE hardware.inc
IO_COLD:
PL_INIT:
        LD A,095H
        LD (0003H),A
        XOR A
        LD (LY_RSTA),A
        LD A,3
        OUT (AL_SSTAT),A
        LD A,011H
        OUT (AL_SSTAT),A
        RET
PL_CONST:
        JP AL_CONST
PL_CONIN:
        JP AL_CONIN
PL_CONOT:
        LD A,C
        CP 28
        JP NZ,AL_CONOUT
        LD HL,AL_CLS
        JP AL_STRING
PL_CURSOR:
        XOR A
        RET
AL_CLS: DB 27,'[2J',27,'[H',0
        INCLUDE console.inc
        INCLUDE checked-load.inc
