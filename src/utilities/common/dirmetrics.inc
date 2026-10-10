; Add one selected physical directory entry without issuing BDOS calls.
; HL = entry, DE = DPB, BC = zero-initialized twelve-byte accumulator:
; allocated 128-byte records, logical records and entries (three DWORDs).
; Scratch/registers are disposable. Caller owns grouping and selection.
DM_ADD:
        LD (DM_ENTRY),HL
        LD (DM_DPB),DE
        LD (DM_TOTAL),BC
        LD DE,16
        ADD HL,DE
        LD DE,(DM_DPB)
        EX DE,HL
        LD BC,6
        ADD HL,BC
        LD A,(HL)
        EX DE,HL
        LD B,16
        LD C,0
        OR A
        JR Z,DM_BYTES
        LD B,8
DM_WORDS:
        LD A,(HL)
        INC HL
        OR (HL)
        JR Z,DM_WNEXT
        INC C
DM_WNEXT:
        INC HL
        DJNZ DM_WORDS
        JR DM_BLOCKS
DM_BYTES:
        LD A,(HL)
        OR A
        JR Z,DM_BNEXT
        INC C
DM_BNEXT:
        INC HL
        DJNZ DM_BYTES
DM_BLOCKS:
        LD L,C
        LD H,0
        LD DE,(DM_DPB)
        INC DE
        INC DE
        LD A,(DE)                  ; BSH: records per allocation block
DM_SCALE:
        OR A
        JR Z,DM_ALLOC
        ADD HL,HL
        DEC A
        JR DM_SCALE
DM_ALLOC:
        EX DE,HL
        LD HL,(DM_TOTAL)
        CALL DM_ADD32
        LD HL,(DM_DPB)
        LD BC,4
        ADD HL,BC
        LD A,(HL)                  ; EXM: logical extents per entry
        LD HL,(DM_ENTRY)
        LD BC,12
        ADD HL,BC
        AND (HL)
        LD L,A
        LD H,0
        LD B,7
DM_EXSHIFT:
        ADD HL,HL
        DJNZ DM_EXSHIFT
        EX DE,HL
        LD HL,(DM_ENTRY)
        LD BC,15
        ADD HL,BC
        LD C,(HL)
        LD B,0
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD HL,(DM_TOTAL)
        LD BC,4
        ADD HL,BC
        CALL DM_ADD32
        LD HL,(DM_TOTAL)
        LD BC,8
        ADD HL,BC
        LD DE,1
        JP DM_ADD32
DM_ADD32:
        LD A,(HL)
        ADD A,E
        LD (HL),A
        INC HL
        LD A,(HL)
        ADC A,D
        LD (HL),A
        INC HL
        LD A,(HL)
        ADC A,0
        LD (HL),A
        INC HL
        LD A,(HL)
        ADC A,0
        LD (HL),A
        RET
DM_ENTRY: DW 0
DM_DPB: DW 0
DM_TOTAL: DW 0
