; BetterCP/M initial TRS-80 Model 4 hardware abstraction
;
; This is a bring-up interface, not the CP/M BIOS ABI.

        INCLUDE m4cons.inc

HAL_INIT:
        XOR     A
        OUT     (INTMASK),A
        OUT     (NMIREG),A
        LD      A,0C3H
        LD      (NMIVECTOR),A
        LD      HL,HAL_NMI
        LD      (NMIVECTOR+1),HL
        JP      M4_INIT

HAL_CONOUT      EQU     M4_OUT
HAL_CONST       EQU     M4_STAT
HAL_CONIN       EQU     M4_IN

; Read a 512-byte physical sector from drive 0, track 0, side 0.
; Input: C = physical sector number, HL = destination.
; Return: Z and A=0 on success; NZ and A=controller status on failure.
; Clobbers AF, BC, DE, HL.
HAL_READ0:
        LD      A,C
        OUT     (FDCSECTOR),A
        LD      A,081H
        OUT     (FDCSELECT),A
HWAITIDL:
        IN      A,(FDCSTATUS)
        AND     1
        JR      NZ,HWAITIDL
        LD      C,FDCDATA
        LD      DE,0C102H
        LD      A,D
        AND     0BFH
        OUT     (FDCSELECT),A
        LD      A,FDCREAD
        OUT     (FDCCOMMAND),A
HWAITBSY:
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,HWAITBSY
        LD      A,0C0H
        OUT     (NMIREG),A
HWAITDRQ:
        IN      A,(FDCSTATUS)
        AND     E
        JR      Z,HWAITDRQ
        INI
        LD      A,D
HREADLP:
        OUT     (FDCSELECT),A
        INI
        JR      HREADLP

HAL_NMI:
        POP     HL
        XOR     A
        OUT     (NMIREG),A
        IN      A,(FDCSTATUS)
        AND     09CH
        RET
