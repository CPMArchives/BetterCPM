; File setup after EI_PARSE. No prompt/output: caller owns diagnostics/exit.
; Carry A=1 destination collision, 2 system source, 3 storage failure.
; FS_NEW/FS_RO inform caller; FS_STATUS retains the last raw BDOS result.
; DRI order is intentional: collision first, source open/create, delete old
; backups, delete stale work, create work. No close or rename in this stage.
FS_SETUP:
        XOR A
        LD (FS_NEW),A
        LD (FS_RO),A
        LD DE,ES_DATA
        LD C,26
        CALL 5
        LD HL,EI_FCB
        LD DE,FS_SOURCE
        LD BC,36
        LDIR
        LD HL,EI_FCB
        LD DE,FS_WORK
        LD BC,36
        LDIR
        LD A,(EI_SDRV)
        INC A
        LD (FS_SOURCE),A
        LD A,(EI_ODRV)
        INC A
        LD (FS_WORK),A
        LD A,(EI_SDRV)
        LD B,A
        LD A,(EI_ODRV)
        CP B
        JP NZ,FS_CHECK
        LD A,(EI_SUSR)
        LD B,A
        LD A,(EI_OUSR)
        CP B
        JP Z,FS_OPEN
FS_CHECK:
        CALL FS_DEST
        LD DE,FS_WORK
        LD C,17
        CALL FS_CALL
        CP 255
        JP NZ,FS_CLASH
FS_OPEN:
        CALL FS_SRC
        LD DE,FS_SOURCE
        LD C,15
        CALL FS_CALL
        CP 255
        JP NZ,FS_ATTR
        LD DE,FS_SOURCE
        LD C,22
        CALL FS_CALL
        CP 255
        JP Z,FS_DISK
        LD A,1
        LD (FS_NEW),A
        JP FS_BAK
FS_ATTR:
        LD A,(FS_SOURCE+9)
        AND 128
        LD (FS_RO),A
        JP NZ,FS_BAK              ; DRI reports RO before checking SYS
        LD A,(FS_SOURCE+10)
        AND 128
        JP NZ,FS_SYSTEM
FS_BAK:
        LD HL,FS_BEXT
        CALL FS_TYPE
        CALL FS_SRC
        LD A,(EI_SDRV)
        INC A
        LD (FS_WORK),A
        LD DE,FS_WORK
        LD C,19
        CALL FS_CALL              ; absent backup is harmless
        LD A,(EI_SDRV)
        LD B,A
        LD A,(EI_ODRV)
        CP B
        JP NZ,FS_DBK
        LD A,(EI_SUSR)
        LD B,A
        LD A,(EI_OUSR)
        CP B
        JP Z,FS_TEMP
FS_DBK:
        CALL FS_DEST
        LD A,(EI_ODRV)
        INC A
        LD (FS_WORK),A
        LD DE,FS_WORK
        LD C,19
        CALL FS_CALL
FS_TEMP:
        CALL FS_DEST
        LD A,(EI_ODRV)
        INC A
        LD (FS_WORK),A
        LD HL,FS_TEXT
        CALL FS_TYPE
        LD DE,FS_WORK
        LD C,19
        CALL FS_CALL
        LD DE,FS_WORK
        LD C,22
        CALL FS_CALL
        CP 255
        JP Z,FS_DISK
        LD HL,FS_SOURCE
        LD A,(EI_SUSR)
        CALL ES_INIT
        LD HL,FS_WORK
        LD A,(EI_OUSR)
        CALL EW_INIT
        CALL EF_INIT
        CALL FP_INIT
        XOR A
        RET
FS_SRC:
        LD A,(EI_SDRV)
        LD E,A
        LD C,14
        CALL 5
        LD A,(EI_SUSR)
        LD E,A
        LD C,32
        JP 5
FS_DEST:
        LD A,(EI_ODRV)
        LD E,A
        LD C,14
        CALL 5
        LD A,(EI_OUSR)
        LD E,A
        LD C,32
        JP 5
FS_CALL:
        CALL 5
        LD (FS_STATUS),A
        RET
FS_TYPE:
        LD DE,FS_WORK+9
        LD BC,3
        LDIR
        RET
FS_CLASH:
        LD A,1
        SCF
        RET
FS_SYSTEM:
        LD A,2
        SCF
        RET
FS_DISK:
        LD A,3
        SCF
        RET
FS_BEXT: DB 'BAK'
FS_TEXT: DB '$$$'
FS_NEW: DB 0
FS_RO: DB 0
FS_STATUS: DB 0
FS_SOURCE: DS 36
FS_WORK: DS 36
