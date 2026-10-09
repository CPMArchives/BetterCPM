; Destination metadata is complete before changing source backup status.
CTBPOST:
        LD A,(CT_BACK)
        OR A
        RET Z
        CALL BC_CSELS
        LD HL,BC_FCB+11
        RES 7,(HL)
        LD DE,BC_FCB
        LD C,30
        CALL BDOS
        OR A
        RET Z
        JP CTBMFAIL

; The data is complete: retain it even if either metadata update failed.
; This file counts as failed; the frozen batch may continue.
CTBMFAIL:
        XOR A
        LD (BC_CMADE),A
        LD HL,CT_FAILS
        INC (HL)
        LD DE,CTB_MSG
        CALL BC_PRINT
        SCF
        RET
CTB_MSG: DB 13,10,'DATA COPIED; ATTRIBUTE STATUS INCOMPLETE',13,10,'$'
