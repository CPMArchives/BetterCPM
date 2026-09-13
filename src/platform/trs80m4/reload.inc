; SYSTEM OVERLAY READ -- TRS-80 BOOT MEDIA ADAPTER
;
; PL_RELOAD comes here only after the transient has finished.  Its RAM
; may now be used for the reloader.  Keep SP below 0100H until the two
; sectors are in; only then is the reloader's own stack safe to use.
; Sector numbering belongs here, not in the common BIOS.
M4_RELOAD:
        LD SP,0100H
        LD HL,LY_LOAD
        LD DE,M4_RLTAB
        CALL M4_FETCH
        JR NZ,M4_RLFAIL
        LD SP,LY_STKT
        JP LY_LOAD
M4_RSLOAD:
        PUSH AF
        LD HL,LY_CFG
        LD DE,M4_RLTAB
        CALL M4_FETCH          ; selector occupies the reloader block tail
        POP AF
        RET NZ
        JP LY_CFG+0380H
M4_OVLOAD:
        LD HL,LY_CFG
        LD DE,M4_OVTAB
; Fetch two physical sectors.
; IN: HL = destination, DE = cylinder/side/sector triples.
; OUT: A = status, Z if good.  AF,BC,DE,HL used; IX preserved.
; The last byte of a triple may replace H after the pointer is spent.
M4_FETCH:
        LD B,2
M4_RLLOOP:
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
M4_RLFAIL:
        JR M4_RLFAIL
M4_RLTAB:
; @reloader-sector-table@

M4_OVTAB:
; @control-sector-table@
