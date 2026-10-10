; Shared resident COPY/MOVE source selection and preflight. The record engine
; remains common; only its existing MOVE flag controls source deletion.
BC_CPARSE:
        JR CM_PSTART
CM_DERROR:
        POP BC
        POP HL
        JP BC_CSYNT
CM_PSTART:
        LD A,(BC_CDSAV)
        LD D,A
        LD A,(BC_CUSAV)
        LD E,A
        LD HL,(BC_CDPTR)
        LD A,(BC_CDLEN)
        LD B,A
        PUSH DE
        CALL RF_TRIM
        POP DE
        CALL DU_PARSE
        JP C,BC_CSYNT
        LD A,B
        LD (CM_LEN),A
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JR C,CM_DERROR
        LD A,D
        CP 4
        JR NC,CM_DERROR
        LD (BC_CDDRV),A
        LD A,E
        LD (BC_CDUSR),A
        CALL DU_NEXT
        JR NC,CM_DERROR            ; destination must resolve to one DU
        POP BC
        POP HL
        LD A,B
        OR A
        JR Z,CM_EMPTY
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE          ; exact destination name, never a pattern
        POP BC
        POP HL
        JP C,BC_CSYNT
CM_EMPTY:
        LD DE,CM_TARGET
        CALL BC_PFCB
        LD A,(BC_CDSAV)
        LD D,A
        LD A,(BC_CUSAV)
        LD E,A
        LD HL,(BC_CSPTR)
        LD A,(BC_CSLEN)
        LD B,A
        PUSH DE
        CALL RF_TRIM
        POP DE
        LD A,B
        OR A
        JP Z,BC_CSYNT
        CALL FS_PARSE
        JP C,BC_CSYNT
        LD HL,DU_MAP+16
        LD B,48
CM_DOMAIN:
        LD A,(HL)
        OR A
        JP NZ,BC_BDERR
        INC HL
        DJNZ CM_DOMAIN
        XOR A
        LD (CM_PASS),A
        LD (CM_SEEN),A
CM_BEGIN:
        LD BC,0
        LD (RF_INDEX),BC
        LD A,(CM_LEN)
        OR A
        JR NZ,CM_SOURCE
        LD A,(CM_PASS)
        OR A
        JR Z,CM_SOURCE
        LD HL,BC_CDDRV
        LD A,D
        CP (HL)
        JR NZ,CM_SOURCE
        INC HL
        LD A,E
        CP (HL)
        JR Z,CM_DU                ; never discover new files in target DU
CM_SOURCE:
CM_DU:
        LD BC,(RF_INDEX)
        CALL DU_NEXT
        JP C,CM_END
        LD (RF_INDEX),BC
        LD A,D
        LD (RF_DRIVE),A
        LD A,E
        LD (RF_USER),A
        CALL RF_SELECT
        LD HL,RF_LAST
        LD B,11
        XOR A
CM_ZERO:
        LD (HL),A
        INC HL
        DJNZ CM_ZERO
CM_NEXT:
        CALL RF_SELECT
        CALL RF_FIND
        JR C,CM_DU
        LD HL,RF_BEST
        LD DE,RF_LAST
        LD BC,11
        LDIR
        LD A,(CM_PASS)
        OR A
        JP NZ,CM_COPY
        LD A,(CM_LEN)
        OR A
        JR Z,CM_COUNT
        LD A,(CM_SEEN)
        OR A
        JP NZ,BC_CSYNT            ; many sources require a DU-only target
CM_COUNT:
        LD A,1
        LD (CM_SEEN),A
        LD A,(BC_MVFLAG)
        OR A
        JR Z,CM_MAP
        LD A,(RF_ATTR)
        OR A
        JP NZ,BC_CRO              ; cannot erase a read-only MOVE source
CM_MAP:
        CALL CM_FCBS
        ; Refuse all source overlap, including exact self-copy.
        CALL CM_OVERLAP
        JP Z,BC_CEXIST
        LD A,(CM_LEN)
        OR A
        JR NZ,CM_DEST
        CALL CM_DUPLICATE
        JP Z,CM_CONFLICT
CM_DEST:
        CALL BC_CSELD
        LD DE,BC_NEWFCB
        LD C,15
        CALL BDOS
        CP 0FFH
        JP Z,CM_NEXT
        LD A,(BC_OVER)
        OR A
        JP Z,BC_CEXIST
        LD A,(BC_NEWFCB+9)
        AND 80H
        JP NZ,BC_CRO
        JP CM_NEXT
CM_COPY:
        CALL CM_FCBS
        XOR A
        LD (BC_WERROR),A
        LD (BC_CMADE),A
        INC A
        LD (BC_WACTIVE),A
        CALL BC_COPEN
        XOR A
        LD (BC_WACTIVE),A
        LD A,(BC_WERROR)
        OR A
        JR NZ,CM_END
        LD A,(CM_LEN)
        OR A
        JR NZ,CM_END              ; one preflight source, exactly one copy
        JP CM_NEXT
CM_END:
        LD A,(CM_PASS)
        OR A
        JP NZ,BC_COK
        LD A,(CM_SEEN)
        OR A
        JP Z,BC_CNOFILE
        LD (CM_PASS),A
        JP CM_BEGIN
CM_FCBS:
        LD HL,BC_FCB
        LD B,36
        XOR A
CM_FZERO:
        LD (HL),A
        INC HL
        DJNZ CM_FZERO
        LD HL,RF_BEST
        LD DE,BC_FCB+1
        LD BC,11
        LDIR
        LD HL,CM_TARGET
        LD DE,BC_NEWFCB
        LD BC,36
        LDIR
        LD A,(CM_LEN)
        OR A
        RET NZ
        LD HL,RF_BEST
        LD DE,BC_NEWFCB+1
        LD BC,11
        LDIR
        RET
; Search a selected source DU for a concrete name and evaluate its predicate.
; Input D/E=DU, HL=name. Return Z iff a selected source has this name.
CM_MEMBER:
        PUSH HL
        PUSH DE
        LD E,D
        LD C,14
        CALL BDOS
        POP DE
        LD C,32
        CALL BDOS
        CALL RF_FCB
        POP HL
        LD DE,RF_FILE+1
        LD BC,11
        LDIR
        LD DE,BC_DMA
        LD C,26
        CALL BDOS
        LD DE,RF_FILE
        LD C,17
        CALL BDOS
        CP 0FFH
        JR Z,CM_ABSENT
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,BC_DMA
        ADD HL,DE
        LD (BC_DIREP),HL
        CALL RD_FILTER
        JR NC,CM_ABSENT
        XOR A
        RET
CM_ABSENT:
        LD A,1
        OR A
        RET
; Is the destination DU in the source map, and target name selected there?
CM_OVERLAP:
        LD A,(BC_CDDRV)
        LD D,A
        LD A,(BC_CDUSR)
        LD E,A
        CALL CM_SELECTED
        RET NZ
        ; The target must also match the original source filename pattern.
        LD HL,FS_FCB+1
        LD DE,BC_NEWFCB+1
        LD B,11
CM_PATTERN:
        LD A,(HL)
        CP '?'
        JR Z,CM_PNEXT
        LD C,A
        LD A,(DE)
        CP C
        JR NZ,CM_ABSENT
CM_PNEXT:
        INC HL
        INC DE
        DJNZ CM_PATTERN
        LD A,(BC_CDDRV)
        LD D,A
        LD A,(BC_CDUSR)
        LD E,A
        LD HL,BC_NEWFCB+1
        JR CM_MEMBER
CM_SELECTED:
        LD A,D
        ADD A,A
        ADD A,A
        LD C,A
        LD A,E
        SRL A
        SRL A
        SRL A
        ADD A,C
        LD L,A
        LD H,0
        LD BC,DU_MAP
        ADD HL,BC
        LD A,E
        AND 7
        LD B,A
        INC B
        LD A,(HL)
CM_BIT:
        RRCA
        DJNZ CM_BIT
        JR NC,CM_ABSENT
        XOR A
        RET
; All generated names are the original names for a DU-only destination.
; A matching selected name in another source DU therefore collides.
CM_DUPLICATE:
        LD BC,0
CM_DLOOP:
        CALL DU_NEXT
        JR C,CM_ABSENT
        LD A,(RF_DRIVE)
        CP D
        JR NZ,CM_DCHECK
        LD A,(RF_USER)
        CP E
        JR Z,CM_DLOOP
CM_DCHECK:
        PUSH BC
        LD HL,RF_BEST
        CALL CM_MEMBER
        POP BC
        RET Z
        JR CM_DLOOP
CM_CONFLICT:
        LD DE,CM_MSG
        JP BC_CPRINT
CM_LEN: DB 0
CM_PASS: DB 0
CM_SEEN: DB 0
CM_TARGET: DS 36
CM_MSG: DB 13,10,'Destination mapping collision.',13,10,'$'
