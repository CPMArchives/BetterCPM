; Poll the FDC UART, which has RDA on bit 6 and TBE on bit 7.
; The pinned UART emulator strips output parity (seven-bit console).
CM_CONST:
        IN A,(CM_SSTAT)
        AND 040H
        RET
CM_CONIN:
        CALL CM_CONST
        JR Z,CM_CONIN
        IN A,(CM_SDATA)
        RET
CM_CONOUT:
        LD A,C
; Private leaf for bound display modules: A=byte, preserve AF and all registers.
CM_TXA:
        PUSH AF
CM_TXWAIT:
        IN A,(CM_SSTAT)
        AND 080H
        JR Z,CM_TXWAIT
        POP AF
        OUT (CM_SDATA),A
        RET
CM_STRING:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        LD C,A
        CALL CM_CONOUT
        JR CM_STRING
