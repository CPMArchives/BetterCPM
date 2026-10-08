; Transient-only trailing /O and /S options. Repetition is idempotent, but
; overwrite and skip are mutually exclusive. Strip options before preflight.
BC_COPT:
        XOR     A
        LD      (CT_SKIP),A
        LD      (CT_SKIPS),A
        LD      (CT_FAILS),A
        PUSH    HL
        LD      E,B
        LD      D,0
        ADD     HL,DE
CTOTRIM:
        DEC     HL
        LD      A,(HL)
        CP      ' '
        JR      NZ,CTOTEST
        DJNZ    CTOTRIM
        JP      CT_OBAD
CTOTEST:
        LD      A,B
        CP      4
        JR      C,CT_OEND
        LD      A,(HL)
        LD      C,A
        CP      'O'
        JR      Z,CTOSLASH
        CP      'S'
        JR      NZ,CT_OEND
CTOSLASH:
        DEC     HL
        LD      A,(HL)
        CP      '/'
        JR      NZ,CT_OEND
        DEC     HL
        LD      A,(HL)
        CP      ' '
        JR      NZ,CT_OEND
        LD      A,(BC_MVFLAG)
        OR      A
        JR      NZ,CT_OBAD
        LD      A,C
        CP      'S'
        JR      Z,CTSETS
        LD      A,(CT_SKIP)
        OR      A
        JR      NZ,CT_OBAD
        INC     A
        LD      (BC_OVER),A
        JR      CTOTAIL
CTSETS:
        LD      A,(BC_OVER)
        OR      A
        JR      NZ,CT_OBAD
        INC     A
        LD      (CT_SKIP),A
CTOTAIL:
        DEC     B
        DEC     B
        DEC     B
        JR      CTOTRIM
CT_OEND:
        POP     HL
        OR      A
        RET
CT_OBAD:
        POP     HL
        SCF
        RET

; Existing read-only destinations fail this file even under /O or /S. A
; writable /S collision returns without delete/make/write and advances batch.
CTEXIST:
        LD      A,(BC_NEWFCB+9)
        AND     80H
        JR      NZ,CTROFAIL
        LD      A,(CT_SKIP)
        OR      A
        JP      Z,CTALLOW
        LD      HL,CT_SKIPS
        INC     (HL)
        LD      DE,CT_SKIPM
        CALL    BC_PRINT
        RET
CTROFAIL:
        LD      HL,CT_FAILS
        INC     (HL)
        LD      DE,BC_ROMESS
        CALL    BC_PRINT
        RET
