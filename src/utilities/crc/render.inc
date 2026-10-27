; One row builder feeds both output destinations. Console /40 is independent.
PUTNAME:
        LD HL,LASTNAME
        LD B,8
PNBASE:
        LD A,(HL)
        CALL PUT
        INC HL
        DJNZ PNBASE
        LD A,' '
        CALL PUT
        LD B,3
PNEXT:
        LD A,(HL)
        CALL PUT
        INC HL
        DJNZ PNEXT
        RET
HEADERS:
        CALL WSECTION
        CALL NEWLINE
        LD HL,TITLELIN
        CALL PUTS
        CALL HEADEROU
        CALL NEWLINE
        LD HL,NAMEHEAD
        CALL PUTS
        CALL SPACE2
        LD HL,RECSHEAD
        CALL PUTS
        LD A,(RECSWIDT)
        SUB 4
        CALL PAD
        XOR A
        CALL FIELDS
        CALL HEADEROU
        CALL NEWLINE
        LD HL,NAMEDASH
        CALL PUTS
        CALL SPACE2
        LD A,(RECSWIDT)
        LD B,A
        LD A,'-'
        CALL REPEATPU
        LD A,1
        CALL FIELDS
        JP HEADEROU
HEADEROU:
        XOR A
        CALL PUT
        LD A,(NARROW)
        OR A
        JR NZ,HEADERSA
        LD HL,LINE
        CALL TEXT
        CALL NL
HEADERSA:
        LD A,(LEGACY)
        OR A
        RET NZ
        JP WLINE
RESULTRO:
        CALL NEWLINE
        CALL PUTNAME
        CALL SPACE2
        LD A,(RECSWIDT)
        LD HL,RECS
        CALL PUTDEC
        LD A,2
        CALL FIELDS
        XOR A
        CALL PUT
        LD A,(NARROW)
        OR A
        JR NZ,ROWSTACK
        LD HL,LINE
        CALL TEXT
        CALL NL
        JR ROWSAVE
ROWSTACK:
        CALL STACKED
ROWSAVE:
        LD A,(LEGACY)
        OR A
        JP Z,WLINE
        CALL NEWLINE
        LD HL,LEGACYPR
        CALL PUTS
        LD HL,LASTNAME
        LD B,8
LEGNAME:
        LD A,(HL)
        CALL PUT
        INC HL
        DJNZ LEGNAME
        LD A,'.'
        CALL PUT
        LD B,3
LEGEXT:
        LD A,(HL)
        CALL PUT
        INC HL
        DJNZ LEGEXT
        LD HL,LEGACYSU
        CALL PUTS
        LD A,(CVALUES+1)
        CALL HEXBYTE
        LD A,' '
        CALL PUT
        LD A,(CVALUES)
        CALL HEXBYTE
        XOR A
        CALL PUT
        CALL WLINE
        CALL NEWLINE
        XOR A
        CALL PUT
        JP WLINE
; A=0 headings,1 dashes,2 values. Width/labels from the same descriptor.
FIELDS:
        LD (FIELDMOD),A
        LD IX,FIELDTAB
        LD A,1
        LD (FIELDBIT),A
FIELDNEX:
        LD A,(ALGSEL)
        LD B,A
        LD A,(FIELDBIT)
        AND B
        JR Z,FIELDSKI
        CALL SPACE2
        LD A,(FIELDMOD)
        OR A
        JR Z,FIELDLAB
        DEC A
        JR Z,FIELDDAS
        LD A,(IX+2)
        LD B,(IX+4)
        LD C,B
        SLA C
        LD A,(IX+3)
        CP 14
        JR NZ,FIELDDIG
        DEC C
FIELDDIG:
        LD A,(IX+2)
        SUB C
        CALL PAD
        LD HL,CVALUES
        LD E,(IX+3)
        LD D,0
        ADD HL,DE
        LD B,(IX+4)
        CALL FIELDHEX
        JR FIELDSKI
FIELDLAB:
        LD L,(IX+0)
        LD H,(IX+1)
        CALL PUTS
        JR FIELDSKI
FIELDDAS:
        LD B,(IX+2)
        LD A,'-'
        CALL REPEATPU
FIELDSKI:
        LD DE,5
        ADD IX,DE
        LD A,(FIELDBIT)
        ADD A,A
        LD (FIELDBIT),A
        OR A
        JR NZ,FIELDNEX
        RET
PAD:
        OR A
        RET Z
        LD B,A
        LD A,' '
REPEATPU:
        CALL PUT
        DJNZ REPEATPU
        RET
STACKED:
        ; Preserve the native row while rendering narrow console-only lines.
        LD HL,LINE
        LD DE,ROWCOPY
        LD BC,256
        LDIR
        CALL NEWLINE
        CALL PUTNAME
        CALL ENDLINE
        CALL NEWLINE
        LD HL,STACKREC
        CALL PUTS
        LD HL,RECS
        XOR A
        CALL PUTDEC
        CALL ENDLINE
        LD IX,FIELDTAB
        LD A,1
        LD (FIELDBIT),A
STACKNEX:
        LD A,(ALGSEL)
        LD B,A
        LD A,(FIELDBIT)
        AND B
        JR Z,STACKSKI
        CALL NEWLINE
        CALL SPACE2
        LD L,(IX+0)
        LD H,(IX+1)
        CALL PUTS
        LD A,' '
        CALL PUT
        LD HL,CVALUES
        LD E,(IX+3)
        LD D,0
        ADD HL,DE
        LD B,(IX+4)
        CALL FIELDHEX
        CALL ENDLINE
STACKSKI:
        LD DE,5
        ADD IX,DE
        LD A,(FIELDBIT)
        ADD A,A
        LD (FIELDBIT),A
        OR A
        JR NZ,STACKNEX
        LD HL,ROWCOPY
        LD DE,LINE
        LD BC,256
        LDIR
        RET
TITLELIN: DB '; BetterCP/M CRC list',0
NAMEHEAD: DB 'NAME     EXT',0
NAMEDASH: DB '-------- ---',0
RECSHEAD: DB 'RECS',0
STACKREC: DB '  RECS  ',0
LABELCRC: DB 'CRCK',0
LABELC01: DB 'CRCK5',0
LABELCHE: DB 'CHEK',0
LABELC02: DB 'CRC32   ',0
LABELS08: DB 'SUM8',0
LABELS16: DB 'SUM16',0
LABELK06: DB 'KERM6',0
LABELK12: DB 'KERM12',0
FIELDTAB:
        DW LABELCRC
        DB 4,0,2
        DW LABELC01
        DB 5,2,2
        DW LABELCHE
        DB 4,4,2
        DW LABELC02
        DB 8,6,4
        DW LABELS08
        DB 4,10,1
        DW LABELS16
        DB 5,11,2
        DW LABELK06
        DB 5,13,1
        DW LABELK12
        DB 6,14,2
LEGACYPR: DB '--> FILE:  ',0
LEGACYSU: DB 9,9,'CRC = ',0
FIELDMOD: DB 0
FIELDBIT: DB 0
ROWCOPY: DS 256

; IX descriptor, HL little-endian value, B bytes. KERM12 is three hex digits.
FIELDHEX:
        LD A,(IX+3)
        CP 14
        JP NZ,HEXVALUE
        INC HL
        LD A,(HL)
        CALL HEXDIGIT
        DEC HL
        LD A,(HL)
        JP HEXBYTE
