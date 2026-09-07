; CPMSIM CONSOLE AND SYSTEM CARRIERS -- 07-Sep-2026
; All resident addresses come from the common layout. The host terminal
; supplies the screen; ANSI sequences replace the Model 4 display memory.
PL_INIT:
        XOR A
        LD (LY_HIST),A
        LD (LY_RSTA),A
        RET
PL_CONST:
        IN A,(0)
        AND 1
        RET
PL_CONIN:
        CALL PL_CONST
        JR Z,PL_CONIN
        IN A,(1)
        RET
PL_CONOT:
        LD A,C
        CP 28
        JR Z,Z_CLEAR
        OUT (1),A
        RET
Z_CLEAR:
        LD HL,Z_CLS
Z_STRING:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        OUT (1),A
        JR Z_STRING
PL_CURSOR:
; No inverse-character service; the common utilities use plain output.
        XOR A
        RET
Z_CLS:  DB 27,'[2J',27,'[H',0
PL_RELOAD:
        LD SP,0100H
        LD HL,LY_LOAD
        LD DE,60
        LD B,8
        CALL LY_DISK+15
        JR NZ,Z_HALT
        LD SP,LY_STKT
        JP LY_LOAD
PL_OVLOAD:
        LD HL,LY_CFG
        LD DE,68
        LD B,8
        JP LY_DISK+15
PL_RSXLOAD:
        LD HL,LY_RSX
        LD DE,76
        LD B,8
        JP LY_DISK+15
Z_HALT:
        LD A,'!'
        OUT (1),A
        HALT
        JR Z_HALT
