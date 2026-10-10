; Pure live-DPB/allocation-vector free-space calculation. HL=DPB, DE=ALV.
; Return DF_VALUE as DWORD KiB. DSM is inclusive, bits are MSB first, and
; padding bits beyond DSM are ignored. No BDOS calls or vector modifications.
DF_COUNT:
        PUSH DE
        INC HL
        INC HL
        LD A,(HL)
        SUB 3
        LD (DF_SHIFT),A
        INC HL
        INC HL
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        POP HL
        XOR A
        LD (DF_VALUE),A
        LD (DF_VALUE+1),A
        LD (DF_VALUE+2),A
        LD (DF_VALUE+3),A
        LD C,80H
DF_BIT:
        LD A,(HL)
        AND C
        JR NZ,DF_USED
        PUSH HL
        LD HL,DF_VALUE
        INC (HL)
        JR NZ,DF_ADDED
        INC HL
        INC (HL)
        JR NZ,DF_ADDED
        INC HL
        INC (HL)
        JR NZ,DF_ADDED
        INC HL
        INC (HL)
DF_ADDED:
        POP HL
DF_USED:
        LD A,D
        OR E
        JR Z,DF_SCALE
        DEC DE
        SRL C
        JR NZ,DF_BIT
        LD C,80H
        INC HL
        JR DF_BIT
DF_SCALE:
        LD A,(DF_SHIFT)
        OR A
        RET Z
        LD B,A
DF_DOUBLE:
        LD HL,DF_VALUE
        SLA (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        DJNZ DF_DOUBLE
        RET
DF_VALUE: DS 4
DF_SHIFT: DB 0
