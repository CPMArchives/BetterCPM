; Transient DIR collection. One 24-byte record per selected file on this DU:
; normalized name (11), reserved (1), DM accumulator (12).
; The buffer occupies disposable TPA below the current BDOS/RSX entry minus
; 256 bytes. Never rescan a file while Search Next is active.
RD_SEARCH:
        LD HL,(0006H)
        LD DE,0100H
        OR A
        SBC HL,DE
        LD (DT_LIMIT),HL
        LD HL,DT_BUFFER
        LD (DT_END),HL
        LD HL,0
        LD (DT_FILES),HL
        XOR A
        LD HL,DT_TOTAL
        LD B,12
DT_RESET:
        LD (HL),A
        INC HL
        DJNZ DT_RESET
        LD A,'?'
        LD (BC_FCB+12),A
        LD DE,0080H
        LD C,26
        CALL BDOS
        LD C,17
DT_SEARCH:
        LD DE,BC_FCB
        CALL BDOS
        CP 0FFH
        JP Z,DT_REPORT
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,080H
        LD L,A
        LD H,0
        LD (BC_DIREP),HL
        CALL DT_FILTER
        JR NC,DT_NEXT
        CALL DT_STORE
        JP C,DT_FULL
DT_NEXT:
        LD C,18
        JR DT_SEARCH

; Find an existing name, ignoring attribute high bits. All extents contribute,
; including entries that have no EX=0 entry and entries in native search order.
DT_STORE:
        LD HL,DT_BUFFER
        LD (DT_SCAN),HL
        LD HL,(DT_FILES)
        LD (DT_LEFT),HL
DT_FIND:
        LD HL,(DT_LEFT)
        LD A,H
        OR L
        JR Z,DT_NEW
        LD HL,(DT_SCAN)
        LD DE,(BC_DIREP)
        INC DE
        LD B,11
DT_COMPARE:
        LD A,(DE)
        AND 7FH
        CP (HL)
        JR NZ,DT_ADVANCE
        INC DE
        INC HL
        DJNZ DT_COMPARE
        LD HL,(DT_SCAN)
        JR DT_ACCUM
DT_ADVANCE:
        LD HL,(DT_SCAN)
        LD DE,24
        ADD HL,DE
        LD (DT_SCAN),HL
        LD HL,(DT_LEFT)
        DEC HL
        LD (DT_LEFT),HL
        JR DT_FIND
DT_NEW:
        LD HL,(DT_END)
        LD DE,24
        ADD HL,DE
        JP C,DT_NOSPACE
        LD DE,(DT_LIMIT)
        OR A
        SBC HL,DE
        JP NC,DT_NOSPACE
        LD HL,(DT_END)
        LD (DT_SCAN),HL
        LD DE,(BC_DIREP)
        INC DE
        LD B,11
DT_NAMECOPY:
        LD A,(DE)
        AND 7FH
        LD (HL),A
        INC HL
        INC DE
        DJNZ DT_NAMECOPY
        XOR A
        LD B,13
DT_ZEROREC:
        LD (HL),A
        INC HL
        DJNZ DT_ZEROREC
        LD (DT_END),HL
        LD HL,(DT_FILES)
        INC HL
        LD (DT_FILES),HL
        LD HL,(DT_SCAN)
DT_ACCUM:
        LD DE,12
        ADD HL,DE
        LD B,H
        LD C,L
        LD HL,(BC_DIREP)
        LD DE,(DT_DPB)
        CALL DM_ADD
        OR A
        RET
DT_NOSPACE:
        SCF
        RET
DT_FULL:
        LD DE,DT_FULLMSG
        CALL BC_PRINT
        JP BC_DURST

; Initial one-column formatter; adaptive columns and display switches follow.
DT_REPORT:
        LD DE,BC_NL
        CALL BC_PRINT
        LD C,25
        CALL BDOS
        ADD A,'A'
        CALL BC_PCHAR
        CALL RD_PRINTUSER
        LD DE,DT_HEADING
        CALL BC_PRINT
        LD HL,(DT_FILES)
        LD A,H
        OR L
        JR NZ,DT_ROWS
        LD DE,BC_NOFILE
        CALL BC_PRINT
        JP RD_NEXT
DT_ROWS:
        LD HL,DT_BUFFER
        LD (DT_SCAN),HL
        LD HL,(DT_FILES)
        LD (DT_LEFT),HL
DT_ROW:
        LD HL,(DT_SCAN)
        LD B,8
        CALL BC_FFIX
        LD A,' '
        CALL BC_PCHAR
        LD HL,(DT_SCAN)
        LD DE,8
        ADD HL,DE
        LD B,3
        CALL BC_FFIX
        LD DE,DT_SPACE
        CALL BC_PRINT
        LD HL,(DT_SCAN)
        LD DE,12
        ADD HL,DE
        CALL DT_K
        LD DE,DT_KLINE
        CALL BC_PRINT
        LD HL,(DT_SCAN)
        LD DE,24
        ADD HL,DE
        LD (DT_SCAN),HL
        LD HL,(DT_LEFT)
        DEC HL
        LD (DT_LEFT),HL
        LD A,H
        OR L
        JR NZ,DT_ROW
        LD HL,(DT_FILES)
        LD (DTD_NUM),HL
        LD HL,0
        LD (DTD_NUM+2),HL
        CALL DTD_DEC
        LD DE,DT_FILEMSG
        LD HL,(DT_FILES)
        DEC HL
        LD A,H
        OR L
        JR NZ,DT_SUMMARY
        LD DE,DT_ONEMSG
DT_SUMMARY:
        CALL BC_PRINT
        LD HL,DT_TOTAL
        CALL DT_K
        LD DE,DT_SUMMSG
        CALL BC_PRINT
        JP RD_NEXT
DT_K:
        LD DE,DTD_NUM
        LD BC,4
        LDIR
        ; Allocation records are multiples of eight for supported CP/M DPBs.
        LD B,3
DT_KSHIFT:
        LD HL,DTD_NUM+3
        LD C,4
        OR A
DT_KBYTE:
        RR (HL)
        DEC HL
        DEC C
        JR NZ,DT_KBYTE
        DJNZ DT_KSHIFT
        JP DTD_DEC
DT_LIMIT: DW 0
DT_END: DW 0
DT_FILES: DW 0
DT_SCAN: DW 0
DT_LEFT: DW 0
DT_HEADING: DB ':',13,10,'$'
DT_SPACE: DB '  $'
DT_KLINE: DB 'K',13,10,'$'
DT_FILEMSG: DB ' FILES, $'
DT_ONEMSG: DB ' FILE, $'
DT_SUMMSG: DB 'K TOTAL',13,10,'$'
DT_FULLMSG: DB 13,10,'Directory too large.',13,10,'$'
