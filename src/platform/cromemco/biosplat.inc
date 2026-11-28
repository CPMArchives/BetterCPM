        INCLUDE hardware.inc
IO_COLD:
PL_INIT:
        LD A,095H
        LD (0003H),A
        XOR A
        LD (LY_RSTA),A
        LD A,0C0H
        OUT (CM_SSTAT),A
        LD A,1
        OUT (002H),A
        XOR A
        OUT (002H),A
        RET
PL_CONST:
        JP CM_CONST
PL_CONIN:
        JP CM_CONIN
PL_CONOT:
        LD A,C
        CP 28
        JP NZ,CM_CONOUT
        LD HL,CM_CLS
        JP CM_STRING
PL_CURSOR:
        XOR A
        RET
CM_CLS: DB 27,'[2J',27,'[H',0
        INCLUDE console.inc
        INCLUDE checked-load.inc
