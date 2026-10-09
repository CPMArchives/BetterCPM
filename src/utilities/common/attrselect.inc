; Shared internal attribute predicate compiler. Input HL/B is bracket content.
; Output CF clear, A=truth mask for RO(bit0), SYS(bit1), ARC(bit2) combinations.
; Operators ! > + > comma; no parentheses, whitespace or nonattribute terms.
; On failure CF set and A/AT_RESULT zero; HL identifies the detected position.
AT_PARSE:
        XOR A
        LD (AT_RESULT),A
        LD (AT_SUM),A
AT_OR:
        CALL AT_ATOM
        JR C,AT_BAD
        LD (AT_TERM),A
AT_AND:
        LD A,B
        OR A
        JR Z,AT_MERGE
        LD A,(HL)
        CP '+'
        JR NZ,AT_MERGE
        INC HL
        DEC B
        CALL AT_ATOM
        JR C,AT_BAD
        LD C,A
        LD A,(AT_TERM)
        AND C
        LD (AT_TERM),A
        JR AT_AND
AT_MERGE:
        LD A,(AT_SUM)
        LD C,A
        LD A,(AT_TERM)
        OR C
        LD (AT_SUM),A
        LD A,B
        OR A
        JR Z,AT_OK
        LD A,(HL)
        CP ','
        JR NZ,AT_BAD
        INC HL
        DEC B
        JR AT_OR
AT_OK:
        LD A,(AT_SUM)
        LD (AT_RESULT),A
        OR A
        RET
AT_BAD:
        XOR A
        LD (AT_RESULT),A
        SCF
        RET
AT_ATOM:
        XOR A
        LD (AT_NOT),A
AT_NEG:
        LD A,B
        OR A
        JR Z,AT_BAD
        LD A,(HL)
        CP '!'
        JR NZ,AT_DOLL
        LD A,(AT_NOT)
        CPL
        LD (AT_NOT),A
        INC HL
        DEC B
        JR AT_NEG
AT_DOLL:
        CP '$'
        JR NZ,AT_BAD
        INC HL
        DEC B
        LD DE,AT_NAME
        LD C,0
AT_LETTER:
        LD A,B
        OR A
        JR Z,AT_LOOK
        LD A,(HL)
        CP '+'
        JR Z,AT_LOOK
        CP ','
        JR Z,AT_LOOK
        PUSH AF
        LD A,C
        CP 3
        JR NC,AT_LONG
        POP AF
        CP 'a'
        JR C,AT_STORE
        CP 'z'+1
        JR NC,AT_STORE
        SUB 32
AT_STORE:
        LD (DE),A
        INC DE
        INC C
        INC HL
        DEC B
        JR AT_LETTER
AT_LONG:
        POP AF
        JR AT_BAD
AT_LOOK:
        LD A,C
        OR A
        JR Z,AT_BAD
        LD (AT_LEN),A
        PUSH HL
        PUSH BC
        LD HL,AT_TABLE
AT_ROW:
        LD A,(HL)
        OR A
        JR Z,AT_MISS
        LD B,A
        INC HL
        LD A,(AT_LEN)
        CP B
        JR NZ,AT_SKIP
        LD DE,AT_NAME
AT_MATCH:
        LD A,(DE)
        CP (HL)
        JR NZ,AT_SKIP
        INC DE
        INC HL
        DJNZ AT_MATCH
        LD A,(HL)
        LD C,A
        LD A,(AT_NOT)
        XOR C
        POP BC
        POP HL
        OR A
        RET
AT_SKIP:
        INC HL
        DJNZ AT_SKIP
        INC HL
        JR AT_ROW
AT_MISS:
        POP BC
        POP HL
        JP AT_BAD
AT_TABLE:
        DB 2,'RO',0AAH,2,'RW',055H,3,'SYS',0CCH,3,'DIR',033H
        DB 3,'ARC',0F0H,3,'R/O',0AAH,3,'R/W',055H,0
AT_NAME: DS 3
AT_LEN: DB 0
AT_NOT: DB 0
AT_SUM: DB 0
AT_TERM: DB 0
AT_RESULT: DB 0

; Destination modification list: comma-separated attribute literals only.
; AT_SET/AT_CLEAR use RO=1 SYS=2 ARC=4. Contradictions clear both and fail.
AT_STATE:
        XOR A
        LD (AT_SET),A
        LD (AT_CLEAR),A
AS_NEXT:
        CALL AT_ATOM
        JP C,AS_BAD
        LD (AS_MASK),A
        PUSH HL
        PUSH BC
        LD HL,AS_TABLE
        LD B,6
AS_FIND:
        LD A,(AS_MASK)
        CP (HL)
        JR Z,AS_FOUND
        INC HL
        INC HL
        INC HL
        DJNZ AS_FIND
        POP BC
        POP HL
        JR AS_BAD
AS_FOUND:
        INC HL
        LD C,(HL)
        INC HL
        LD A,(HL)
        OR A
        JR Z,AS_CLR
        LD A,(AT_CLEAR)
        AND C
        JR NZ,AS_CONFL
        LD A,(AT_SET)
        OR C
        LD (AT_SET),A
        JR AS_MORE
AS_CLR:
        LD A,(AT_SET)
        AND C
        JR NZ,AS_CONFL
        LD A,(AT_CLEAR)
        OR C
        LD (AT_CLEAR),A
AS_MORE:
        POP BC
        POP HL
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        CP ','
        JR NZ,AS_BAD
        INC HL
        DEC B
        JR AS_NEXT
AS_CONFL:
        POP BC
        POP HL
AS_BAD:
        XOR A
        LD (AT_SET),A
        LD (AT_CLEAR),A
        SCF
        RET
AS_TABLE:
        DB 0AAH,1,1,055H,1,0,0CCH,2,1,033H,2,0,0F0H,4,1,00FH,4,0
AS_MASK: DB 0
AT_SET: DB 0
AT_CLEAR: DB 0
