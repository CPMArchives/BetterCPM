; Known DRI setup, stream and work-close UI. Carry A=1 means exit ready.
; Other rename failures are deliberately returned raw for later qualification.
FD_BEGIN:
        CALL FS_SETUP
        JP C,FD_SETUPERR
FD_NOTES:
        LD A,(FS_NEW)
        OR A
        JP Z,FD_RO
        LD DE,FD_NEW
        CALL FD_PRINT
FD_RO:
        LD A,(FS_RO)
        OR A
        JP Z,FD_OK
        LD DE,FD_READONLY
        CALL FD_PRINT
FD_OK:
        XOR A
        RET
FD_ACT:
        CALL FQ_ACT
        JP C,FD_ACTIONERR
        OR A
        RET NZ
        JP FD_NOTES
FD_ACTIONERR:
        PUSH AF
        LD A,(FQ_STAGE)
        CP 2
        JP Z,FD_SETERR
        CP 1
        JP Z,FD_RAW
        POP AF
        JP FD_FATAL
FD_SETERR:
        POP AF
        JP FD_SETUPERR
FD_RAW:
        POP AF
        PUSH AF
        LD A,(FP_STEP)
        OR A
        JP NZ,FD_RENAME
        POP AF
        JP FD_FATAL              ; DRI FINIS calls FERR when work close fails
FD_RENAME:
        LD A,(FS_RO)
        OR A
        JP Z,FD_UNHANDLED
        LD A,(FP_STEP)
        CP 1
        JP NZ,FD_UNHANDLED
        POP AF
        JP FD_ROFAIL
FD_UNHANDLED:
        POP AF
        RET
FD_SETUPERR:
        CP 1
        JP Z,FD_CLASH
        CP 2
        JP Z,FD_SYSTEM
FD_FATAL:
        LD (FD_STATUS),A
        CALL FS_DEST
        LD DE,FS_WORK
        LD C,16
        CALL FS_CALL              ; DRI FERR: attempt close, even if it fails
        LD DE,FD_DISK
        JP FD_ABORT
FD_CLASH:
        LD DE,FD_EXISTS
        JP FD_ABORT
FD_SYSTEM:
        LD DE,FD_SYS
FD_ABORT:
        CALL FD_PRINT
FD_EXIT:
        LD A,(EI_CDRV)
        LD (FQ_DRIVE),A
        LD A,(EI_CUSR)
        CALL FQ_LEAVE
        LD A,1
        SCF
        RET
FD_ROFAIL:
        LD DE,FD_BDOS
        CALL FD_PRINT
        LD A,(EI_SDRV)
        ADD A,'A'
        LD E,A
        LD C,2
        CALL 5
        LD DE,FD_FILE_RO
        CALL FD_PRINT
        LD C,1
        CALL 5
        LD DE,FD_NEWLINE
        CALL FD_PRINT
        JP FD_EXIT
FD_PRINT:
        LD C,9
        JP 5
FD_NEW: DB 'NEW FILE',13,10,'$'
FD_READONLY: DB '** FILE IS READ/ONLY **',13,10,'$'
FD_EXISTS: DB 'FILE EXISTS, ERASE IT',13,10,'$'
FD_SYS: DB '"SYSTEM" FILE NOT ACCESSIBLE',13,10,'$'
FD_DISK: DB 'DISK OR DIRECTORY FULL',13,10,'$'
FD_STATUS: DB 0
FD_BDOS: DB 13,10,'Bdos Err On $'
FD_FILE_RO: DB ': File R/O$'
FD_NEWLINE: DB 13,10,'$'
