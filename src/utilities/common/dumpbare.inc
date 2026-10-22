; Sealed DRI display/interruption path; caller constructs DFCB first.
DBARE:
        XOR     A
        LD      (DFCB+32),A
        LD      DE,DFCB
        LD      C,15
        CALL    BDOS
        CP      0FFH
        JR      NZ,OPENED
        LD      DE,BAREMISS
        LD      C,9
        CALL    BDOS
        JR      FINISH
OPENED:
        LD      A,128
        LD      (INDEX),A
        LD      HL,0
LOOP:
        PUSH    HL
        CALL    NEXTBYTE
        POP     HL
        JR      C,FINISH
        LD      B,A
        LD      A,L
        AND     15
        JR      NZ,VALUE
        CALL    NEWLINE
        LD      C,11
        CALL    SERVICE
        RRCA
        JR      C,FINISH
        LD      A,H
        CALL    HEXBYTE
        LD      A,L
        CALL    HEXBYTE
VALUE:
        INC     HL
        LD      A,' '
        CALL    CHARACTER
        LD      A,B
        CALL    HEXBYTE
        JR      LOOP
FINISH:
        CALL NEWLINE
        JP DEXIT
