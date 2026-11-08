; Private XTAB 0.1 feasibility library. Original BetterCP/M code, not VLIB.
; OPEN copies the selected personality's bounded description without output.
; CRT only in this experiment. Callers must reopen after layout/routing changes.
; EMIT A=slot 0..6, B/C=zero-based row/column. All output uses BDOS 2.
; A=0 success (including plain fallback), 1 unavailable, 2 malformed, 3 bad args.
; IX/IY preserved; AF/BC/DE/HL scratch; ordinary transient calls only.
TC_OPEN:
        XOR A
        LD (TC_TABLE+6),A              ; failed discovery cannot reuse old facts
        LD (TC_TABLE+3),A
        CALL TC_ROUTE
        RET NZ
        LD DE,TC_MLOOK
        LD C,182
        CALL 5
        OR A
        JR NZ,TC_NONE
        LD DE,TC_LOOK
        LD C,182
        CALL 5
        OR A
        JR NZ,TC_NONE
        LD A,(TC_MLOOK+18)
        LD DE,TC_LOOK+18
        LD B,A
        LD A,(DE)
        CP B
        JR NZ,TC_NONE                 ; facts must belong to selected MCON
        LD DE,TC_GOT
        PUSH DE
        XOR A
        JP (HL)
TC_GOT:
        OR A
        JR NZ,TC_NONE
        LD A,(HL)
        CP 'T'
        JR NZ,TC_BAD
        INC HL
        LD A,(HL)
        CP 'C'
        JR NZ,TC_BAD
        INC HL
        LD A,(HL)
        OR A                          ; exact experimental table version zero
        JR NZ,TC_BAD
        INC HL
        LD A,(HL)
        CP 16
        JR C,TC_BAD
        CP 129
        JR NC,TC_BAD
        LD C,A
        LD B,0
        DEC HL
        DEC HL
        DEC HL
        PUSH HL
        ADD HL,BC
        POP HL
        JR C,TC_BAD
        LD DE,TC_TABLE
        LDIR
        LD HL,TC_TABLE+8
        LD B,8
TC_SLOT:
        LD A,(HL)
        OR A
        JR Z,TC_NEXT
        CP 16
        JR C,TC_BAD
        LD C,A
        LD A,(TC_TABLE+3)
        CP C
        JR Z,TC_BAD
        JR C,TC_BAD
        SUB C
        PUSH HL
        PUSH BC
        LD B,A                        ; remaining bytes bound every scan
        LD E,C
        LD D,0
        LD HL,TC_TABLE
        ADD HL,DE
TC_SCAN:
        LD A,(HL)
        INC HL
        OR A
        JR Z,TC_SCANNED
        DJNZ TC_SCAN
        POP BC
        POP HL
        JR TC_BAD
TC_SCANNED:
        POP BC
        POP HL
TC_NEXT:
        INC HL
        DJNZ TC_SLOT
        XOR A
        RET
TC_BAD:
        LD A,2
        JR TC_ERROR
TC_NONE:
        LD A,1
TC_ERROR:
        PUSH AF
        XOR A
        LD (TC_TABLE+6),A
        LD (TC_TABLE+3),A
        POP AF
        RET
TC_ROUTE:
        LD A,(3)
        AND 3
        CP 1
        LD A,1
        RET NZ
        XOR A
        RET
TC_EMIT:
        PUSH AF
        CALL TC_ROUTE
        JR NZ,TC_EROUTE
        LD A,(TC_TABLE+3)
        OR A
        JR Z,TC_EROUTE
        POP AF
        CP 7
        JR NC,TC_ARG
        LD (TC_RC),BC
        CP 1
        JR NZ,TC_FIND
        LD A,B
        CP 255
        JR Z,TC_ARG
        LD A,(TC_TABLE+4)
        OR A
        JR Z,TC_COL
        CP B
        JR Z,TC_ARG
        JR C,TC_ARG
TC_COL:
        LD A,C
        CP 255
        JR Z,TC_ARG
        LD A,(TC_TABLE+5)
        OR A
        JR Z,TC_MOVE
        CP C
        JR Z,TC_ARG
        JR C,TC_ARG
TC_MOVE:
        LD A,1
TC_FIND:
        ADD A,8
        LD E,A
        LD D,0
        LD HL,TC_TABLE
        ADD HL,DE
        LD E,(HL)
        LD A,E
        OR A
        RET Z                         ; absent optional sequence = plain output
        LD HL,TC_TABLE
        ADD HL,DE
TC_BYTES:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        CP 5
        JR NC,TC_LITERAL
        LD D,A
        LD A,(TC_RC+1)
        BIT 0,D
        JR NZ,TC_COORD
        LD A,(TC_RC)
TC_COORD:
        LD E,A
        LD A,D
        CP 3
        LD A,E
        JR NC,TC_NUMBER
        ADD A,32
        JR TC_LITERAL
TC_NUMBER:
        INC A
        CALL TC_DECIMAL
        JR TC_BYTES
TC_LITERAL:
        CALL TC_PUT
        JR TC_BYTES
TC_EROUTE:
        POP AF
        LD A,1
        RET
TC_ARG:
        LD A,3
        RET
TC_DECIMAL:
        LD B,'0'-1
        LD C,0
TC_HUND:
        INC B
        SUB 100
        JR NC,TC_HUND
        ADD A,100
        PUSH AF
        LD A,B
        CP '0'
        JR Z,TC_NOH
        CALL TC_PUT
        INC C
TC_NOH:
        POP AF
        LD B,'0'-1
TC_TENS:
        INC B
        SUB 10
        JR NC,TC_TENS
        ADD A,10
        PUSH AF
        LD A,B
        CP '0'
        JR NZ,TC_TOUT
        LD A,C
        OR A
        JR Z,TC_NOT
        LD A,B
TC_TOUT:
        CALL TC_PUT
TC_NOT:
        POP AF
        ADD A,'0'
TC_PUT:
        PUSH HL
        PUSH BC
        PUSH DE
        LD E,A
        LD C,2
        CALL 5
        POP DE
        POP BC
        POP HL
        RET
TC_CODE_END:
TC_MLOOK: DB 1,20,0,0,'MCON',1,1,4,0
        DS 8,0
TC_LOOK: DB 1,20,0,0,'XTAB',0,1,0,0
        DS 8,0
TC_RC: DW 0
TC_TABLE: DS 128,0
TC_LIBRARY_END:
