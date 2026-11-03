; ********************************************************************************
; *                       TRS-80 Model 4 Physical Console                        *
; *                                                                              *
; * Shared BetterCP/M console implementation providing direct video output and   *
; * keyboard-matrix input for the Model 4 BIOS and bootstrap environment.        *
; ********************************************************************************

; ================================================================================
; =                            Model 4 Console Output                            =
; =                                                                              =
; = Initializes the physical console and writes characters directly to Model 4 video =
; = memory while maintaining cursor position and screen-column state.            =
; ================================================================================
; -------------------------------------------------------------------------------
; Console Initialization
; -------------------------------------------------------------------------------

M4_INIT:                                ; initialize Model 4 console
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

; -------------------------------------------------------------------------------
; Character Output
; -------------------------------------------------------------------------------

M4_OUT:                                 ; write console character
        LD      A,C
        CP      13
        JR      Z,M4_CR
        CP      10
        JR      Z,M4_LF
        LD      HL,(M4CURSOR)
        LD      (HL),A
        INC     HL
        LD      A,(M4COLUMN)
        INC     A
        CP      VIDEOCOLS
        JR      C,M4_STCOL
        XOR     A

M4_STCOL:                               ; store updated console column and cursor
        LD      (M4COLUMN),A
M4_SETC:
        LD      (M4CURSOR),HL
        RET

; -------------------------------------------------------------------------------
; Carriage Return and Line Feed
; -------------------------------------------------------------------------------

M4_CR:                                  ; perform carriage return
        LD      A,(M4COLUMN)
        LD      E,A
        LD      D,0
        LD      HL,(M4CURSOR)
        OR      A
        SBC     HL,DE
        XOR     A
        JR      M4_STCOL

M4_LF:                                  ; perform line feed
        LD      HL,(M4CURSOR)
        LD      DE,VIDEOCOLS
        ADD     HL,DE
        JR      M4_SETC

; ================================================================================
; =                            Model 4 Keyboard Input                            =
; =                                                                              =
; = Scans the Model 4 keyboard matrix, debounces repeated keys, preserves overlapping =
; = keypresses, applies modifier mappings, and publishes ASCII/control key values. =
; ================================================================================
; -------------------------------------------------------------------------------
; Console Status and Blocking Input
; -------------------------------------------------------------------------------

M4_IN:                                  ; return captured input on release or rollover
        CALL    M4_SCAN
        OR      A
        JR      Z,M4_KEYDONE
        LD      D,A
        LD      HL,M4_PENDING
        LD      A,E
        CP      (HL)                    ; compare physical identity, never ASCII
        JR      Z,M4_IN
        LD      (HL),E
        INC     HL
        LD      A,(HL)
        LD      (HL),D

M4_RETURN:
        OR      A
        RET     NZ
        JR      M4_IN

M4_KEYDONE:
        LD      HL,M4_PENDING
        LD      (HL),0FFH                ; sentinel is outside physical slots 0..55
        INC     HL
        LD      A,(HL)
        LD      (HL),D                  ; M4_SCAN always returns D=0
        JR      M4_RETURN

; -------------------------------------------------------------------------------
; Keyboard Matrix Scan
; -------------------------------------------------------------------------------

M4_STAT:
M4_SCAN:
        IF      M4_EDITOR_KEYS EQ 1
  ; CAPS is a momentary matrix key. Confirm both press and release before
  ; changing the tracked state; only a confirmed press changes letter case.
  ; The delay is bounded, not a key-release wait. Nominal 15ms at 4.05504MHz;
  ; real Model 4 wait states must be included in native timing qualification.
        LD      A,(KEYBASE+128)
        AND     8
        LD      B,A
        LD      HL,M4_KSTATE
        XOR     (HL)
        AND     8
        JR      Z,M4_ROWS
        LD      DE,00922H
M4_KDWAIT:
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4_KDWAIT
        LD      A,(KEYBASE+128)
        AND     8
        CP      B
        JR      NZ,M4_ROWS              ; transient did not confirm
        RLCA
        RLCA                            ; current CAPS bit 3 -> case mask bit 5
        OR      8                       ; change tracked press state on either edge
        XOR     (HL)
        LD      (HL),A
        ENDIF

M4_ROWS:
        LD      HL,KEYBASE+1
        LD      DE,0                    ; E=physical slot, D=0 on every return path
        LD      B,7
M4_KEYRW:
        LD      A,(HL)
        OR      A
        JR      NZ,M4_KEYBT
        SLA     L
        LD      A,E
        ADD     A,8
        LD      E,A
M4_KEYNX:
        DJNZ    M4_KEYRW
        XOR     A
        RET

M4_KEYBT:
        RRCA
        JR      C,M4_KEYFD
        INC     E
        JR      M4_KEYBT

; -------------------------------------------------------------------------------
; Key Translation
; -------------------------------------------------------------------------------

M4_KEYFD:
        LD      A,(KEYBASE+128)
        LD      B,A
        LD      A,E
        CP      32
        JR      NC,M4_NUMKEY
        IF      M4_EDITOR_KEYS EQ 1
        BIT     2,B
        RET     NZ                      ; Control @.._ is the physical index
        ENDIF
        ADD     A,'@'
        LD      C,A
        IF      M4_EDITOR_KEYS EQ 1
        LD      A,E
        DEC     A
        CP      26
        LD      A,C
        RET     NC                      ; keep @ and unconnected [.._ slots
        LD      A,B
        AND     3
        LD      A,C
        RET     NZ                      ; either/both Shift keys force uppercase
        LD      A,(M4_KSTATE)
        AND     020H
        OR      C
        RET
        ELSE
        JR      M4_KEYSHIFT             ; retain bring-up uppercase behavior
        ENDIF
M4_NUMKEY:
        ADD     A,16
        CP      60
        JR      C,M4_CHAR
        SUB     16
        CP      48
        JR      C,M4_CHAR
        LD      HL,M4_KEYTAB-48
        ADD     HL,DE
        LD      A,(HL)
M4_CHAR:
        LD      C,A
        IF      M4_EDITOR_KEYS EQ 1
        BIT     2,B
        JR      Z,M4_KEYSHIFT
        SUB     ','
        CP      14
        JR      NC,M4_CTRLLETTER
        LD      HL,M4_CTRLTAB
        LD      B,D                     ; D=0 established by M4_ROWS
        LD      C,A
        ADD     HL,BC
        LD      A,(HL)
        RET
M4_CTRLLETTER:
        LD      A,C
        CP      01BH                    ; Ctrl-CLEAR is DEL; other specials unchanged
        RET     NZ
        LD      A,07FH
        RET
        ENDIF

M4_KEYSHIFT:
        LD      A,B
        AND     3
        LD      A,C
        RET     Z
        IF      M4_EDITOR_KEYS EQ 1
        CP      28
        ELSE
        CP      8
        ENDIF
        LD      A,127
        RET     Z                       ; Shift-Left
        LD      A,C
        CP      ','
        RET     C
        IF      M4_EDITOR_KEYS EQ 0
        CP      '<'
        RET     NC                      ; letters reach this path only in bring-up
        ENDIF
        CP      '0'
        RET     Z                       ; preserve Shift-0
        XOR     010H                    ; ,../ -> <..? and 1..; -> !..+
        RET

M4_KEYTAB:
        IF      M4_EDITOR_KEYS EQ 1
        DB      13,27,3,11,10,28,29,' '
        ELSE
        DB      13,27,3,11,10,8,9,' '
        ENDIF

        IF      M4_EDITOR_KEYS EQ 1
M4_CTRLTAB:
        DB      '{','_','}',05CH,'0','|','2','~','4','^','6',060H,'[',']'
M4_KSTATE:
  ; Bit 3 = confirmed physical CAPS; bit 5 = lowercase mask (Caps Lock off).
  ; 20h -> 08h -> 00h -> 28h -> 20h for press/release/press/release.
  ; This replaces the former padding byte. Screen clearing must not reset it.
        DB      020H
        ENDIF

; -------------------------------------------------------------------------------
; Console Working State
; -------------------------------------------------------------------------------

M4CURSOR:
        DW      VIDEOBASE
M4COLUMN:
        DB      0
M4_PENDING:                             ; raw identity, then captured byte
        DW      000FFH
