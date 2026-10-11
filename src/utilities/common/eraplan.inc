; Destructive ERA allocation planner. Pure: no BIOS/BDOS calls or disk writes.
; Requires ER_DPB from eraraw.inc and a complete immutable directory snapshot.
; EG_PLAN: HL=snapshot, BC=entry count, DE=user + normalized 11-byte name,
; IX=workspace, EG_LIMIT=exclusive upper bound of workspace.
; Success CF clear. EG_MAP has DSM+1 ownership bytes: 1 target, 2 other file,
; 4 reserved. EG_MARK has one byte per directory entry: 1 target, 0 other.
; EG_UNIQUE/EG_SHARED count distinct target blocks. Preserve shared blocks.
; Failure CF set, EG_ERROR=1 geometry/capacity, 2 corrupt map, 3 no target.
; A failed output is not an executable plan. Input snapshot is never modified.
EG_PLAN:
        LD (EG_DIR),HL
        LD (EG_NENT),BC
        LD (EG_IDENT),DE
        LD (EG_MAP),IX
        XOR A
        LD (EG_ERROR),A
        LD HL,0
        LD (EG_FOUND),HL
        LD (EG_UNIQUE),HL
        LD (EG_SHARED),HL
        LD HL,(ER_DPB+7)
        INC HL
        OR A
        SBC HL,BC
        JP NZ,EG_BADG
        LD A,(ER_DPB+2)
        CP 3
        JP C,EG_BADG
        CP 8
        JP NC,EG_BADG
        LD B,A
        LD HL,0FFFFH
EG_BOUND:
        SRL H
        RR L
        DJNZ EG_BOUND
        LD DE,(ER_DPB+5)
        OR A
        SBC HL,DE
        JP C,EG_BADG
        ; Check BLM equals 2^BSH-1 and compute directory block reservation.
        LD A,(ER_DPB+2)
        LD B,A
        LD A,1
EG_BLM:
        ADD A,A
        DJNZ EG_BLM
        DEC A
        LD C,A
        LD A,(ER_DPB+3)
        CP C
        JP NZ,EG_BADG
        LD HL,(ER_DPB+7)
        LD DE,4
        ADD HL,DE
        JP C,EG_BADG
        SRL H
        RR L
        SRL H
        RR L
        LD E,C
        LD D,0
        ADD HL,DE
        JP C,EG_BADG
        LD A,(ER_DPB+2)
        LD B,A
EG_RSHIFT:
        SRL H
        RR L
        DJNZ EG_RSHIFT
        LD (EG_RSV),HL
        LD HL,(ER_DPB+5)
        INC HL
        LD (EG_NBLK),HL
        LD DE,(EG_RSV)
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JP C,EG_BADG
        PUSH IX
        POP DE
        ADD HL,DE
        JP C,EG_BADG
        LD (EG_MARK),HL
        LD DE,(EG_NENT)
        ADD HL,DE
        JP C,EG_BADG
        LD (EG_END),HL
        LD DE,(EG_LIMIT)
        OR A
        SBC HL,DE
        JR C,EG_FIT
        LD A,H
        OR L
        JP NZ,EG_BADG
EG_FIT:
        LD HL,(EG_MAP)
        LD DE,(EG_END)
EG_CLEAR:
        XOR A
        LD (HL),A
        INC HL
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JR NZ,EG_CLEAR
        ; Reserve contiguous directory blocks, independent of AL0/AL1.
        LD HL,(EG_MAP)
        LD BC,(EG_RSV)
EG_RESERVE:
        LD A,B
        OR C
        JR Z,EG_ALMAP
        LD (HL),4
        INC HL
        DEC BC
        JR EG_RESERVE
EG_ALMAP:
        LD HL,(EG_MAP)
        LD DE,(EG_NBLK)
        LD A,(ER_DPB+9)
        LD C,A
        LD A,(ER_DPB+10)
        LD B,A
        LD A,16
        LD (EG_BITS),A
EG_ALBIT:
        LD A,D
        OR E
        JR Z,EG_BEGIN
        SLA B
        RL C
        JR NC,EG_ALNEXT
        LD (HL),4
EG_ALNEXT:
        INC HL
        DEC DE
        LD A,(EG_BITS)
        DEC A
        LD (EG_BITS),A
        JR NZ,EG_ALBIT
EG_BEGIN:
        LD HL,(EG_DIR)
        LD (EG_ENTRY),HL
        LD HL,(EG_MARK)
        LD (EG_FLAG),HL
        LD HL,(EG_NENT)
        LD (EG_LEFT),HL
EG_SCAN:
        LD HL,(EG_ENTRY)
        LD A,(HL)
        CP 32
        JP NC,EG_NEXT
        CALL EG_MATCH
        LD A,2
        JR NZ,EG_OTHER
        LD A,1
        LD HL,(EG_FOUND)
        INC HL
        LD (EG_FOUND),HL
        LD HL,(EG_FLAG)
        LD (HL),1
EG_OTHER:
        LD (EG_OWNER),A
        LD HL,(EG_ENTRY)
        LD DE,16
        ADD HL,DE
        LD (EG_APTR),HL
        LD HL,(ER_DPB+5)
        LD A,H
        OR A
        LD A,16
        JR Z,EG_SLOTS
        LD A,8
EG_SLOTS:
        LD (EG_NSLOT),A
EG_POINTER:
        LD HL,(EG_APTR)
        LD E,(HL)
        INC HL
        LD D,0
        LD A,(ER_DPB+6)
        OR A
        JR Z,EG_BYTE
        LD D,(HL)
        INC HL
EG_BYTE:
        LD (EG_APTR),HL
        LD A,D
        OR E
        JR Z,EG_PNEXT
        PUSH DE
        LD HL,(ER_DPB+5)
        OR A
        SBC HL,DE
        POP DE
        JP C,EG_BADM
        LD HL,(EG_MAP)
        ADD HL,DE
        LD A,(HL)
        AND 4
        JP NZ,EG_BADM
        LD A,(EG_OWNER)
        LD C,A
        CP 1
        JR NZ,EG_SET
        LD A,(HL)
        AND 1
        JP NZ,EG_BADM
EG_SET:
        LD A,(HL)
        OR C
        LD (HL),A
EG_PNEXT:
        LD A,(EG_NSLOT)
        DEC A
        LD (EG_NSLOT),A
        JR NZ,EG_POINTER
EG_NEXT:
        LD HL,(EG_ENTRY)
        LD DE,32
        ADD HL,DE
        LD (EG_ENTRY),HL
        LD HL,(EG_FLAG)
        INC HL
        LD (EG_FLAG),HL
        LD HL,(EG_LEFT)
        DEC HL
        LD (EG_LEFT),HL
        LD A,H
        OR L
        JP NZ,EG_SCAN
        LD HL,(EG_FOUND)
        LD A,H
        OR L
        JP Z,EG_MISSING
        LD HL,(EG_MAP)
        LD BC,(EG_NBLK)
EG_COUNT:
        LD A,(HL)
        AND 3
        CP 1
        JR NZ,EG_CSHARE
        LD DE,(EG_UNIQUE)
        INC DE
        LD (EG_UNIQUE),DE
        JR EG_CNEXT
EG_CSHARE:
        CP 3
        JR NZ,EG_CNEXT
        LD DE,(EG_SHARED)
        INC DE
        LD (EG_SHARED),DE
EG_CNEXT:
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,EG_COUNT
        OR A
        RET
; Z only if entry user and all normalized filename bytes match the identity.
EG_MATCH:
        LD HL,(EG_ENTRY)
        LD DE,(EG_IDENT)
        LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        LD B,11
EG_NAME:
        LD A,(HL)
        AND 7FH
        LD C,A
        LD A,(DE)
        CP C
        RET NZ
        INC HL
        INC DE
        DJNZ EG_NAME
        XOR A
        RET
EG_BADG:
        LD A,1
        JR EG_FAIL
EG_BADM:
        LD A,2
        JR EG_FAIL
EG_MISSING:
        LD A,3
EG_FAIL:
        LD (EG_ERROR),A
        SCF
        RET
EG_DIR: DW 0
EG_NENT: DW 0
EG_IDENT: DW 0
EG_MAP: DW 0
EG_MARK: DW 0
EG_LIMIT: DW 0
EG_END: DW 0
EG_RSV: DW 0
EG_NBLK: DW 0
EG_ENTRY: DW 0
EG_FLAG: DW 0
EG_LEFT: DW 0
EG_APTR: DW 0
EG_FOUND: DW 0
EG_UNIQUE: DW 0
EG_SHARED: DW 0
EG_OWNER: DB 0
EG_NSLOT: DB 0
EG_BITS: DB 0
EG_ERROR: DB 0
