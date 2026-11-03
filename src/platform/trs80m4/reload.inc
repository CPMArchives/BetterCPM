; ********************************************************************************
; *                    TRS-80 Model 4 System Overlay Loader                      *
; *                                                                              *
; * Boot-media adapter for loading the command reloader, RSX carrier, and system *
; * control overlay from fixed physical sectors. Sector placement remains a      *
; * platform concern and is deliberately kept outside the common BIOS.           *
; ********************************************************************************

; ================================================================================
; =                           System Overlay Loads                              =
; =                                                                              =
; = Provides the Model 4 platform entry points that fetch protected system       =
; = components from their fixed boot-media sectors into their runtime buffers.   =
; ================================================================================

M4_RELOAD:                              ; load command-environment reloader
        LD SP,0100H
        LD HL,LY_LOAD
        LD DE,M4_RLTAB
        CALL M4_FETCH
        JR NZ,M4_RLFAIL
        LD SP,LY_STKT
        JP LY_LOAD

M4_RSLOAD:                              ; load RSX carrier
        PUSH AF
        LD DE,M4_RLTAB
        CALL M4_CFGFETCH                ; selector occupies the reloader block tail
        POP BC
        RET NZ
        LD A,B
        JP LY_RSSEL

M4_OVLOAD:                              ; load control overlay
        LD DE,M4_OVTAB
M4_CFGFETCH:
        LD HL,LY_CFG
  ; Fetch two physical sectors.
  ; IN: HL = destination, DE = cylinder/side/sector triples.
  ; OUT: A = status, Z if good.  AF,BC,DE,HL used; IX preserved.

; -------------------------------------------------------------------------------
; Physical Sector Fetch
; -------------------------------------------------------------------------------

M4_FETCH:                               ; fetch two boot-media sectors
        CALL M4_ONE
        RET NZ
  ; A successful first read falls through for the second. INC DE preserves
  ; the physical read's status flags; the tables remain arbitrary triples.

M4_ONE:                                 ; read one physical sector
        PUSH DE
        EX DE,HL
        LD A,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD C,(HL)
        EX DE,HL
        CALL BIOPHREAD
        POP DE
        INC DE
        INC DE
        INC DE
        RET

M4_RLFAIL:                              ; return sector-read failure
        JR M4_RLFAIL

; -------------------------------------------------------------------------------
; Boot-Media Sector Tables
; -------------------------------------------------------------------------------

M4_RLTAB:                               ; reloader sector table
  ; @reloader-sector-table@

M4_OVTAB:                               ; control-overlay sector table
  ; @control-sector-table@
