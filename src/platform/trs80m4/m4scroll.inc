; Bounded 80-column, 24-row console output for the resident BIOS.
;
; Patch 2026-09-01: the first long ENTRYTST run exposed the old bring-up
; console's deliberate lack of a screen boundary.  Preserve M4_OUT for the
; size-constrained loaders, but put the resident operating system behind this
; scrolling wrapper.

M4_SCROLL_OUT:
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

        LD      A,(M4COLUMN)
        LD      E,A
        LD      D,0
        LD      HL,VIDEOEND-VIDEOCOLS
        ADD     HL,DE
        LD      (M4CURSOR),HL
        RET
