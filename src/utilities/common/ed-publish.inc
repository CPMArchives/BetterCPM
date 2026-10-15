; Publication primitives after EF_DRAIN. No command diagnostics or reboot.
; FP_COMMIT: close work, rename source->BAK, rename work->original.
; Carry A=255 on failed primitive, 254 if data is not finalized.
; FP_STEP records completed phases; caller must not retry a failed rename
; sequence blindly. Policy for failures belongs to the lifecycle owner.
FP_INIT:
        XOR A
        LD (FP_STEP),A
        LD (FP_USED),A
        RET
FP_COMMIT:
        LD A,(EF_DONE)
        OR A
        JP Z,FP_EARLY
        LD A,(FP_USED)
        OR A
        JP NZ,FP_EARLY
        INC A
        LD (FP_USED),A
        CALL FS_DEST
        XOR A
        LD (FS_WORK+13),A          ; stock CP/M reserved S1, not padding count
        LD DE,FS_WORK
        LD C,16
        CALL FS_CALL
        CP 255
        JP Z,FP_FAIL
        LD A,1
        LD (FP_STEP),A
        CALL FP_NAMES
        LD HL,EI_FCB
        LD DE,FP_RENAME
        LD BC,12
        LDIR
        LD HL,EI_FCB
        LD DE,FP_RENAME+16
        LD BC,12
        LDIR
        LD HL,FS_BEXT
        LD DE,FP_RENAME+25
        LD BC,3
        LDIR
        CALL FS_SRC
        LD A,(EI_SDRV)
        INC A
        LD (FP_RENAME),A
        LD (FP_RENAME+16),A
        LD DE,FP_RENAME
        LD C,23
        CALL FS_CALL
        CP 255
        JP Z,FP_FAIL
        LD A,2
        LD (FP_STEP),A
        CALL FP_NAMES
        LD HL,EI_FCB
        LD DE,FP_RENAME
        LD BC,12
        LDIR
        LD HL,EI_FCB
        LD DE,FP_RENAME+16
        LD BC,12
        LDIR
        LD HL,FS_TEXT
        LD DE,FP_RENAME+9
        LD BC,3
        LDIR
        CALL FS_DEST
        LD A,(EI_ODRV)
        INC A
        LD (FP_RENAME),A
        LD (FP_RENAME+16),A
        LD DE,FP_RENAME
        LD C,23
        CALL FS_CALL
        CP 255
        JP Z,FP_FAIL
        LD A,3
        LD (FP_STEP),A
        XOR A
        RET
FP_NAMES:
        LD HL,FP_RENAME
        LD DE,FP_RENAME+1
        LD BC,35
        LD (HL),0
        LDIR
        RET
FP_FAIL:
        SCF
        RET
FP_EARLY:
        LD A,254
        SCF
        RET
FP_STEP: DB 0
FP_USED: DB 0
FP_RENAME: DS 36
