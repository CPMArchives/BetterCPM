; Transient DIR collection. One 24-byte record per selected file on this DU:
; normalized name (11), RO/SYS/ARC mask (1), DM accumulator (12).
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
        LD DE,11
        ADD HL,DE
        PUSH HL
        LD HL,(BC_DIREP)
        LD DE,9
        ADD HL,DE
        LD C,0
        LD A,(HL)
        AND 80H
        JR Z,DT_ASYS
        INC C
DT_ASYS:
        INC HL
        LD A,(HL)
        AND 80H
        JR Z,DT_AARC
        LD A,C
        OR 2
        LD C,A
DT_AARC:
        INC HL
        LD A,(HL)
        AND 80H
        JR Z,DT_AMERGE
        LD A,C
        OR 4
        LD C,A
DT_AMERGE:
        LD A,C
        POP HL
        OR (HL)
        LD (HL),A
        INC HL
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

; Column width is measured over selected records before headings are printed.
DT_REPORT:
        CALL DC_LAYOUT
        JP C,DC_REJECT
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
        CALL DN_SORT
        LD HL,DT_BUFFER
        LD (DT_SCAN),HL
        LD HL,(DT_FILES)
        LD (DT_LEFT),HL
DT_ROW:
        XOR A
        LD (DG_CHARS),A
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
        CALL DT_SIZE
        CALL DT_SUFFIX
        CALL DT_ATTRIBUTES
        LD HL,(DT_SCAN)
        LD DE,24
        ADD HL,DE
        LD (DT_SCAN),HL
        LD HL,(DT_LEFT)
        DEC HL
        LD (DT_LEFT),HL
        LD A,H
        OR L
        JR Z,DT_ROWEND
        CALL DC_SEPARATOR
        JP DT_ROW
DT_ROWEND:
        LD DE,BC_NL
        CALL BC_PRINT
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
        CALL DT_SIZE
        CALL DT_SUFFIX
        LD DE,DT_SUMMSG
        CALL BC_PRINT
        JP RD_NEXT
; Display selection does not change the allocated-record sort key.
DT_SIZE:
        LD A,(DT_UNIT)
        CP 'K'
        JP Z,DT_K
        LD DE,DTD_NUM
        LD BC,4
        LDIR
        JP DTD_DEC
DT_SUFFIX:
        LD A,(DT_UNIT)
        JP BC_PCHAR
DT_UNIT: DB 'K'
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
; /A is reporting only. Accumulated attributes stay with the sorted record.
DT_ATTRIBUTES:
        LD A,(DT_SHOWATTR)
        OR A
        RET Z
        LD DE,DT_SPACE
        CALL BC_PRINT
        LD HL,(DT_SCAN)
        LD DE,11
        ADD HL,DE
        LD A,(HL)
        LD (DT_ATTRBITS),A
        LD HL,DT_ATTRTABLE
        LD B,3
DT_APOS:
        LD A,(DT_ATTRBITS)
        AND (HL)
        INC HL
        LD A,'-'
        JR Z,DT_APRINT
        LD A,(HL)
DT_APRINT:
        INC HL
        PUSH HL
        PUSH BC
        CALL BC_PCHAR
        POP BC
        POP HL
        DJNZ DT_APOS
        RET
DT_SHOWATTR: DB 0
DT_ATTRBITS: DB 0
DT_ATTRTABLE: DB 2,'S',1,'R',4,'A'
DT_LIMIT: DW 0
DT_END: DW 0
DT_FILES: DW 0
DT_SCAN: DW 0
DT_LEFT: DW 0
DT_HEADING: DB ':',13,10,'$'
DT_SPACE: DB '  $'
DT_FILEMSG: DB ' FILES, $'
DT_ONEMSG: DB ' FILE, $'
DT_SUMMSG: DB ' TOTAL',13,10,'$'
DT_FULLMSG: DB 13,10,'Directory too large.',13,10,'$'

; Stable comparison of the selected key, with name/extension tie-breaks. Move whole
; records so allocation, logical-record and physical-entry totals stay attached.
; Shrink the sorted tail after each pass; an already-sorted pass returns early.
DN_SORT:
        LD A,(DN_MODE)
        CP 'U'
        RET Z
        LD HL,(DT_FILES)
        DEC HL
        LD A,H
        OR L
        RET Z
        INC HL
        LD A,H
        OR L
        RET Z
        LD HL,(DT_END)
        LD DE,24
        OR A
        SBC HL,DE
        LD (DN_LAST),HL
DN_PASS:
        XOR A
        LD (DN_SWAP),A
        LD HL,DT_BUFFER
        LD (DN_PTR),HL
DN_PAIR:
        LD HL,(DN_PTR)
        LD DE,24
        ADD HL,DE
        EX DE,HL
        LD HL,(DN_PTR)
        CALL DN_ORDER
        JR C,DN_EXCH
        JR DN_NEXT
DN_EXCH:
        LD A,1
        LD (DN_SWAP),A
        LD HL,(DN_PTR)
        LD DE,24
        ADD HL,DE
        EX DE,HL
        LD HL,(DN_PTR)
        LD B,24
DN_BYTES:
        LD C,(HL)
        LD A,(DE)
        LD (HL),A
        LD A,C
        LD (DE),A
        INC HL
        INC DE
        DJNZ DN_BYTES
DN_NEXT:
        LD HL,(DN_PTR)
        LD DE,24
        ADD HL,DE
        LD (DN_PTR),HL
        LD DE,(DN_LAST)
        OR A
        SBC HL,DE
        JR NZ,DN_PAIR
        LD A,(DN_SWAP)
        OR A
        RET Z
        LD HL,(DN_LAST)
        LD DE,24
        OR A
        SBC HL,DE
        LD (DN_LAST),HL
        LD DE,DT_BUFFER
        OR A
        SBC HL,DE
        JR NZ,DN_PASS
        RET
DN_PTR: DW 0
DN_LAST: DW 0
DN_SWAP: DB 0
DN_MODE: DB 'N'
DN_REV: DB 0

; Carry means the right record should precede the left. Reverse applies to
; the primary key; type/size ties use ascending name+extension in either mode.
DN_ORDER:
        LD A,(DN_MODE)
        CP 'T'
        JR Z,DN_TYPE
        CP 'Z'
        JR Z,DN_SIZE
        CALL DN_NAME
        JR DN_DIR
DN_TYPE:
        LD BC,8
        ADD HL,BC
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD B,3
        CALL DN_LEX
        JR NZ,DN_DIR
        JP DN_NAME
DN_SIZE:
        LD BC,15                ; allocated record DWORD, most significant byte
        ADD HL,BC
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD B,4
DN_NUM:
        LD C,(HL)
        LD A,(DE)
        CP C
        JR NZ,DN_DIR
        DEC HL
        DEC DE
        DJNZ DN_NUM
        JP DN_NAME
DN_NAME:
        LD HL,(DN_PTR)
        LD DE,24
        ADD HL,DE
        EX DE,HL
        LD HL,(DN_PTR)
        LD B,11
DN_LEX:
        LD C,(HL)
        LD A,(DE)
        CP C
        RET NZ
        INC HL
        INC DE
        DJNZ DN_LEX
        RET
DN_DIR:
        RET Z
        PUSH AF
        LD A,(DN_REV)
        OR A
        JR Z,DN_NORMAL
        POP AF
        CCF
        RET
DN_NORMAL:
        POP AF
        RET
