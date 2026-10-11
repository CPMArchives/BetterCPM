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

M4_IN:                                  ; read keyboard character
        LD      A,(M4_PENDING+1)
        OR      A
        JR      NZ,M4_KEYCHANGE

M4_INWAIT:                              ; wait for keyboard input
        CALL    M4_SCAN
        OR      A
        JR      Z,M4_INWAIT
        LD      D,A
        LD      (M4_PENDING),DE
  ; Patch 2026-09-02: the original whole-matrix release wait could discard a
  ; second key pressed before the first was released.  Retain that debounce for
  ; reliable repeated letters, but queue one different overlapping key.

; -------------------------------------------------------------------------------
; Key Debounce and Pending Input
; -------------------------------------------------------------------------------

M4_KEYCHANGE:                           ; handle changed key state
        CALL    M4_SCAN
        OR      A
        JR      Z,M4_KEYDONE
  ; E identifies the physical matrix slot. Compare that identity, never
  ; its translated byte: a Shift/Control release is not another keypress.
        LD      D,A
        LD      A,(M4_PENDING)
        CP      E
        JR      Z,M4_KEYCHANGE
        LD      A,(M4_PENDING+1)
        LD      (M4_PENDING),DE
        RET

M4_KEYDONE:                             ; finish keyboard scan
        LD      HL,M4_PENDING+1
        LD      A,(HL)
        LD      (HL),0
        RET

  ; Patch 2026-09-01: rows are selected by successive address bits at
  ; F401h..F440h.  Modifier/configuration policy remains above this scanner.

; -------------------------------------------------------------------------------
; Keyboard Matrix Scan
; -------------------------------------------------------------------------------

M4_STAT:                                ; status uses the same physical scan
M4_SCAN:                                ; scan keyboard matrix
        LD      HL,KEYBASE+1
        LD      E,0                     ; physical matrix slot, 0..55
        LD      B,7

M4_KEYRW:                               ; scan next keyboard row
        LD      A,(HL)
        OR      A
        JR      NZ,M4_KEYBT
        SLA     L
        LD      A,E
        ADD     A,8
        LD      E,A

M4_KEYNX:                               ; advance keyboard row
        DJNZ    M4_KEYRW
        XOR     A
        RET

; -------------------------------------------------------------------------------
; Key Translation
; -------------------------------------------------------------------------------

M4_KEYBT:                               ; translate pressed key bit
        RRCA
        JR      C,M4_KEYFD
        INC     E
        JR      M4_KEYBT

M4_KEYFD:                               ; finish key translation
  ; The first rows are ASCII runs: @.._, 0..;, and ,../. Keeping only
  ; the eight special keys recovers space for Montezuma punctuation chords.
        LD      A,E
        CP      32
        JR      NC,M4_NUMKEY
        ADD     A,'@'
        JR      M4_CHAR
M4_NUMKEY:
        CP      44
        JR      NC,M4_PUNKEY
        ADD     A,16
        JR      M4_CHAR
M4_PUNKEY:
        CP      48
        JR      C,M4_CHAR
        SUB     48
        LD      HL,M4_KEYTAB
        LD      B,0
        LD      C,A
        ADD     HL,BC
        LD      A,(HL)
M4_CHAR:
        LD      C,A
        LD      A,(KEYBASE+128)         ; shifts, Control, Caps, and F1-F3
        IF      M4_EDITOR_KEYS EQ 1
        LD      B,A
        AND     4
        JR      Z,M4_KEYSHIFT
  ; Publish ordinary ASCII control-letter values. This was previously omitted,
  ; making WordStar-style CCP editing keys physically impossible on the Model 4.
        LD      A,C
        SUB     ','
        CP      14
        JR      NC,M4_CTRLLETTER
        LD      HL,M4_CTRLTAB
        LD      B,0
        LD      C,A
        ADD     HL,BC
        LD      A,(HL)
        RET
M4_CTRLLETTER:
        LD      A,C
        CP      '@'
        RET     C
        CP      060H
        RET     NC
        AND     01FH
        RET

; -------------------------------------------------------------------------------
; Shifted Key Translation
; -------------------------------------------------------------------------------

M4_KEYSHIFT:                            ; translate shifted key
        LD      A,B
        ENDIF
        AND     3
        LD      A,C
        RET     Z
        IF      M4_EDITOR_KEYS EQ 1
        CP      28                      ; Shift-Left supplies DEL/Backspace distinctly
        ELSE
        CP      8
        ENDIF
        LD      A,127
        RET     Z
        LD      A,C
  ; The Model 4 shifted punctuation is two ASCII ranges. Keep letters and
  ; editor controls unchanged, and leave Shift-0 as 0 (no printed symbol).
        CP      ','
        RET     C
        CP      '<'
        RET     NC
        CP      '0'
        RET     Z
        CP      '1'
        JR      C,M4_KADD16
        SUB     10H                     ; 1..9, :, ; -> !..), *, +
        RET
M4_KADD16:
        ADD     A,10H                   ; , - . / -> < = > ?
        RET

; -------------------------------------------------------------------------------
; Special-Key Translation
; -------------------------------------------------------------------------------

M4_KEYTAB:                              ; keyboard translation table
  ; Enter, Clear/Insert, Break, Up, Down, Left, Right, Space.
  ; Restore normal arrow control codes; punctuation uses the MM chords.
        IF      M4_EDITOR_KEYS EQ 1
        DB      13,31,3,11,10,28,29,' '
        ELSE
        DB      13,31,3,11,10,8,9,' '
        ENDIF

  ; CTRL punctuation is indexed by the physical unshifted character ,..9.
  ; MM calls these CTRL <, -, >, /, 1, 3, 5, 7, (, ). Shift is immaterial
  ; to the physical chord. Unassigned number chords keep the digit unchanged.
        IF      M4_EDITOR_KEYS EQ 1
M4_CTRLTAB:
        DB      '{','_','}',05CH,'0','|','2','~','4','^','6',060H,'[',']'
        ENDIF

; ================================================================================
; =                            Console Working State                             =
; =                                                                              =
; = Defines the physical cursor, display column, and pending-key state retained by =
; = the shared Model 4 console implementation.                                   =
; ================================================================================
; -------------------------------------------------------------------------------
; Console State
; -------------------------------------------------------------------------------

M4CURSOR:                               ; physical cursor address
        DW      VIDEOBASE

M4COLUMN:                               ; current display column
        DB      0

M4_PENDING:                             ; raw key identity, then translated byte
        DW      0
