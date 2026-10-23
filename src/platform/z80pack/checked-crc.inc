; DE=input, BC=nonzero byte count; HL=CRC-16/CCITT-FALSE result.
; AF,BC,DE,HL clobbered; IX preserved. No memory writes except stack.
Z_CRC:
        LD HL,0FFFFH
Z_CRBYTE:
        LD A,(DE)
        INC DE
        XOR H
        LD H,A
        PUSH BC
        LD B,8
Z_CRBIT:
        ADD HL,HL
        JR NC,Z_CRNEXT
        LD A,L
        XOR 021H
        LD L,A
        LD A,H
        XOR 010H
        LD H,A
Z_CRNEXT:
        DJNZ Z_CRBIT
        POP BC
        DEC BC
        LD A,B
        OR C
        JR NZ,Z_CRBYTE
        RET
Z_CBACK: DW 0
