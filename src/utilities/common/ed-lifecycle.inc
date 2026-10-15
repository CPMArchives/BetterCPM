; Authorized E/H/O/Q requests from EU_READ. No added confirmation here.
; Carry=raw/category error; clear A=0 restart, A=1 exit requested.
; Exit selects full BDOS DU, restores DMA and updates the legacy CCP boot byte.
FQ_ACT:
        LD (FQ_CMD),A
        XOR A
        LD (FQ_STAGE),A
        LD A,(FQ_CMD)
        CP 'Q'
        JP Z,FQ_QUIT
        CP 'O'
        JP Z,FQ_REOPEN
        CP 'E'
        JP Z,FQ_SAVE
        CP 'H'
        JP NZ,EC_BAD
FQ_SAVE:
        LD (FQ_CMD),A
        CALL EF_DRAIN
        RET C
        LD A,1
        LD (FQ_STAGE),A
        CALL FP_COMMIT
        RET C
        LD A,(FQ_CMD)
        CP 'H'
        JP Z,FQ_SWAP
        LD A,(EI_ODRV)
        LD (FQ_DRIVE),A
        LD A,(EI_OUSR)
        JP FQ_LEAVE
FQ_SWAP:
        LD A,(EI_SDRV)
        LD B,A
        LD A,(EI_ODRV)
        LD (EI_SDRV),A
        LD A,B
        LD (EI_ODRV),A
        LD A,(EI_SUSR)
        LD B,A
        LD A,(EI_OUSR)
        LD (EI_SUSR),A
        LD A,B
        LD (EI_OUSR),A
FQ_REOPEN:
        LD A,2
        LD (FQ_STAGE),A
        CALL FS_SETUP
        RET C
        LD HL,(EB_FIRST)
        LD DE,(EB_LIMIT)
        CALL EB_INIT
        RET C
        XOR A
        LD (ET_COL),A
        LD (ET_MUTE),A
        RET
FQ_QUIT:
        CALL FS_DEST
        LD DE,FS_WORK
        LD C,19
        CALL FS_CALL              ; historical Q does not inspect delete status
        LD A,(EI_CDRV)
        LD (FQ_DRIVE),A
        LD A,(EI_CUSR)
FQ_LEAVE:
        LD (FQ_USER),A
        AND 15
        RLCA
        RLCA
        RLCA
        RLCA
        LD B,A
        LD A,(FQ_DRIVE)
        OR B
        LD (0004H),A              ; stock CCP consumes packed user/drive
        LD A,(FQ_DRIVE)
        LD E,A
        LD C,14
        CALL 5
        LD A,(FQ_USER)            ; BetterCP/M keeps the full 0..31 user here
        LD E,A
        LD C,32
        CALL 5
        LD DE,80H
        LD C,26
        CALL 5
        LD A,1
        OR A
        RET
FQ_CMD: DB 0
FQ_DRIVE: DB 0
FQ_USER: DB 0
FQ_STAGE: DB 0
