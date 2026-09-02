; Shared TRS-80 Model 4 physical console implementation.

M4_INIT:
        LD      A,08EH
        OUT     (OPTREG),A
        LD      HL,VIDEOBASE
        LD      (M4CURSOR),HL
        XOR     A
        LD      (M4COLUMN),A
        LD      DE,VIDEOBASE+1
        LD      BC,VIDEOSIZE-1
        LD      (HL),020H
        LDIR
        RET

M4_OUT:
        LD      A,C
        CP      13
        JR      Z,M4_CR
        CP      10
        JR      Z,M4_LF
        LD      HL,(M4CURSOR)
        LD      (HL),A
        INC     HL
        LD      (M4CURSOR),HL
        LD      A,(M4COLUMN)
        INC     A
        CP      VIDEOCOLS
        JR      C,M4_STCOL
        XOR     A
M4_STCOL:
        LD      (M4COLUMN),A
        RET
M4_CR:
        LD      A,(M4COLUMN)
        LD      E,A
        LD      D,0
        LD      HL,(M4CURSOR)
        OR      A
        SBC     HL,DE
        LD      (M4CURSOR),HL
        XOR     A
        LD      (M4COLUMN),A
        RET
M4_LF:
        LD      HL,(M4CURSOR)
        LD      DE,VIDEOCOLS
        ADD     HL,DE
        LD      (M4CURSOR),HL
        RET

M4_STAT:
        CALL    M4_SCAN
        OR      A
        RET
M4_IN:
        LD      A,(M4_PENDING)
        OR      A
        JR      NZ,M4_KEYCHANGE
M4_INWAIT:
        CALL    M4_SCAN
        OR      A
        JR      Z,M4_INWAIT
        LD      (M4_PENDING),A
; Patch 2026-09-02: the original whole-matrix release wait could discard a
; second key pressed before the first was released.  Retain that debounce for
; reliable repeated letters, but queue one different overlapping key.
M4_KEYCHANGE:
        CALL    M4_SCAN
        OR      A
        JR      Z,M4_KEYDONE
        LD      C,A
        LD      A,(M4_PENDING)
        CP      C
        JR      Z,M4_KEYCHANGE
        PUSH    AF
        LD      A,C
        LD      (M4_PENDING),A
        POP     AF
        RET
M4_KEYDONE:
        LD      A,(M4_PENDING)
        LD      C,A
        XOR     A
        LD      (M4_PENDING),A
        LD      A,C
        RET

; Patch 2026-09-01: rows are selected by successive address bits at
; F401h..F440h.  Modifier/configuration policy remains above this scanner.
M4_SCAN:
        LD      HL,KEYBASE+1
        LD      DE,M4_KEYTAB
        LD      B,7
M4_KEYRW:
        LD      A,(HL)
        OR      A
        JR      NZ,M4_KEYBT
        SLA     L
        LD      A,E
        ADD     A,8
        LD      E,A
; All linked users place the compact 56-byte table within one page.  Keeping
; only the low-byte row advance saves the boot diagnostics four bytes needed
; for Shift-Left without enlarging their single-sector carrier.
M4_KEYNX:
        DJNZ    M4_KEYRW
        XOR     A
        RET
M4_KEYBT:
        RRCA
        JR      C,M4_KEYFD
        INC     DE
        JR      M4_KEYBT
M4_KEYFD:
        LD      A,(DE)
        LD      C,A
        LD      A,(KEYBASE+128) ; Model 4 modifier row: either Shift bit
        AND     3
        LD      A,C
        RET     Z
        CP      8              ; Shift-Left supplies DEL/Backspace distinctly
        LD      A,127
        RET     Z
        LD      A,C
        CP      '-'
        JR      Z,M4_KSTAR
        CP      '/'
        RET     NZ
        LD      A,'?'
        RET
M4_KSTAR:
        LD      A,'*'
        RET

M4_KEYTAB:
        DB      '@ABCDEFG'
        DB      'HIJKLMNO'
        DB      'PQRSTUVW'
        DB      'XYZ',0,0,0,0,0
        DB      '01234567'
        DB      '89:;,-./'
; Patch 2026-09-02: publish the Model 4 special-key row instead of silently
; discarding it.  These are the conventional ASCII/control representations:
; Enter, Clear/Insert, Break, Up, Down, Left, Right, Space.  The CCP consumes
; them as editor keys; ordinary programs continue to receive the same bytes
; through BIOS CONIN and the BDOS console functions.
        DB      13,31,3,11,10,8,9,' '
M4CURSOR:
        DW      VIDEOBASE
M4COLUMN:
        DB      0
M4_PENDING:
        DB      0
