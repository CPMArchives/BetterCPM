; TRS-80 Model 4 physical 512-byte sector reader.
; A=cylinder, B=side, C=sector ID, HL=destination. Returns A=0/Z or status/NZ.

M4_READ:
        LD      (M4R_CYL),A
        IF      M4_MULTI_DRIVE EQ 1
        CALL    M4_DCHG
        ENDIF
        LD      A,B
        AND     1
        RLCA
        RLCA
        RLCA
        RLCA
        OR      080H            ; MFM and side; drive comes from BIOS mapping
        LD      B,A
        LD      A,(B_PDrive)
        OR      B
        LD      (M4R_SEL),A
        OUT     (FDCSELECT),A
        IF      M4_MULTI_DRIVE EQ 1
        CALL    M4_DWAIT
        ENDIF
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
        IF      M4_MULTI_DRIVE EQ 1
M4R_DRIVE:
        DB      0FFH
M4R_CHANGED:
        DB      0

; Patch 2026-09-01: a newly selected physical floppy needs motor settling
; time before its first seek. Later sectors on that drive incur no delay.
M4_DCHG:
        LD      A,(B_PDrive)
        LD      D,A
        LD      A,(M4R_DRIVE)
        CP      D
        LD      A,0
        JR      Z,M4_DCSTORE
        LD      A,D
        LD      (M4R_DRIVE),A
        LD      A,0FFH
M4_DCSTORE:
        LD      (M4R_CHANGED),A
        RET
M4_DWAIT:
        LD      A,(M4R_CHANGED)
        OR      A
        RET     Z
        PUSH    BC
        LD      B,2
M4_DWOUT:
        LD      DE,0
M4_DWIN:
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4_DWIN
        DJNZ    M4_DWOUT
        POP     BC
        ; The WD track register is shared although drive heads are not. Restore
        ; the newly selected drive so the following seek starts coherently.
        LD      A,FDCRESTORE
        OUT     (FDCCOMMAND),A
        LD      DE,0
M4_DWREST:
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4_DWRDONE
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4_DWREST
M4_DWRDONE:
        XOR     A
        LD      (M4R_CHANGED),A
        RET
        ENDIF

; Write one complete 512-byte sector. Parameters and status match M4_READ.
        IF      M4_READ_ONLY EQ 0
M4_WRITE:
        LD      (M4W_CYL),A
        IF      M4_MULTI_DRIVE EQ 1
        CALL    M4_DCHG
        ENDIF
        LD      A,C
        LD      (M4W_SEC),A
        LD      A,B
        AND     1
        RLCA
        RLCA
        RLCA
        RLCA
        OR      080H
        LD      B,A
        LD      A,(B_PDrive)
        OR      B
        OUT     (FDCSELECT),A
        IF      M4_MULTI_DRIVE EQ 1
        CALL    M4_DWAIT
        ENDIF
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
