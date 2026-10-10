; Internal RCP operand transaction. HL/B=input, D/E=caller DU.
; Success CF clear: DU_MAP, FS_FCB (36 bytes), FS_MASK (truth mask).
; Empty filespec means *.*. Failure CF set: map/FCB/mask cleared,
; HL=detected error position, FS_ERROR=1 location/2 qualifier/3 predicate/4 file.
; No BDOS calls, input unchanged. Registers and parser scratch are disposable.
FS_PARSE:
        LD (FS_INPUT),HL
        LD A,B
        LD (FS_LENGTH),A
        CALL FS_CLEAR
        ; For unqualified operands, hide the attribute suffix from DU_SCAN.
        ; Qualified operands contain a colon and use the full DU grammar.
        PUSH HL
        PUSH BC
FS_COLON:
        LD A,B
        OR A
        JR Z,FS_NOQUAL
        LD A,(HL)
        CP ':'
        JR Z,FS_LOCATION
        INC HL
        DJNZ FS_COLON
FS_NOQUAL:
        POP BC
        POP HL
        PUSH HL
        LD C,0
FS_BRACKET:
        LD A,B
        OR A
        JR Z,FS_PREFIX
        LD A,(HL)
        CP '['
        JR Z,FS_PREFIX
        INC HL
        INC C
        DJNZ FS_BRACKET
FS_PREFIX:
        POP HL
        LD B,C
        CALL DU_PARSE
        JP C,FS_DUBAD
        LD HL,(FS_INPUT)
        LD A,(FS_LENGTH)
        LD B,A
        JR FS_QUALIFIER
FS_LOCATION:
        POP BC
        POP HL
        CALL DU_PARSE
        JP C,FS_DUBAD
FS_QUALIFIER:
        CALL OQ_SPLIT
        JR C,FS_OQBAD
        LD (FS_FILE),HL
        LD A,B
        LD (FS_FLEN),A
        LD A,(OQ_LEN)
        OR A
        LD A,0FFH
        JR Z,FS_PREDOK
        LD HL,(OQ_PTR)
        LD A,(OQ_LEN)
        LD B,A
        CALL AT_PARSE
        JR C,FS_ATBAD
FS_PREDOK:
        LD (FS_MASK),A
        LD HL,(FS_FILE)
        LD A,(FS_FLEN)
        LD B,A
        OR A
        JR NZ,FS_VALIDATE
        LD HL,BC_ALL
        LD B,3
FS_VALIDATE:
        ; Shared lexical policy is explicit, independent of COPY state.
        PUSH HL
        PUSH BC
        LD A,1
        CALL FP_VALIDATE
        JR C,FS_LEXBAD
        POP BC
        POP HL
        LD DE,FS_FCB
        CALL BC_PFCB
        OR A
        RET
FS_LEXBAD:
        LD (FS_FILE),HL
        POP BC
        POP HL
        LD HL,(FS_FILE)
        LD A,4
        JR FS_BAD
FS_DUBAD:
        LD A,1
        JR FS_BAD
FS_OQBAD:
        LD HL,(OQ_ERRPTR)
        LD A,2
        JR FS_BAD
FS_ATBAD:
        LD A,3
FS_BAD:
        PUSH AF
        CALL FS_CLEAR
        POP AF
        LD (FS_ERROR),A
        SCF
        RET
FS_CLEAR:
        CALL DU_CLEAR
        PUSH HL
        PUSH BC
        XOR A
        LD HL,FS_FCB
        LD B,38
FS_ZERO:
        LD (HL),A
        INC HL
        DJNZ FS_ZERO
        POP BC
        POP HL
        RET
FS_FCB: DS 36
FS_MASK: DB 0
FS_ERROR: DB 0
FS_INPUT: DW 0
FS_LENGTH: DB 0
FS_FILE: DW 0
FS_FLEN: DB 0
