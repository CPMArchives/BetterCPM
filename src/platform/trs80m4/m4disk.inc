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
M4R_IDLE:
        IN      A,(FDCSTATUS)
        AND     1
        JR      NZ,M4R_IDLE
        LD      A,(M4R_CYL)
        OUT     (FDCDATA),A
        LD      A,FDCSEEK
        OUT     (FDCCOMMAND),A
M4R_SEEK:
        IN      A,(FDCSTATUS)
        AND     1
        JR      NZ,M4R_SEEK
        LD      A,C
        OUT     (FDCSECTOR),A
        LD      A,FDCREAD
        OUT     (FDCCOMMAND),A
        LD      C,FDCDATA
        LD      B,0
        CALL    M4R_256
        LD      B,0
        CALL    M4R_256
M4R_DONE:
        IN      A,(FDCSTATUS)
        BIT     0,A
        JR      NZ,M4R_DONE
        AND     09CH
        RET
M4R_256:
        IN      A,(FDCSTATUS)
        AND     2
        JR      Z,M4R_256
        INI
        JR      NZ,M4R_256
        RET

M4R_CYL:
        DB      0
M4R_SEL:
        DB      081H

; Write one complete 512-byte sector. Parameters and status match M4_READ.
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
M4W_IDLE:
        IN      A,(FDCSTATUS)
        AND     1
        JR      NZ,M4W_IDLE
        LD      A,(M4W_CYL)
        OUT     (FDCDATA),A
        LD      A,FDCSEEK
        OUT     (FDCCOMMAND),A
M4W_SEEK:
        IN      A,(FDCSTATUS)
        AND     1
        JR      NZ,M4W_SEEK
        LD      A,(M4W_SEC)
        OUT     (FDCSECTOR),A
        LD      A,FDCWRITE
        OUT     (FDCCOMMAND),A
        LD      C,FDCDATA
        LD      B,0
        CALL    M4W_256
        LD      B,0
        CALL    M4W_256
M4W_DONE:
        IN      A,(FDCSTATUS)
        BIT     0,A
        JR      NZ,M4W_DONE
        AND     0FCH
        RET
M4W_256:
        IN      A,(FDCSTATUS)
        AND     2
        JR      Z,M4W_256
        OUTI
        JR      NZ,M4W_256
        RET
M4W_CYL:
        DB      0
M4W_SEC:
        DB      1
