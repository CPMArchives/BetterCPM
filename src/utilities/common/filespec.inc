; Shared bounded 8.3 validator. HL/B=filespec, A=0 exact / 1 wildcards.
; Success CF clear, A=1 if wildcard present else 0; HL=end, B=0.
; Failure CF set, A=0, HL=detected position. BC/DE scratch.
; No input/global writes, BDOS calls, or command-policy dependencies.
FP_VALIDATE:
        LD      D,A
        LD      C,8
        LD      E,0
FP_NEXT:
        LD      A,B
        OR      A
        JR      Z,FP_END
        LD      A,(HL)
        CP      '.'
        JR      Z,FP_DOT
        CP      ' '+1
        JR      C,FP_BAD
        CP      07FH
        JR      NC,FP_BAD
        CP      '*'
        JR      Z,FP_STAR
        CP      '?'
        JR      NZ,FP_CHAR
        CALL    FP_WILD
        RET     C
FP_CHAR:
        CP      ':'
        JR      Z,FP_BAD
        CP      '='
        JR      Z,FP_BAD
        LD      A,C
        OR      A
        JR      Z,FP_BAD
        DEC     C
        INC     HL
        DEC     B
        JR      FP_NEXT
FP_STAR:
        LD      A,C
        OR      A
        JR      Z,FP_BAD
        CALL    FP_WILD
        RET     C
        LD      C,0
FP_SR:
        INC     HL
        DEC     B
        JR      Z,FP_END
        LD      A,(HL)
        CP      '*'
        JR      Z,FP_SR
        CP      '.'
        JR      Z,FP_DOT
        JR      FP_BAD
FP_WILD:
        LD      A,D
        AND     1
        JR      Z,FP_BAD
        LD      A,D
        OR      2
        LD      D,A
        OR      A
        RET
FP_DOT:
        LD      A,E
        OR      A
        JR      NZ,FP_BAD
        LD      A,C
        CP      8
        JR      Z,FP_BAD
        INC     E
        LD      C,3
        INC     HL
        DEC     B
        JR      FP_NEXT
FP_END:
        LD      A,E
        OR      A
        JR      NZ,FP_OK
        LD      A,C
        CP      8
        JR      Z,FP_BAD
FP_OK:
        LD      A,D
        AND     2
        RRCA
        OR      A
        RET
FP_BAD:
        XOR     A
        SCF
        RET

