; Part 7 prototype. All executable bytes are checked before entry.
; Initial RSX control runs in CFG; it leaves the live resolver in place.
PL_RELOAD:
        LD SP,0100H
        LD HL,LY_LOAD
        LD DE,60
        LD B,8
        CALL LY_DISK+15
        JR NZ,Z_HALT
        LD DE,LY_LOAD
Z_EREL: LD HL,0
        CALL Z_VERIFY
        JR NZ,Z_HALT
        LD SP,LY_STKT
        JP LY_LOAD
Z_HALT:
        LD A,'!'
        OUT (1),A
        HALT
        JR Z_HALT

PL_OVLOAD:
        LD HL,LY_CFG
        LD DE,68
        LD B,8
        CALL LY_DISK+15
        RET NZ
        LD DE,LY_CFG
Z_ECTL: LD HL,0
        JP Z_VERIFY

PL_RSXLOAD:
        OR A
        JR NZ,Z_RESTORE
        LD H,A
        LD L,A
        LD (LY_CBACK),HL
        LD HL,LY_CFG
        LD DE,76
        LD B,8
        CALL LY_DISK+15
        RET NZ
        LD DE,LY_CFG
Z_EENT: LD HL,0
        CALL Z_VERIFY
        RET NZ
        LD HL,LY_CFG+03FDH
        LD DE,LY_RSX+03FDH
        LD BC,3
        LDIR
        XOR A
        RET
Z_RESTORE:
        CP 3
        JR NZ,Z_BADLOAD
        LD HL,(LY_CBACK)
        LD A,H
        OR L
        RET Z
        LD DE,LY_RSX
        LD BC,03F4H
        LDIR
        XOR A
        RET
Z_BADLOAD:
        LD A,0FFH
        OR A
        RET
Z_VERIFY:
        PUSH HL
        PUSH DE
        LD HL,1000
        ADD HL,DE
        LD DE,LY_CID
        CALL LY_CCMP
        POP DE
        JR NZ,Z_IDBAD
        LD BC,0400H
        CALL LY_CCRC
        POP DE
        OR A
        SBC HL,DE
        LD A,H
        OR L
        RET
Z_IDBAD:
        POP HL
        RET
