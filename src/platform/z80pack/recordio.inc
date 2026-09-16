; VARIABLE-SECTOR RECORD DMA
; Keep 128-byte media on the direct path because the resident module loader
; uses LY_BUF as its destination. Larger physical sectors are staged through
; LY_BUF and the selected 128-byte quarter is copied to or from the caller DMA.
BIOREAD:
        CALL    LY_DISK+3
        RET     NZ
        CALL    ZR_SIZE
        OR      A
        JR      NZ,ZR_READ
        LD      HL,(BIO_DMA)
        JP      LY_DISK+9
ZR_READ:
        CALL    ZR_STAGE
        CALL    LY_DISK+9
        RET     NZ
        CALL    ZR_SLOT
        LD      DE,(BIO_DMA)
        LD      BC,128
        LDIR
        XOR     A
        RET

BIOWRITE:
        CALL    LY_DISK+3
        RET     NZ
        CALL    ZR_SIZE
        OR      A
        JR      NZ,ZR_WRITE
        LD      HL,(BIO_DMA)
        JP      LY_DISK+12
ZR_WRITE:
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
ZR_STAGE:
        CP      3
        LD      HL,LY_BUF
        RET     NC
        LD      HL,LY_BUF+512
        RET

; Return the selected binding's maximum physical-sector size code in A.
ZR_SIZE:
        LD      A,(BIO_DRIVE)
        LD      HL,LY_TAB+34
        LD      DE,80
        OR      A
        JR      Z,ZR_SIZEOK
ZR_SIZELP:
        ADD     HL,DE
        DEC     A
        JR      NZ,ZR_SIZELP
ZR_SIZEOK:
        LD      A,(HL)
        RET

; Return HL = address of the selected 128-byte record within LY_BUF.
ZR_SLOT:
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
