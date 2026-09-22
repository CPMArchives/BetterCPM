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
        LD      (M4CURSOR),HL
        LD      A,(M4COLUMN)
        INC     A
        CP      VIDEOCOLS
        JR      C,M4_STCOL
        XOR     A

M4_STCOL:                               ; store updated console column
        LD      (M4COLUMN),A
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
        LD      (M4CURSOR),HL
        XOR     A
        LD      (M4COLUMN),A
        RET

M4_LF:                                  ; perform line feed
        LD      HL,(M4CURSOR)
        LD      DE,VIDEOCOLS
        ADD     HL,DE
        LD      (M4CURSOR),HL
        RET

; ================================================================================
; =                            Model 4 Keyboard Input                            =
; =                                                                              =
; = Scans the Model 4 keyboard matrix, debounces repeated keys, preserves overlapping =
; = keypresses, applies modifier mappings, and publishes ASCII/control key values. =
; ================================================================================
; -------------------------------------------------------------------------------
; Console Status and Blocking Input
; -------------------------------------------------------------------------------

M4_STAT:                                ; return keyboard status
        JP      M4_SCAN

M4_IN:                                  ; read keyboard character
        LD      A,(M4_PENDING)
        OR      A
        JR      NZ,M4_KEYCHANGE

M4_INWAIT:                              ; wait for keyboard input
        CALL    M4_SCAN
        OR      A
        JR      Z,M4_INWAIT
        LD      (M4_PENDING),A
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
        LD      C,A
        LD      A,(M4_PENDING)
        CP      C
        JR      Z,M4_KEYCHANGE
        PUSH    AF
        LD      A,C
        LD      (M4_PENDING),A
        POP     AF
        RET

M4_KEYDONE:                             ; finish keyboard scan
        LD      HL,M4_PENDING
        LD      A,(HL)
        LD      (HL),0
        RET

  ; Patch 2026-09-01: rows are selected by successive address bits at
  ; F401h..F440h.  Modifier/configuration policy remains above this scanner.

; -------------------------------------------------------------------------------
; Keyboard Matrix Scan
; -------------------------------------------------------------------------------

M4_SCAN:                                ; scan keyboard matrix
        LD      HL,KEYBASE+1
        LD      DE,M4_KEYTAB
        LD      B,7

M4_KEYRW:                               ; scan next keyboard row
        LD      A,(HL)
        OR      A
        JR      NZ,M4_KEYBT
        SLA     L
        LD      A,E
        ADD     A,8
        LD      E,A
  ; BIOS growth can move the key table across a page boundary.
        JR      NC,M4_KEYNX
        INC     D

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
        INC     DE
        JR      M4_KEYBT

M4_KEYFD:                               ; finish key translation
        LD      A,(DE)
        LD      C,A
        LD      A,(KEYBASE+128)         ; shifts, Control, Caps, and F1-F3
        IF      M4_EDITOR_KEYS EQ 1
        LD      B,A
        AND     4
        JR      Z,M4_KEYSHIFT
  ; Publish ordinary ASCII control-letter values. This was previously omitted,
  ; making WordStar-style CCP editing keys physically impossible on the Model 4.
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
        CP      ':'
        JR      Z,M4_KSUB16
        CP      '4'
        JR      Z,M4_KSUB16
        CP      '-'
        JR      Z,M4_KADD16
        CP      '/'
        RET     NZ

M4_KADD16:                              ; advance key-table pointer by 16
        ADD     A,10H                   ; '-' -> '=', '/' -> '?'
        RET

M4_KSUB16:                              ; retreat key-table pointer by 16
        SUB     10H                     ; ':' -> '*', Shift-4 -> '$'
        RET

; -------------------------------------------------------------------------------
; Special-Key Translation
; -------------------------------------------------------------------------------

M4_KEYTAB:                              ; keyboard translation table
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
        IF      M4_EDITOR_KEYS EQ 1
        DB      13,31,3,11,10,28,29,' '
        ELSE
        DB      13,31,3,11,10,8,9,' '
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

M4_PENDING:                             ; pending overlapping key
        DB      0
