; Internal operand qualifier splitter. Caller has already removed location/DU.
; Input HL/B: remaining filespec, possibly followed by one [qualifier] block.
; Output CF clear, HL unchanged, B filespec length; OQ_PTR/OQ_LEN locate content.
; No block: pointer/length zero. Empty filespec is legal for destination DU-only.
; CF set rejects empty/unclosed/nested blocks, stray ] or suffix after ].
; No whitespace is admitted within brackets. Semantic expression parsing follows.
OQ_SPLIT:
        XOR A
        LD (OQ_LEN),A
        LD (OQ_PTR),A
        LD (OQ_PTR+1),A
        PUSH HL
        LD C,0
OQ_SCAN:
        LD A,B
        OR A
        JR Z,OQ_DONE
        LD A,(HL)
        CP ']'
        JR Z,OQ_BAD
        CP '['
        JR Z,OQ_OPEN
        INC HL
        INC C
        DEC B
        JR OQ_SCAN
OQ_OPEN:
        LD A,C
        LD (OQ_BASE),A
        INC HL
        DEC B
        LD (OQ_PTR),HL
        LD C,0
OQ_INNER:
        LD A,B
        OR A
        JR Z,OQ_BAD
        LD A,(HL)
        CP ']'
        JR Z,OQ_CLOSE
        CP '['
        JR Z,OQ_BAD
        CP 21H
        JR C,OQ_BAD
        CP 7FH
        JR NC,OQ_BAD
        INC HL
        INC C
        DEC B
        JR OQ_INNER
OQ_CLOSE:
        LD A,C
        OR A
        JR Z,OQ_BAD
        LD (OQ_LEN),A
        DEC B
        JR NZ,OQ_BAD
        LD A,(OQ_BASE)
        LD B,A
        POP HL
        OR A
        RET
OQ_DONE:
        LD B,C
        POP HL
        OR A
        RET
OQ_BAD:
        XOR A
        LD (OQ_LEN),A
        LD (OQ_PTR),A
        LD (OQ_PTR+1),A
        POP HL
        SCF
        RET
OQ_PTR: DW 0
OQ_LEN: DB 0
OQ_BASE: DB 0
