; Per-operation user selection: never leave a caller in another user area.
; UC_BDOS owns register preservation; only its A/status result is significant.
SY_USER_BDOS:
        LD A,C
        CP 15
        JP C,5
        CP 24
        JP NC,5
        PUSH BC
        PUSH DE
        LD A,(SY_DSTUSER)
        LD HL,UC_INPUT
        OR A
        SBC HL,DE
        JR NZ,SY_USER_CHOSEN
        LD A,(SY_SRCUSER)
SY_USER_CHOSEN:
        LD E,A
        LD C,32
        CALL 5
        POP DE
        POP BC
        CALL 5
        PUSH AF
        LD A,(SY_OLDUSER)
        LD E,A
        LD C,32
        CALL 5
        POP AF
        RET

SY_PARSE:
        LD A,(80H)
        CP 128
        JP NC,UC_PARSE_BAD
        LD B,A
        LD HL,81H
        CALL UC_TOKEN
        JP C,UC_PARSE_BAD
        LD (SY_TAILPTR),HL
        LD C,A
        LD A,B
        LD (SY_TAILLEFT),A
        EX DE,HL
        LD B,C
        CALL SY_DU
        RET C
        LD A,(SY_DUDRIVE)
        LD (UC_DRIVE),A
        LD A,(SY_DUUSER)
        LD (SY_SRCUSER),A
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE
        POP BC
        POP HL
        RET C
        LD DE,UC_INPUT
        CALL UC_NAME_FCB
        RET C
        LD A,(UC_DRIVE)
        LD (UC_INPUT),A
        LD HL,(SY_TAILPTR)
        LD A,(SY_TAILLEFT)
        LD B,A
        CALL UC_TOKEN
        JR C,SY_PARSE_DONE
        LD (SY_TAILPTR),HL
        LD C,A
        LD A,B
        LD (SY_TAILLEFT),A
        EX DE,HL
        LD B,C
        CALL SY_DU
        RET C
        LD A,B
        OR A
        JP NZ,UC_PARSE_BAD
        LD A,(SY_DUDRIVE)
        LD (UC_DEST),A
        LD A,(SY_DUUSER)
        LD (SY_DSTUSER),A
        LD HL,(SY_TAILPTR)
        LD A,(SY_TAILLEFT)
        LD B,A
        CALL UC_TOKEN
        JP NC,UC_PARSE_BAD
SY_PARSE_DONE:
        OR A
        RET

; Bounded single-DU selection. Compound scopes are rejected before any I/O.
SY_DU:
        LD A,(SY_LOGDRIVE)
        DEC A
        LD D,A
        LD A,(SY_OLDUSER)
        LD E,A
        CALL DU_PARSE
        RET C
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JR C,SY_DU_BAD
        LD A,D
        INC A
        LD (SY_DUDRIVE),A
        LD A,E
        LD (SY_DUUSER),A
        CALL DU_NEXT
        JR NC,SY_DU_BAD
        POP BC
        POP HL
        OR A
        RET
SY_DU_BAD:
        POP BC
        POP HL
        SCF
        RET

        INCLUDE duselect.inc
        INCLUDE filespec.inc
