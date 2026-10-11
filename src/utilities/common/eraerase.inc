; Destructive ERA transaction. Owns no resident memory; links only into ERA.COM.
; ED_STAGE: 0 no plan, 1 data overwrite, 2 directory scrub, 3 completed.
; Retry retains snapshot, block ownership and scrub progress. Skip/Abort must
; call ED_CLEAN before any BDOS file operation after directory mutation.
ED_BEGIN:
        LD IX,(E_CURRENT)
        LD A,(IX+0)
        CALL ER_OPEN
        RET C
        CALL ER_PERMIT
        RET C
        LD HL,(E_LIMIT)
        LD DE,(E_NEXT)
        OR A
        SBC HL,DE
        RET C
        LD B,H
        LD C,L
        LD DE,(E_NEXT)
        CALL ER_SNAP
        RET C
        ; Planner workspace follows the immutable directory snapshot.
        LD HL,(E_NEXT)
        LD DE,(ER_BYTES)
        ADD HL,DE
        PUSH HL
        POP IX
        LD HL,(E_LIMIT)
        LD (EG_LIMIT),HL
        LD HL,(E_CURRENT)
        INC HL
        EX DE,HL
        LD HL,(E_NEXT)
        ; Entry count comes from the DPB, not stale planner state.
        LD BC,(ER_DPB+7)
        INC BC
        CALL EG_PLAN
        RET C
        LD A,1
        LD (ED_STAGE),A
ED_DATA:
        ; Always retry data from the preserved plan. Metadata is still intact.
        LD HL,0
        LD (ED_BLOCK),HL
ED_BLOOP:
        CALL E_ABORTKEY
        JP C,E_CANCEL
        LD HL,(EG_MAP)
        LD DE,(ED_BLOCK)
        ADD HL,DE
        LD A,(HL)
        AND 3
        CP 1
        JR NZ,ED_NEXTBL
        LD HL,(ED_BLOCK)
        LD A,(ER_DPB+2)
        LD B,A
ED_BLREC:
        ADD HL,HL
        DJNZ ED_BLREC
        LD (ED_RECORD),HL
        LD A,(ER_DPB+3)
        INC A
        LD (ED_REMAIN),A
ED_ZEROLOOP:
        CALL E_ABORTKEY
        JP C,E_CANCEL
        LD HL,(ED_RECORD)
        LD DE,ED_ZERO
        LD C,0
        CALL ER_WRITE
        RET C
        LD HL,(ED_RECORD)
        INC HL
        LD (ED_RECORD),HL
        LD A,(ED_REMAIN)
        DEC A
        LD (ED_REMAIN),A
        JR NZ,ED_ZEROLOOP
ED_NEXTBL:
        LD HL,(ED_BLOCK)
        INC HL
        LD (ED_BLOCK),HL
        LD DE,(EG_NBLK)
        OR A
        SBC HL,DE
        JR NZ,ED_BLOOP
        LD A,2
        LD (ED_STAGE),A
        LD HL,0
        LD (ED_SREC),HL
ED_SCRUB:
        CALL E_ABORTKEY
        JP C,E_CANCEL
        LD HL,(ED_SREC)
        LD B,7
ED_SOFFSET:
        ADD HL,HL
        DJNZ ED_SOFFSET
        LD DE,(E_NEXT)
        ADD HL,DE
        LD (ED_ORIGINAL),HL
        LD DE,ED_PROPOSED
        LD BC,128
        LDIR
        LD HL,(ED_SREC)
        ADD HL,HL
        ADD HL,HL
        LD DE,(EG_MARK)
        ADD HL,DE
        LD (ED_MARKPTR),HL
        LD HL,ED_PROPOSED
        LD (ED_ENTRY),HL
        XOR A
        LD (ED_TOUCH),A
        LD A,4
        LD (ED_NENTRY),A
ED_PREP:
        LD HL,(ED_MARKPTR)
        LD A,(HL)
        OR A
        JR Z,ED_ENEXT
        LD A,1
        LD (ED_TOUCH),A
        LD HL,(ED_ENTRY)
        LD (HL),0E5H
        INC HL
        LD B,31
        XOR A
ED_SZERO:
        LD (HL),A
        INC HL
        DJNZ ED_SZERO
ED_ENEXT:
        LD HL,(ED_MARKPTR)
        INC HL
        LD (ED_MARKPTR),HL
        LD HL,(ED_ENTRY)
        LD DE,32
        ADD HL,DE
        LD (ED_ENTRY),HL
        LD A,(ED_NENTRY)
        DEC A
        LD (ED_NENTRY),A
        JR NZ,ED_PREP
        LD A,(ED_TOUCH)
        OR A
        JP Z,ED_SNEXT
        LD HL,(ED_SREC)
        LD DE,ED_ACTUAL
        CALL ER_READ
        RET C
        ; A retry may see old or already-scrubbed target bytes after a failed
        ; write. Unselected bytes must still equal the original snapshot.
        LD HL,(ED_ORIGINAL)
        LD DE,ED_PROPOSED
        LD IX,ED_ACTUAL
        LD B,128
ED_COMPARE:
        LD A,(IX+0)
        CP (HL)
        JR Z,ED_EQUAL
        LD C,A
        LD A,(DE)
        CP C
        JR NZ,ED_CHANGED
ED_EQUAL:
        INC HL
        INC DE
        INC IX
        DJNZ ED_COMPARE
        LD HL,(ED_SREC)
        LD DE,ED_PROPOSED
        LD C,1
        CALL ER_WRITE
        PUSH AF
        LD A,(ER_ATTEMPT)
        OR A
        JR Z,ED_NOWRITE
        LD A,1
        LD (ED_DIRTY),A
ED_NOWRITE:
        POP AF
        RET C
ED_SNEXT:
        LD HL,(ED_SREC)
        INC HL
        LD (ED_SREC),HL
        LD DE,(ER_COUNT)
        OR A
        SBC HL,DE
        JP NZ,ED_SCRUB
        CALL ED_RELOG
        LD A,3
        LD (ED_STAGE),A
        OR A
        RET
ED_CHANGED:
        SCF
        RET
ED_RETRY:
        LD A,(ED_STAGE)
        CP 2
        JP Z,ED_SCRUB
        JP ED_DATA
ED_RELOG:
        LD A,(ED_DIRTY)
        OR A
        RET Z
        LD A,(ER_DRIVE)
        LD B,A
        LD DE,1
        LD A,B
        OR A
        JR Z,ED_RESET
ED_SHMASK:
        SLA E
        RL D
        DJNZ ED_SHMASK
ED_RESET:
        LD C,37
        CALL 5
        XOR A
        LD (ED_DIRTY),A
        JP E_SELECT
ED_CLEAN:
        LD A,(ED_STAGE)
        CP 2
        RET NZ
        CALL E_FULL
        LD DE,ED_INCOMP
        CALL E_PRINT
        JP ED_RELOG
ED_SUCCESS:
        LD HL,(EG_SHARED)
        LD A,H
        OR L
        LD HL,E_DERASE
        JR Z,ED_DCOUNT
        LD HL,E_SHARED
        CALL E_INC
        CALL E_FULL
        LD DE,ED_SHAREMSG
        CALL E_PRINT
        JR ED_FREED
ED_DCOUNT:
        CALL E_INC
ED_FREED:
        LD HL,(EG_UNIQUE)
        LD A,(ER_DPB+2)
        LD B,A
ED_RCOUNT:
        ADD HL,HL
        DJNZ ED_RCOUNT
        LD (ED_FREEREC),HL
        LD HL,ED_FREEREC
        LD DE,E_FREED
        CALL E_ADD4
        JP E_ADVANCE
ED_STAGE: DB 0
ED_DIRTY: DB 0
ED_BLOCK: DW 0
ED_RECORD: DW 0
ED_REMAIN: DB 0
ED_SREC: DW 0
ED_ORIGINAL: DW 0
ED_MARKPTR: DW 0
ED_ENTRY: DW 0
ED_TOUCH: DB 0
ED_NENTRY: DB 0
ED_FREEREC: DB 0,0,0,0
ED_INCOMP: DB ' - Incomplete destructive erase.',13,10,'$'
ED_SHAREMSG: DB ' - erased; shared blocks retained',13,10,'$'
ED_ACTUAL: DS 128
ED_PROPOSED: DS 128
ED_ZERO: DB 0
        REPT 127
        DB 0
        ENDM
