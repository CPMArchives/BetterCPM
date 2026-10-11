; ERA destructive-workflow raw-record adapter.
; Uses public CP/M BIOS vectors, not resident/private cache addresses.
; ER_OPEN: A=drive; success CF clear, private ER_DPB contains the DPB.
; ER_READ: HL=data-area-relative 128-byte record, DE=private buffer.
; Both preserve no caller registers. Unsupported geometry fails before I/O.
; Logical record addresses are bounded to 16 bits in this first adapter.
ER_OPEN:
        CP 4
        JR NC,ER_BAD
        LD (ER_DRIVE),A
        LD C,A
        LD E,0
        LD HL,(1)
        DEC HL
        DEC HL
        DEC HL
        LD (ER_BASE),HL
        LD A,27
        CALL ER_BCALL
        LD A,H
        OR L
        JR Z,ER_BAD
        LD DE,10
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD A,D
        OR E
        JR Z,ER_BAD
        EX DE,HL
        LD DE,ER_DPB
        LD BC,15
        LDIR
        LD HL,(ER_DPB)
        LD A,H
        OR L
        JR Z,ER_BAD
        ; Bound the absolute track sum, including the reserved-track offset.
        LD HL,0FFFFH
        CALL ER_DIV
        LD HL,(ER_DPB+13)
        ADD HL,BC
        JR C,ER_BAD
        OR A
        RET
ER_BAD:
        SCF
        RET
ER_READ:
        CALL ER_POS
        RET C
        LD A,39
        CALL ER_BCALL
        OR A
        RET Z
        SCF
        RET
; ER_WRITE: HL=record, DE=buffer, C=0 data/1 directory. Honor drive RO.
ER_WRITE:
        XOR A
        LD (ER_ATTEMPT),A
        LD (ER_WREC),HL
        LD (ER_DMA),DE
        LD A,C
        LD (ER_KIND),A
        CALL ER_PERMIT
        RET C
        LD HL,(ER_WREC)
        LD DE,(ER_DMA)
        CALL ER_POS
        RET C
        LD A,(ER_KIND)
        LD C,A
        LD A,1
        LD (ER_ATTEMPT),A
        LD A,42
        CALL ER_BCALL
        OR A
        RET Z
        SCF
        RET
ER_PERMIT:
        LD C,29
        CALL 5
        LD A,(ER_DRIVE)
        LD B,A
        INC B
        LD A,L
ER_ROTEST:
        RRCA
        DJNZ ER_ROTEST
        RET
ER_POS:
        LD (ER_DMA),DE
        CALL ER_DIV
        PUSH HL
        LD HL,(ER_DPB+13)
        ADD HL,BC
        JR C,ER_READBAD
        LD B,H
        LD C,L
        LD A,30
        CALL ER_BCALL
        POP BC
        LD DE,0
        LD A,48
        CALL ER_BCALL
        LD B,H
        LD C,L
        LD A,33
        CALL ER_BCALL
        LD BC,(ER_DMA)
        LD A,36
        CALL ER_BCALL
        OR A
        RET
ER_READBAD:
        POP HL
        SCF
        RET
 ; ER_SNAP: DE=private buffer, BC=capacity. Read the complete rounded directory
; before a destructive planner can consider data writes. Failure never writes
; to disk; caller must discard an incomplete snapshot. Success HL=buffer,
; BC=actual directory-entry count, ER_BYTES=rounded snapshot byte count.
ER_SNAP:
        LD (ER_CAP),BC
        LD (ER_PTR),DE
        LD (ER_START),DE
        LD HL,(ER_DPB+7)
        LD DE,4
        ADD HL,DE
        JP C,ER_BAD
        SRL H
        RR L
        SRL H
        RR L
        LD (ER_COUNT),HL
        LD B,7
ER_SIZE:
        ADD HL,HL
        JP C,ER_BAD
        DJNZ ER_SIZE
        LD (ER_BYTES),HL
        LD DE,(ER_CAP)
        OR A
        SBC HL,DE
        JR C,ER_FITS
        LD A,H
        OR L
        JP NZ,ER_BAD
ER_FITS:
        LD HL,(ER_BYTES)
        LD DE,(ER_START)
        ADD HL,DE
        JP C,ER_BAD
        LD HL,0
        LD (ER_RECORD),HL
ER_SLOOP:
        LD HL,(ER_RECORD)
        LD DE,(ER_PTR)
        CALL ER_READ
        RET C
        LD HL,(ER_PTR)
        LD DE,128
        ADD HL,DE
        JP C,ER_BAD
        LD (ER_PTR),HL
        LD HL,(ER_RECORD)
        INC HL
        LD (ER_RECORD),HL
        LD DE,(ER_COUNT)
        OR A
        SBC HL,DE
        JR NZ,ER_SLOOP
        LD HL,(ER_DPB+7)
        INC HL
        LD B,H
        LD C,L
        LD HL,(ER_START)
        OR A
        RET
; HL=relative record; return BC=track quotient, HL=logical sector remainder.
ER_DIV:
        LD DE,(ER_DPB)
        LD BC,0
ER_DIVLOOP:
        OR A
        SBC HL,DE
        JR C,ER_DIVDONE
        INC BC
        JR ER_DIVLOOP
ER_DIVDONE:
        ADD HL,DE
        RET
ER_BCALL:
        PUSH DE
        LD HL,(ER_BASE)
        LD E,A
        LD D,0
        ADD HL,DE
        POP DE
        JP (HL)
ER_ATTEMPT: DB 0
ER_WREC: DW 0
ER_KIND: DB 0
ER_BASE: DW 0
ER_DMA: DW 0
ER_DRIVE: DB 0
ER_CAP: DW 0
ER_PTR: DW 0
ER_START: DW 0
ER_COUNT: DW 0
ER_BYTES: DW 0
ER_RECORD: DW 0
ER_DPB: DS 15
