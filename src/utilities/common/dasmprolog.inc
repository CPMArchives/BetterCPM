; Validate both bounds before emitting source. All supported names receive EQU
; definitions, including aliases and symbols inside instruction operands.
; Same-value labels remain readable and are accepted by pinned ZSM4 and Munk.
D_PROLOG:
 LD HL,INBUF+3
 LD A,(HL)
 CP 13
 JP Z,WHAT
 CALL CNVRT
 CP ','
 JR Z,D_P_SECOND
 CP ' '
 JP NZ,WHAT
D_P_SECOND:
 LD (D_P_START),DE
 INC HL
D_P_SKIP:
 LD A,(HL)
 CP ' '
 JR Z,D_P_NEXT
 CP 9
 JR NZ,D_P_PARSE_END
D_P_NEXT:
 INC HL
 JR D_P_SKIP
D_P_PARSE_END:
 LD A,(HL)
 CP 13
 JP Z,WHAT
 CALL D_PARSE_END
 LD (D_P_END),DE
 CALL D_TRAILING_SPACE
 CALL D_CHECK_INTERVAL
 LD A,1
 LD (WRTENAB),A
 CALL PSTG
 DB 9,'.Z80',13,10,9,'ASEG',13,10,9,'ORG',9,0
 LD DE,(D_P_START)
 CALL D_P_HEX
 CALL CRLF
 LD HL,SYMTAB
D_P_SYMBOL:
 LD (D_P_REC),HL
 LD E,(HL)
 INC HL
 LD D,(HL)
 INC HL
 LD A,(HL)
 OR A
 JP Z,GETCMD
 LD B,A
 INC HL
D_P_NAME:
 LD A,(HL)
 CALL COUT
 INC HL
 DJNZ D_P_NAME
 CALL PSTG
 DB 9,'EQU',9,0
 CALL D_P_HEX
 CALL CRLF
 CALL BRKCHK
 LD HL,(D_P_REC)
 CALL D_SNEXT_TEXT
 JR D_P_SYMBOL
D_P_HEX:
 LD A,D
 CALL PASHEX
 LD A,E
 CALL PHEX
 LD A,'H'
 JP COUT
D_P_START: DW 0
D_P_END: DW 0
D_P_PHYS: DW 0
D_P_REC: DW 0
