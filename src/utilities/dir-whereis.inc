; WHEREIS uses a bounded raw directory snapshot through the existing ERA adapter.
DW_PARSE:
        LD A,(DW_MODE)
        OR A
        RET Z
        LD A,(DW_OTHER)
        OR A
        JR NZ,DW_BAD
        LD A,(DP_HAS)
        OR A
        JR Z,DW_BAD
        OR A
        RET
DW_BAD:
        LD A,1
        LD (DP_ERROR),A
        JP DP_BAD
DW_LONG:
        INC HL
        LD DE,DW_WORD+1
        LD B,7
DW_MATCH:
        LD A,(HL)
        AND 0DFH
        LD C,A
        LD A,(DE)
        CP C
        JP NZ,DP_OPBAD
        INC HL
        INC DE
        DJNZ DW_MATCH
        LD A,1
        LD (DW_MODE),A
        JP DP_OK
DW_START:
        LD DE,BC_NL
        CALL BC_PRINT
        LD HL,(1)
        DEC HL
        DEC HL
        DEC HL
        LD (ER_BASE),HL
        XOR A
        LD (DW_FAIL),A
        LD HL,0
        LD (DW_TOTAL),HL
        LD (DW_TOTAL+2),HL
        LD (DW_INDEX),HL
        LD A,0FFH
        LD (DW_DRIVE),A
        ; A colon distinguishes any explicit selector from global default.
        LD HL,DP_ARG
        LD A,(DP_ALEN)
        LD B,A
DW_QUAL:
        LD A,(HL)
        CP ':'
        JR Z,DW_NEXT
        INC HL
        DJNZ DW_QUAL
        LD HL,DU_MAP
        LD B,64
        XOR A
DW_ZERO:
        LD (HL),A
        INC HL
        DJNZ DW_ZERO
        XOR A
        LD (DW_QUERY),A
DW_GLOBAL:
        CALL DW_CONFIG
        JR C,DW_GNEXT
        LD A,(DW_BIND+1)
        CP 4
        JR NC,DW_GNEXT
        LD A,(DW_QUERY)
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,DU_MAP
        ADD HL,DE
        LD B,4
DW_USERS:
        LD (HL),0FFH
        INC HL
        DJNZ DW_USERS
DW_GNEXT:
        LD HL,DW_QUERY
        INC (HL)
        LD A,(HL)
        CP 4
        JR NZ,DW_GLOBAL
DW_NEXT:
        LD BC,(DW_INDEX)
        CALL DU_NEXT
        JP C,DW_FINISH
        LD (DW_INDEX),BC
        LD A,E
        LD (DW_USER),A
        LD A,D
        LD (DW_QUERY),A
        LD HL,DW_DRIVE
        CP (HL)
        JR Z,DW_REUSE
        LD (HL),A
        XOR A
        LD (DW_OK),A
        CALL DW_CONFIG
        JP C,DW_SKIP
        LD A,(DW_BIND+1)
        CP 4
        JP NC,DW_UFAIL
        LD A,(DW_DRIVE)
        CALL ER_OPEN
        JP C,DW_UFAIL
        LD HL,(0006H)
        LD DE,0100H+04000H
        OR A
        SBC HL,DE
        JP C,DW_CAP
        PUSH HL
        LD DE,DT_BUFFER+24
        OR A
        SBC HL,DE
        POP HL
        JP C,DW_CAP
        LD (DW_SNAP),HL
        LD (DT_LIMIT),HL
        EX DE,HL
        LD BC,04000H
        CALL ER_SNAP
        JP C,DW_READERR
        LD (DW_ENTRIES),BC
        LD HL,ER_DPB
        LD (DT_DPB),HL
        LD A,1
        LD (DW_OK),A
DW_REUSE:
        LD A,(DW_OK)
        OR A
        JP Z,DW_NEXT
        LD HL,DT_BUFFER
        LD (DT_END),HL
        LD HL,0
        LD (DT_FILES),HL
        LD HL,(DW_SNAP)
        LD (DW_CURSOR),HL
        LD HL,(DW_ENTRIES)
        LD (DW_LEFT),HL
DW_SCAN:
        LD HL,(DW_LEFT)
        LD A,H
        OR L
        JP Z,DW_REPORT
        DEC HL
        LD (DW_LEFT),HL
        LD HL,(DW_CURSOR)
        LD (BC_DIREP),HL
        LD DE,32
        ADD HL,DE
        LD (DW_CURSOR),HL
        LD HL,(BC_DIREP)
        LD A,(DW_USER)
        CP (HL)
        JR NZ,DW_SCAN
        INC HL
        LD DE,FS_FCB+1
        LD B,11
DW_NAME:
        LD A,(DE)
        CP '?'
        JR Z,DW_NNEXT
        LD C,A
        LD A,(HL)
        AND 7FH
        CP C
        JR NZ,DW_SCAN
DW_NNEXT:
        INC HL
        INC DE
        DJNZ DW_NAME
        CALL RD_FILTER
        JR NC,DW_SCAN
        CALL DT_STORE
        JR NC,DW_SCAN
        LD DE,DW_CAPMSG
        CALL BC_PRINT
        CALL DW_MARK
DW_REPORT:
        LD HL,DT_BUFFER
        LD (DT_SCAN),HL
        LD HL,(DT_FILES)
        LD (DT_LEFT),HL
DW_ROW:
        LD HL,(DT_LEFT)
        LD A,H
        OR L
        JP Z,DW_NEXT
        DEC HL
        LD (DT_LEFT),HL
        CALL DW_PREFIX
        LD HL,(DT_SCAN)
        LD B,8
        CALL DW_FIELD
        LD HL,(DT_SCAN)
        LD DE,8
        ADD HL,DE
        LD A,(HL)
        CP ' '
        JR Z,DW_EOL
        LD A,'.'
        CALL BC_PCHAR
        LD HL,(DT_SCAN)
        LD DE,8
        ADD HL,DE
        LD B,3
        CALL DW_FIELD
DW_EOL:
        LD DE,BC_NL
        CALL BC_PRINT
        LD HL,(DT_SCAN)
        LD DE,24
        ADD HL,DE
        LD (DT_SCAN),HL
        LD HL,(DW_TOTAL)
        INC HL
        LD (DW_TOTAL),HL
        LD A,H
        OR L
        JR NZ,DW_ROW
        LD HL,(DW_TOTAL+2)
        INC HL
        LD (DW_TOTAL+2),HL
        JR DW_ROW
DW_FIELD:
        LD A,(HL)
        CP ' '
        RET Z
        PUSH BC
        PUSH HL
        CALL BC_PCHAR
        POP HL
        POP BC
        INC HL
        DJNZ DW_FIELD
        RET
DW_PREFIX:
        LD A,(DW_DRIVE)
        ADD A,'A'
        CALL BC_PCHAR
        LD A,(DW_USER)
        LD B,0
DW_TENS:
        CP 10
        JR C,DW_DIGITS
        SUB 10
        INC B
        JR DW_TENS
DW_DIGITS:
        PUSH AF
        LD A,B
        OR A
        JR Z,DW_ONES
        ADD A,'0'
        CALL BC_PCHAR
DW_ONES:
        POP AF
        ADD A,'0'
        CALL BC_PCHAR
        LD A,':'
        JP BC_PCHAR
DW_CONFIG:
        LD A,(DW_QUERY)
        LD (DW_BIND),A
        LD DE,DW_BIND
        LD B,3
        LD C,181
        CALL BDOS
        OR A
        RET Z
        CALL DW_UNAVAIL
        SCF
        RET
DW_UNAVAIL:
        LD DE,DW_UNMSG
        JR DW_DIAG
DW_UFAIL:
        CALL DW_UNAVAIL
        JP DW_NEXT
DW_READERR:
        LD DE,DW_READMSG
        CALL DW_DIAG
        JP DW_NEXT
DW_DIAG:
        PUSH DE
        LD DE,DW_DIRMSG
        CALL BC_PRINT
        LD A,(DW_QUERY)
        ADD A,'A'
        CALL BC_PCHAR
        POP DE
        CALL BC_PRINT
DW_MARK:
        LD A,1
        LD (DW_FAIL),A
        RET
DW_SKIP:
        JP DW_NEXT
DW_CAP:
        LD DE,DW_CAPMSG
        CALL BC_PRINT
        CALL DW_MARK
        JP DW_NEXT
DW_FINISH:
        ; Raw reads do not change BDOS DU. Restore the BIOS selection and DMA.
        LD A,(BC_DSAVE)
        LD C,A
        LD E,1
        LD A,27
        CALL ER_BCALL
        LD BC,0080H
        LD A,36
        CALL ER_BCALL
        LD HL,DW_TOTAL
        LD DE,DTD_NUM
        LD BC,4
        LDIR
        LD HL,(DW_TOTAL)
        LD DE,(DW_TOTAL+2)
        LD A,H
        OR L
        LD B,D
        OR B
        OR E
        JR Z,DW_NO
        CALL DTD_DEC
        LD DE,(DW_TOTAL+2)
        LD HL,(DW_TOTAL)
        DEC HL
        LD A,H
        OR L
        LD B,D
        OR B
        OR E
        LD DE,DW_MANY
        JR NZ,DW_SUM
        LD DE,DW_ONE
        JR DW_SUM
DW_NO:
        LD DE,DW_NOMSG
DW_SUM:
        CALL BC_PRINT
        LD A,(DW_FAIL)
        OR A
        RET Z
        LD DE,DW_INCOMP
        JP BC_PRINT
DW_WORD: DB '/WHEREIS'
DW_DIRMSG: DB 'DIR: $'
DW_UNMSG: DB ': unavailable.',13,10,'$'
DW_READMSG: DB ': directory read error.',13,10,'$'
DW_CAPMSG: DB 'DIR: Directory capacity exceeded.',13,10,'$'
DW_ONE: DB ' MATCH',13,10,'$'
DW_MANY: DB ' MATCHES',13,10,'$'
DW_NOMSG: DB 'DIR: No matches found.',13,10,'$'
DW_INCOMP: DB 'Search incomplete.',13,10,'$'
DW_MODE: DB 0
DW_OTHER: DB 0
DW_OK: DB 0
DW_FAIL: DB 0
DW_QUERY: DB 0
DW_DRIVE: DB 0
DW_USER: DB 0
DW_INDEX: DW 0
DW_TOTAL: DS 4
DW_SNAP: DW 0
DW_ENTRIES: DW 0
DW_CURSOR: DW 0
DW_LEFT: DW 0
DW_BIND: DS 80
