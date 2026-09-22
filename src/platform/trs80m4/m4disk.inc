; ********************************************************************************
; *                      TRS-80 Model 4 Physical Sector I/O                      *
; *                                                                              *
; * Shared low-level 512-byte floppy-sector read/write implementation. Handles   *
; * physical drive selection, motor settling, seek/restore, WD controller DRQ    *
; * transfers, and status reporting for bootstrap and diagnostic clients.        *
; ********************************************************************************

; ================================================================================
; =                             Physical Sector Read                             =
; =                                                                              =
; = Reads one complete 512-byte Model 4 floppy sector, including drive selection, =
; = motor settling, seek, controller command, DRQ transfer, and status return.   =
; ================================================================================
; -------------------------------------------------------------------------------
; Read Setup and Drive Selection
; -------------------------------------------------------------------------------

M4_READ:                                ; read physical 512-byte sector
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
        OR      080H                    ; MFM and side; drive comes from BIOS mapping
        LD      B,A
        LD      A,(B_PDrive)
        OR      B
        LD      (M4R_SEL),A
        OUT     (FDCSELECT),A
        IF      M4_MULTI_DRIVE EQ 1
        CALL    M4_DWAIT
        ENDIF
        LD      DE,0

M4R_IDLE:                               ; wait for read controller idle
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4R_IDOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_IDLE
        JP      M4_TIMEOUT

M4R_IDOK:                               ; accept read idle state
        LD      A,(M4R_CYL)
        OUT     (FDCDATA),A
        LD      A,FDCSEEK
        OUT     (FDCCOMMAND),A
        LD      DE,0

; -------------------------------------------------------------------------------
; Read Seek
; -------------------------------------------------------------------------------

M4R_SEEK:                               ; seek for physical read
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4R_SKOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_SEEK
        JP      M4_TIMEOUT

M4R_SKOK:                               ; begin physical read command
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

M4R_DONE:                               ; finish physical read
        IN      A,(FDCSTATUS)
        BIT     0,A
        JR      Z,M4R_DNOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_DONE
        JP      M4_TIMEOUT

M4R_DNOK:                               ; return successful read
        AND     09CH
        RET

M4R_256:                                ; select 256-byte transfer half
        LD      DE,0

; -------------------------------------------------------------------------------
; Read Data Transfer
; -------------------------------------------------------------------------------

M4R_DRQ:                                ; poll read data request
        IN      A,(FDCSTATUS)
        AND     2
        JR      NZ,M4R_BYTE
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4R_DRQ
        JP      M4_TIMEOUT

M4R_BYTE:                               ; store next read byte
        INI
        JR      NZ,M4R_256
        XOR     A
        RET

M4R_CYL:                                ; saved read cylinder
        DB      0

M4R_SEL:                                ; saved read select byte
        DB      081H
        IF      M4_MULTI_DRIVE EQ 1

M4R_DRIVE:                              ; saved read drive
        DB      0FFH

M4R_CHANGED:                            ; read drive-change flag
        DB      0

  ; Patch 2026-09-01: a newly selected physical floppy needs motor settling
  ; time before its first seek. Later sectors on that drive incur no delay.

; ================================================================================
; =                           Drive-Change Preparation                           =
; =                                                                              =
; = Handles first access to a newly selected physical drive, including motor spin-up =
; = and track-zero restoration required by the WD controller's shared track register. =
; ================================================================================
; -------------------------------------------------------------------------------
; Motor Settle and Restore
; -------------------------------------------------------------------------------

M4_DCHG:                                ; prepare newly selected drive
        LD      A,(B_PDrive)
        LD      D,A
        LD      A,(M4R_DRIVE)
        CP      D
        LD      A,0
        JR      Z,M4_DCSTORE
        LD      A,D
        LD      (M4R_DRIVE),A
        LD      A,0FFH

M4_DCSTORE:                             ; save selected drive
        LD      (M4R_CHANGED),A
        RET

M4_DWAIT:                               ; wait for motor spin-up
        LD      A,(M4R_CHANGED)
        OR      A
        RET     Z
        PUSH    BC
        LD      B,2

M4_DWOUT:                               ; execute spin-up delay
        LD      DE,0

M4_DWIN:                                ; continue spin-up delay
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

M4_DWREST:                              ; restore selected drive
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4_DWRDONE
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4_DWREST

M4_DWRDONE:                             ; finish drive-change preparation
        XOR     A
        LD      (M4R_CHANGED),A
        RET
        ENDIF

  ; Write one complete 512-byte sector. Parameters and status match M4_READ.
        IF      M4_READ_ONLY EQ 0

; ================================================================================
; =                            Physical Sector Write                             =
; =                                                                              =
; = Writes one complete 512-byte Model 4 floppy sector using the same selection, =
; = seek, transfer, and status conventions as the physical read path.            =
; ================================================================================
; -------------------------------------------------------------------------------
; Write Setup and Drive Selection
; -------------------------------------------------------------------------------

M4_WRITE:                               ; write physical 512-byte sector
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

M4W_IDLE:                               ; wait for write controller idle
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4W_IDOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_IDLE
        JP      M4_TIMEOUT

M4W_IDOK:                               ; accept write idle state
        LD      A,(M4W_CYL)
        OUT     (FDCDATA),A
        LD      A,FDCSEEK
        OUT     (FDCCOMMAND),A
        LD      DE,0

; -------------------------------------------------------------------------------
; Write Seek
; -------------------------------------------------------------------------------

M4W_SEEK:                               ; seek for physical write
        IN      A,(FDCSTATUS)
        AND     1
        JR      Z,M4W_SKOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_SEEK
        JP      M4_TIMEOUT

M4W_SKOK:                               ; begin physical write command
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

M4W_DONE:                               ; finish physical write
        IN      A,(FDCSTATUS)
        BIT     0,A
        JR      Z,M4W_DNOK
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_DONE
        JP      M4_TIMEOUT

M4W_DNOK:                               ; return successful write
        AND     0FCH
        RET

M4W_256:                                ; select 256-byte transfer half
        LD      DE,0

; -------------------------------------------------------------------------------
; Write Data Transfer
; -------------------------------------------------------------------------------

M4W_DRQ:                                ; poll write data request
        IN      A,(FDCSTATUS)
        AND     2
        JR      NZ,M4W_BYTE
        DEC     DE
        LD      A,D
        OR      E
        JR      NZ,M4W_DRQ
        JP      M4_TIMEOUT

M4W_BYTE:                               ; output next write byte
        OUTI
        JR      NZ,M4W_256
        XOR     A
        RET

M4W_CYL:                                ; saved write cylinder
        DB      0

M4W_SEC:                                ; saved write sector
        DB      1
        ENDIF

M4_TIMEOUT:                             ; controller timeout constant
        LD      A,1
        OR      A
        RET
