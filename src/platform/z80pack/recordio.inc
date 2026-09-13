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
        LD      HL,LY_BUF
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
        LD      HL,LY_BUF
        CALL    LY_DISK+9
        RET     NZ
        CALL    ZR_SLOT
        EX      DE,HL
        LD      HL,(BIO_DMA)
        LD      BC,128
        LDIR
        LD      HL,LY_BUF
        JP      LY_DISK+12

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
        LD      A,(BIO_QUART)
        LD      H,A
        LD      L,0
        SRL     H
        RR      L
        LD      DE,LY_BUF
        ADD     HL,DE
        RET
