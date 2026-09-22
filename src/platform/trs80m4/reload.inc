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
        LD HL,LY_CFG
        LD DE,M4_RLTAB
        CALL M4_FETCH                   ; selector occupies the reloader block tail
        POP AF
        RET NZ
        JP LY_CFG+0380H

M4_OVLOAD:                              ; load control overlay
        LD HL,LY_CFG
        LD DE,M4_OVTAB
  ; Fetch two physical sectors.
  ; IN: HL = destination, DE = cylinder/side/sector triples.
  ; OUT: A = status, Z if good.  AF,BC,DE,HL used; IX preserved.
  ; The last byte of a triple may replace H after the pointer is spent.

; -------------------------------------------------------------------------------
; Physical Sector Fetch
; -------------------------------------------------------------------------------

M4_FETCH:                               ; fetch two boot-media sectors
        LD B,2

M4_RLLOOP:                              ; read next physical sector
        PUSH BC
        PUSH DE
        EX DE,HL
        LD A,(HL)
        INC HL
        LD C,(HL)
        INC HL
        LD H,(HL)
        LD B,C
        LD C,H
        EX DE,HL
        CALL BIOPHREAD
        POP DE
        POP BC
        RET NZ
        INC DE
        INC DE
        INC DE
        DJNZ M4_RLLOOP
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
