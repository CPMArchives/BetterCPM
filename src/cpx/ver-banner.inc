; Transient-only VER /BANNER; resident VER supplies a feature hint.
        CP      7
        JR      NZ,BC_VLEN
  ; Standalone /BANNER; validate the entire option before printing anything.
        LD      DE,BC_VOPT
        LD      C,7
BC_VBM:
        LD      A,(DE)
        CP      (HL)
        JR      NZ,BC_VERBAD
        INC     DE
        INC     HL
        DEC     C
        JR      NZ,BC_VBM
        LD      DE,BC_VBANT
        JP      BC_PRINT
BC_VLEN:
; @banner-data@
BC_VOPT:       DB      '/BANNER'
BC_VBANT:      DB      13,10
               DB      '------------------------------',13,10
               DB      '        BetterCP/M 0.3',13,10
               DB      'An enhanced CP/M-compatible OS',13,10
               DB      '             ----',13,10
               DB      'Type TYPE README.TXT for more',13,10
               DB      '------------------------------',13,10
               DB      '$'
