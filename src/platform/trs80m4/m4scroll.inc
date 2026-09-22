; ********************************************************************************
; *                   TRS-80 Model 4 Scrolling Console                          *
; *                                                                              *
; * Resident 80-column, 24-row output wrapper around the compact Model 4 console.*
; * Enforces the screen boundary, scrolls at the bottom row, handles backspace   *
; * cursor motion, and provides BetterCP/M's private cursor-character service.   *
; ********************************************************************************

; ================================================================================
; =                         Bounded Console Output                              =
; =                                                                              =
; = Extends the compact loader console with resident screen-boundary handling,   =
; = scrolling, backspace motion, and reverse-video cursor presentation.          =
; ================================================================================

; -------------------------------------------------------------------------------
; Scrolling Output
; -------------------------------------------------------------------------------


M4_SCROLL_OUT:                          ; write bounded scrolling console character
        LD      A,C
        CP      8
        JR      Z,M4_BACKSPACE
        CP      01CH
        JP      Z,M4_INIT               ; resident Model 4 clear screen and cursor home
        CALL    M4_OUT
        LD      HL,(M4CURSOR)
        LD      DE,VIDEOEND
        OR      A
        SBC     HL,DE
        RET     C

        LD      HL,VIDEOBASE+VIDEOCOLS
        LD      DE,VIDEOBASE
        LD      BC,VIDEOSIZE-VIDEOCOLS
        LDIR
        LD      HL,VIDEOEND-VIDEOCOLS
        LD      DE,VIDEOEND-VIDEOCOLS+1
        LD      BC,VIDEOCOLS-1
        LD      (HL),020H
        LDIR

  ; The last Model 4 screen row lies wholly within one 256-byte page.
  ; Add the column to L directly; no separate 16-bit offset is needed.
        LD      A,(M4COLUMN)
        LD      HL,VIDEOEND-VIDEOCOLS
        ADD     A,L
        LD      L,A
        LD      (M4CURSOR),HL
        RET

  ; Patch 2026-09-07: CONIN echoed BS correctly, but the old output leaf
  ; planted an 08H character on the screen.  Move left without erasing; the
  ; caller supplies SPACE/BS when rubout is wanted.  Keep this in the resident
  ; wrapper so the little boot loaders retain their original console size.

M4_BACKSPACE:                           ; move cursor left for backspace
        LD      HL,M4COLUMN
        LD      A,(HL)
        OR      A
        RET     Z                       ; do not back over the beginning of a line
        DEC     (HL)
        LD      HL,(M4CURSOR)
        DEC     HL
        LD      (M4CURSOR),HL
        RET

  ; BetterCP/M private cursor-character operation. C=0 queries support. Any
  ; other byte is written at the current console position in reverse video and
  ; advances exactly like ordinary output. Model 4 mode is initialized with
  ; reverse-video interpretation enabled, so bit 7 selects the inverse glyph.

; -------------------------------------------------------------------------------
; Cursor Presentation
; -------------------------------------------------------------------------------

M4_CUROUT:                              ; write reverse-video cursor character
        LD      A,C
        OR      A
        JR      Z,M4_CURQUERY
        OR      080H
        LD      C,A
        CALL    M4_SCROLL_OUT

M4_CURQUERY:                            ; report cursor-output support
        LD      A,1
        RET
