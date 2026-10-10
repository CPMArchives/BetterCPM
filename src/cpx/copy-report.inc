; Transient reporting owns separate FCB/DMA state after data/metadata completion.
CTR_INIT:
        PUSH HL
        PUSH BC
        XOR A
        LD (CTR_RUN),A
        LD (CTR_COP),A
        LD HL,CTR_TOTAL
        LD B,4
CTR_ZERO:
        LD (HL),A
        INC HL
        DJNZ CTR_ZERO
        POP BC
        POP HL
        RET
CTR_OK:
        CALL CTR_ALLOC
        JR C,CTR_BAD
        LD HL,CTR_COP
        INC (HL)
        LD HL,CTR_K
        LD DE,CTR_TOTAL
        LD B,4
        OR A
CTR_ADD:
        LD A,(DE)
        ADC A,(HL)
        LD (DE),A
        INC HL
        INC DE
        DJNZ CTR_ADD
        CALL CTPAIR
        LD DE,CTR_LBR
        CALL BC_PRINT
        LD HL,CTR_K
        CALL CTR_LOAD
        CALL CTR_DEC
        LD DE,CTR_KEND
        JP BC_PRINT
CTR_BAD:
        LD HL,CT_FAILS
        INC (HL)
        CALL CTPAIR
        LD DE,CTR_ERR
        JP BC_PRINT

; Count occupied slots from every physical directory entry, using DSM width.
CTR_ALLOC:
        CALL BC_CSELD
        LD C,31
        CALL BDOS
        INC HL
        INC HL
        LD A,(HL)
        SUB 3
        LD (CTR_SHIFT),A
        INC HL
        INC HL
        INC HL
        INC HL
        LD A,(HL)
        OR A
        LD A,1
        JR Z,CTR_WIDTH
        INC A
CTR_WIDTH:
        LD (CTR_WID),A
        LD HL,0
        LD (CTR_BLOCK),HL
        XOR A
        LD (CTR_FOUND),A
        LD HL,BC_NEWFCB
        LD DE,CTR_FCB
        LD BC,36
        LDIR
        LD A,'?'
        LD (CTR_FCB+12),A
        LD DE,BC_DMA
        LD C,26
        CALL BDOS
        LD DE,CTR_FCB
        LD C,17
CTR_SEARCH:
        CALL BDOS
        CP 0FFH
        JR Z,CTR_END
        LD E,A
        LD D,0
        LD A,1
        LD (CTR_FOUND),A
        LD A,E
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD HL,BC_DMA+16
        ADD HL,DE
        LD A,(CTR_WID)
        CP 2
        LD B,16
        JR NZ,CTR_SLOTS
        LD B,8
CTR_SLOTS:
        LD A,(HL)
        INC HL
        LD E,A
        LD A,(CTR_WID)
        CP 2
        LD A,E
        JR NZ,CTR_TEST
        OR (HL)
        INC HL
CTR_TEST:
        OR A
        JR Z,CTR_NEXT
        PUSH HL
        LD HL,(CTR_BLOCK)
        INC HL
        LD (CTR_BLOCK),HL
        POP HL
CTR_NEXT:
        DJNZ CTR_SLOTS
        LD DE,CTR_FCB
        LD C,18
        JR CTR_SEARCH
CTR_END:
        LD A,(CTR_FOUND)
        OR A
        SCF
        RET Z
        LD HL,(CTR_BLOCK)
        LD (CTR_K),HL
        LD HL,0
        LD (CTR_K+2),HL
        LD A,(CTR_SHIFT)
        OR A
        JR Z,CTR_READY
        LD B,A
CTR_SCALE:
        LD HL,CTR_K
        LD C,4
        OR A
CTR_SHL:
        RL (HL)
        INC HL
        DEC C
        JR NZ,CTR_SHL
        DJNZ CTR_SCALE
CTR_READY:
        OR A
        RET

CTR_SUM:
        LD A,(CTR_RUN)
        OR A
        RET Z
        LD A,(CT_COUNT)
        CP 2
        RET C
        LD A,(CTR_COP)
        OR A
        JR Z,CTR_SKIPPED
        CALL CTR_COUNT
        LD DE,CTR_CMSG
        CALL BC_PRINT
        LD HL,CTR_TOTAL
        CALL CTR_LOAD
        CALL CTR_DEC
        LD DE,CTR_KEND
        CALL BC_PRINT
CTR_SKIPPED:
        LD A,(CT_SKIPS)
        OR A
        JR Z,CTR_FAILED
        CALL CTR_COUNT
        LD DE,CTR_SMSG
        CALL BC_PRINT
CTR_FAILED:
        LD A,(CT_FAILS)
        OR A
        RET Z
        CALL CTR_COUNT
        LD DE,CTR_FMSG
        JP BC_PRINT
CTR_COUNT:
        PUSH AF
        LD DE,BC_NL
        CALL BC_PRINT
        POP AF
        PUSH AF
        LD L,A
        LD H,0
        LD (CTR_NUM),HL
        LD HL,0
        LD (CTR_NUM+2),HL
        CALL CTR_DEC
        LD DE,CTR_FILE
        CALL BC_PRINT
        POP AF
        CP 1
        RET Z
        LD A,'S'
        JP BC_PCHAR
CTR_LOAD:
        LD DE,CTR_NUM
        LD BC,4
        LDIR
        RET

; Unsigned 32-bit decimal via repeated division by ten, no BDOS numeric API.
CTR_DEC:
        LD HL,CTR_DIG
        LD (CTR_PTR),HL
CTR_DIV:
        LD B,32
        XOR A
CTR_BIT:
        LD HL,CTR_NUM
        LD C,4
        OR A
CTR_DSH:
        RL (HL)
        INC HL
        DEC C
        JR NZ,CTR_DSH
        RLA
        CP 10
        JR C,CTR_DNEXT
        SUB 10
        LD HL,CTR_NUM
        INC (HL)
CTR_DNEXT:
        DJNZ CTR_BIT
        ADD A,'0'
        LD HL,(CTR_PTR)
        LD (HL),A
        INC HL
        LD (CTR_PTR),HL
        LD HL,CTR_NUM
        LD B,4
        XOR A
CTR_NONZERO:
        OR (HL)
        INC HL
        DJNZ CTR_NONZERO
        JR NZ,CTR_DIV
        LD HL,(CTR_PTR)
CTR_DIGIT:
        DEC HL
        LD A,(HL)
        PUSH HL
        CALL BC_PCHAR
        POP HL
        LD DE,CTR_DIG
        OR A
        SBC HL,DE
        RET Z
        ADD HL,DE
        JR CTR_DIGIT
CTR_RUN: DB 0
CTR_COP: DB 0
CTR_TOTAL: DS 4
CTR_K: DS 4
CTR_BLOCK: DW 0
CTR_SHIFT: DB 0
CTR_WID: DB 0
CTR_FOUND: DB 0
CTR_FCB: DS 36
CTR_NUM: DS 4
CTR_DIG: DS 10
CTR_PTR: DW 0
CTR_LBR: DB ' [$'
CTR_KEND: DB 'K]',13,10,'$'
CTR_FILE: DB ' FILE$'
CTR_CMSG: DB ' COPIED [$'
CTR_SMSG: DB ' SKIPPED',13,10,'$'
CTR_FMSG: DB ' FAILED',13,10,'$'
CTR_ERR: DB ' [DATA COPIED; ALLOCATION REPORT UNAVAILABLE]',13,10,'$'
