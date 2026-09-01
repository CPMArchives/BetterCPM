; TRS-80 Model 4 physical 512-byte sector reader.
; A=cylinder, B=side, C=sector ID, HL=destination. Returns A=0/Z or status/NZ.

M4_READ:
        LD      (M4R_CYL),A
        LD      A,B
        AND     1
        RLCA
        RLCA
        RLCA
        RLCA
        OR      081H            ; drive 0, MFM
        LD      (M4R_SEL),A
        OUT     (FDCSELECT),A
        LD      DE,0
M4R_IDLE:
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4R_IDOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_IDLE
        JP      M4_TIMEOUT
M4R_IDOK:
        LD      A,(M4R_CYL)
        OUT     (FDCDATA),A
        LD      A,FDCSEEK
        OUT     (FDCCOMMAND),A
        LD      DE,0
M4R_SEEK:
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4R_SKOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_SEEK
        JP      M4_TIMEOUT
M4R_SKOK:
        LD      A,C
        OUT     (FDCSECTOR),A
        LD      A,FDCREAD
        OUT     (FDCCOMMAND),A
        LD      C,FDCDATA
        LD      B,0
        CALL    M4R_256
        RET     NZ
        LD      B,0
        CALL    M4R_256
        RET     NZ
        LD      DE,0
M4R_DONE:
        IN      A,(FDCSTATUS)
        BIT     0,A
        JR      Z,M4R_DNOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_DONE
        JP      M4_TIMEOUT
M4R_DNOK:
        AND     09CH
        RET
M4R_256:
        LD      DE,0
M4R_DRQ:
        IN      A,(FDCSTATUS)
        AND     2
        JR      NZ,M4R_BYTE
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_DRQ
        JP      M4_TIMEOUT
M4R_BYTE:
        INI
        JR      NZ,M4R_256
        XOR     A
        RET

M4R_CYL:
        DB      0
M4R_SEL:
        DB      081H

; Write one complete 512-byte sector. Parameters and status match M4_READ.
        IF      M4_READ_ONLY EQ 0
M4_WRITE:
        LD      (M4W_CYL),A
        LD      A,C
        LD      (M4W_SEC),A
        LD      A,B
        AND     1
        RLCA
        RLCA
        RLCA
        RLCA
        OR      081H
        OUT     (FDCSELECT),A
        LD      DE,0
M4W_IDLE:
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4W_IDOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_IDLE
        JP      M4_TIMEOUT
M4W_IDOK:
        LD      A,(M4W_CYL)
        OUT     (FDCDATA),A
        LD      A,FDCSEEK
        OUT     (FDCCOMMAND),A
        LD      DE,0
M4W_SEEK:
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4W_SKOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_SEEK
        JP      M4_TIMEOUT
M4W_SKOK:
        LD      A,(M4W_SEC)
        OUT     (FDCSECTOR),A
        LD      A,FDCWRITE
        OUT     (FDCCOMMAND),A
        LD      C,FDCDATA
        LD      B,0
        CALL    M4W_256
        RET     NZ
        LD      B,0
        CALL    M4W_256
        RET     NZ
        LD      DE,0
M4W_DONE:
        IN      A,(FDCSTATUS)
        BIT     0,A
        JR      Z,M4W_DNOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_DONE
        JP      M4_TIMEOUT
M4W_DNOK:
        AND     0FCH
        RET
M4W_256:
        LD      DE,0
M4W_DRQ:
        IN      A,(FDCSTATUS)
        AND     2
        JR      NZ,M4W_BYTE
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_DRQ
        JP      M4_TIMEOUT
M4W_BYTE:
        OUTI
        JR      NZ,M4W_256
        XOR     A
        RET
M4W_CYL:
        DB      0
M4W_SEC:
        DB      1
        ENDIF

M4_TIMEOUT:
        LD      A,1
        OR      A
        RET
