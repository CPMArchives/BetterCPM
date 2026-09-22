; ********************************************************************************
; *                    z80pack Variable-Sector Record I/O                        *
; *                                                                              *
; * Adapts complete CPMSIM physical-sector transfers to the BIOS 128-byte record *
; * interface. 128-byte media use the caller DMA directly; larger sectors stage *
; * through LY_BUF and copy only the selected logical record.                    *
; ********************************************************************************

; ================================================================================
; =                          Logical Record I/O                                 =
; =                                                                              =
; = Reads and writes CP/M 128-byte records while deblocking larger physical     =
; = sectors through the shared staging buffer.                                   =
; ================================================================================

BIOREAD:                                ; read one CP/M logical record
        CALL    LY_DISK+3
        RET     NZ
        CALL    ZR_SIZE
        OR      A
        JR      NZ,ZR_READ
        LD      HL,(BIO_DMA)
        JP      LY_DISK+9

ZR_READ:                                ; read staged physical sector
        CALL    ZR_STAGE
        CALL    LY_DISK+9
        RET     NZ
        CALL    ZR_SLOT
        LD      DE,(BIO_DMA)
        LD      BC,128
        LDIR
        XOR     A
        RET

BIOWRITE:                               ; write one CP/M logical record
        CALL    LY_DISK+3
        RET     NZ
        CALL    ZR_SIZE
        OR      A
        JR      NZ,ZR_WRITE
        LD      HL,(BIO_DMA)
        JP      LY_DISK+12

ZR_WRITE:                               ; write staged physical sector
        CALL    ZR_STAGE
        CALL    LY_DISK+9
        RET     NZ
        CALL    ZR_SLOT
        EX      DE,HL
        LD      HL,(BIO_DMA)
        LD      BC,128
        LDIR
        CALL    ZR_SIZE
        CALL    ZR_STAGE
        JP      LY_DISK+12

  ; Keep 256/512-byte physical transfers out of the first half of LY_BUF.  The
  ; protected module loader uses that half for four accumulated CP/M records.
  ; A full 1024-byte sector necessarily consumes the complete shared buffer.

; -------------------------------------------------------------------------------
; Staging Buffer Selection
; -------------------------------------------------------------------------------

ZR_STAGE:                               ; select staging-buffer base
        CP      3
        LD      HL,LY_BUF
        RET     NC
        LD      HL,LY_BUF+512
        RET

  ; Return the selected binding's maximum physical-sector size code in A.

; -------------------------------------------------------------------------------
; Physical Sector Size
; -------------------------------------------------------------------------------

ZR_SIZE:                                ; return maximum physical-sector size
        LD      A,(BIO_DRIVE)
        LD      HL,LY_TAB+34
        LD      DE,80
        OR      A
        JR      Z,ZR_SIZEOK

ZR_SIZELP:                              ; scan sector-size map
        ADD     HL,DE
        DEC     A
        JR      NZ,ZR_SIZELP

ZR_SIZEOK:                              ; return selected sector-size code
        LD      A,(HL)
        RET

  ; Return HL = address of the selected 128-byte record within LY_BUF.

; -------------------------------------------------------------------------------
; Logical Record Slot
; -------------------------------------------------------------------------------

ZR_SLOT:                                ; locate 128-byte record slot
        CALL    ZR_SIZE
        CALL    ZR_STAGE
        EX      DE,HL
        LD      A,(BIO_QUART)
        LD      H,A
        LD      L,0
        SRL     H
        RR      L
        ADD     HL,DE
        RET
