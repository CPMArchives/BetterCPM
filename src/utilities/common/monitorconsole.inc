; Internal clear/home through BIOS API 1.7, preserving utility loop registers.
UI_CLEAR:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD HL,(1)                      ; public WBOOT vector is BIOS+3
        LD DE,63                       ; MONCALL is BIOS+66
        ADD HL,DE
        LD A,4
        CALL UI_JUMP
        POP HL
        POP DE
        POP BC
        POP AF
        RET
UI_JUMP:
        JP (HL)
