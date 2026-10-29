; Shared native/legacy rows feed console and saved lists. /40 wraps console only.
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
        LD A,(LEGACY)
        OR A
        RET NZ
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
        JR NZ,HEADER40
        LD HL,LINE
        CALL TEXT
        CALL NL
        JR HEADERSA
HEADER40:
        CALL TABLE40
HEADERSA:
        LD A,(LEGACY)
        OR A
        RET NZ
        JP WLINE
RESULTRO:
        LD A,(LEGACY)
        OR A
        JP NZ,LEGACYRO
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
        CALL TABLE40
ROWSAVE:
        JP WLINE
LEGACYRO:
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
        LD HL,LINE
        CALL TEXT
        CALL NL
        CALL NL
        CALL WLINE
        CALL NEWLINE
        XOR A
        CALL PUT
        JP WLINE
; A=0 headings,1 dashes,2 values. Width/labels from the same descriptor.
FIELDS:
        LD (FIELDMOD),A
        LD IX,FIELDTAB
FIELDNEX:
        LD A,(IX+0)
        OR (IX+1)
        RET Z
        LD A,(IX+5)
        LD (FIELDBIT),A
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
        LD DE,6
        ADD IX,DE
        JP FIELDNEX
PAD:
        OR A
        RET Z
        LD B,A
        LD A,' '
REPEATPU:
        CALL PUT
        DJNZ REPEATPU
        RET
 ; Render console slices of the native table; LINE remains unchanged for WLINE.
TABLE40:
        LD HL,LINE
        LD A,(HL)
        CP ';'
        JP Z,TABLETEXT
        LD A,(RECSWIDT)
        ADD A,14
        LD (TABLEBASE),A
        LD B,A
        CALL TABLECHARS
        LD A,(TABLEBASE)
        LD (TABLECOL),A
        LD IX,FIELDTAB
TABLENEXT:
        LD A,(IX+0)
        OR (IX+1)
        JP Z,NL
        LD A,(ALGSEL)
        AND (IX+5)
        JR Z,TABLESKIP
        LD A,(IX+2)
        ADD A,2
        LD (TABLEWIDTH),A
        LD B,A
        LD A,(TABLECOL)
        ADD A,B
        CP 41
        JR C,TABLEFIT
        PUSH HL
        CALL NL
        LD A,(TABLEBASE)
        LD B,A
TABLEPAD:
        PUSH BC
        LD A,' '
        CALL CHAR
        POP BC
        DJNZ TABLEPAD
        POP HL
        LD A,(TABLEBASE)
        LD (TABLECOL),A
TABLEFIT:
        LD A,(TABLEWIDTH)
        LD B,A
        CALL TABLECHARS
        LD A,(TABLEWIDTH)
        LD B,A
        LD A,(TABLECOL)
        ADD A,B
        LD (TABLECOL),A
TABLESKIP:
        LD DE,6
        ADD IX,DE
        JR TABLENEXT
TABLECHARS:
        LD A,(HL)
        PUSH HL
        PUSH BC
        CALL CHAR
        POP BC
        POP HL
        INC HL
        DJNZ TABLECHARS
        RET
TABLETEXT:
        CALL TEXT
        JP NL
TABLEBASE: DB 0
TABLECOL: DB 0
TABLEWIDTH: DB 0
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
ALGTEMPL:
        DW LABELCRC
        DB 4,0,2,1
        DW LABELC01
        DB 5,2,2,2
        DW LABELCHE
        DB 4,4,2,4
        DW LABELC02
        DB 8,6,4,8
        DW LABELS08
        DB 4,10,1,16
        DW LABELS16
        DB 5,11,2,32
        DW LABELK06
        DB 5,13,1,64
        DW LABELK12
        DB 6,14,2,128
        DB 0,0
; Ordered descriptors followed by a zero pointer; at most eight selections.
FIELDTAB: DS 50
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
