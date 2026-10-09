; Transient-only trailing /O, /S and /B options. Repetition is idempotent, but
; overwrite and skip are mutually exclusive. Strip options before preflight.
BC_COPT:
        XOR     A
        LD      (CT_BATCH),A
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
        JR      Z,CTOSLASH
        CP      'B'
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
        CP      'B'
        JR      Z,CTSETB
        CP      'S'
        JR      Z,CTSETS
        LD      A,(CT_SKIP)
        OR      A
        JR      NZ,CT_OBAD
        INC     A
        LD      (BC_OVER),A
        JR      CTOTAIL
CTSETB:
        LD      A,1
        LD      (CT_BATCH),A
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
        JP      NZ,CTROFAIL
        LD      A,(CT_SKIP)
        OR      A
        JP      NZ,CTSKIP
        LD      A,(BC_OVER)
        OR      A
        JP      NZ,CTALLOW
        LD      A,(CT_BATCH)
        OR      A
        JP      Z,CTPROMPT
        LD      HL,CT_FAILS
        INC     (HL)
        LD      DE,BC_REXMSG
        CALL    BC_PRINT
        RET
CTSKIP:
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

CTPROMPT:
        CALL    CTPAIR
CTASK:
        LD      DE,CT_ASKM
        CALL    BC_PRINT
CTREAD:
        LD      E,0FFH
        LD      C,6
        CALL    BDOS                    ; direct input permits explicit Ctrl-C
        OR      A
        JR      Z,CTREAD
        CP      3
        JP      Z,CTABORT
        CP      13
        JR      Z,CTREAD
        CP      10
        JR      Z,CTREAD
        CP      'a'
        JR      C,CTANSWER
        CP      'z'+1
        JR      NC,CTANSWER
        SUB     32
CTANSWER:
        LD      (CT_CHOICE),A
        CALL    BC_PCHAR
        LD      DE,BC_NL
        CALL    BC_PRINT
        LD      A,(CT_CHOICE)
        CP      'Y'
        JP      Z,CTYALLOW             ; one file, no sticky overwrite flag
        CP      'N'
        JP      Z,CTSKIP
        CP      'R'
        JP      Z,CTRENAME
        CP      'O'
        JR      Z,CTALLYES
        CP      'S'
        JR      Z,CTALLNO
        LD      DE,CT_HELPM
        CALL    BC_PRINT
        JP      CTASK
CTALLYES:
        LD      A,1
        LD      (BC_OVER),A
        JP      CTALLOW
CTALLNO:
        LD      A,1
        LD      (CT_SKIP),A
        JP      CTSKIP
CTABORT:
        LD      A,1
        LD      (BC_WERROR),A
        LD      DE,CT_ABORTM
        CALL    BC_PRINT
        RET                            ; driver stops and restores caller DU/DMA

; Build a concrete source -> destination label without BDOS register clobber.
CTPAIR:
        LD      HL,CT_LINE
        LD      (HL),13
        INC     HL
        LD      (HL),10
        INC     HL
        LD      A,(BC_CSDRV)
        ADD     A,'A'
        LD      (HL),A
        INC     HL
        LD      A,(BC_CSUSR)
        CALL    CTUSER
        LD      DE,BC_FCB+1
        CALL    CTNAME
        LD      DE,CT_ARROW
        LD      BC,4
        EX      DE,HL
        LDIR
        EX      DE,HL
        LD      A,(BC_CDDRV)
        ADD     A,'A'
        LD      (HL),A
        INC     HL
        LD      A,(BC_CDUSR)
        CALL    CTUSER
        LD      DE,BC_NEWFCB+1
        CALL    CTNAME
        LD      (HL),0
        LD      HL,CT_LINE
CTPAIRLP:
        LD      A,(HL)
        OR      A
        RET     Z
        PUSH    HL
        CALL    BC_PCHAR
        POP     HL
        INC     HL
        JR      CTPAIRLP
CTUSER:
        LD      E,0
CTTEN:
        CP      10
        JR      C,CTONES
        SUB     10
        INC     E
        JR      CTTEN
CTONES:
        PUSH    AF
        LD      A,E
        OR      A
        JR      Z,CTUNIT
        ADD     A,'0'
        LD      (HL),A
        INC     HL
CTUNIT:
        POP     AF
        ADD     A,'0'
        LD      (HL),A
        INC     HL
        LD      (HL),':'
        INC     HL
        RET
CTNAME:
        LD      B,8
        CALL    CTNFIELD
        LD      A,(DE)
        AND     7FH
        CP      ' '
        RET     Z
        LD      (HL),'.'
        INC     HL
        LD      B,3
CTNFIELD:
        LD      A,(DE)
        AND     7FH
        CP      ' '
        JR      Z,CTNSPACE
        LD      (HL),A
        INC     HL
CTNSPACE:
        INC     DE
        DJNZ    CTNFIELD
        RET
CT_ARROW:
        DB      ' -> '
