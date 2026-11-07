; Checked-loader ABI: DE=absolute package record, B=count, HL=destination.
; Records 0..7 live in the FM surface. Records 8..159 begin on cylinder 1.
; Read whole MFM sectors directly; unaligned/single records use deblocking.
        LD A,D
        OR A
        JP NZ,M2_RAW_BAD
        LD A,B
        OR A
        JP Z,M2_RAW_BAD
        ADD A,E
        JP C,M2_RAW_BAD
        CP 161
        JP NC,M2_RAW_BAD
M2_RAW_NEXT:
        PUSH BC
        PUSH DE
        LD A,E
        CP 8
        JR NC,M2_RAW_DATA
        CP 3
        JR NZ,M2_FMID
        LD E,12
M2_FMID:INC E
        LD D,0
        JR M2_RAW_ONE
M2_RAW_DATA:
        SUB 8
        LD C,A
        AND 3
        LD (M2_QUART),A
        LD A,C
        RRCA
        RRCA
        AND 03FH
        LD D,1
        CP 16
        JR C,M2_RAW_SECTOR
        INC D
        SUB 16
        CP 16
        JR C,M2_RAW_SECTOR
        INC D
        SUB 16
M2_RAW_SECTOR:
        INC A
        LD E,A
        LD A,(M2_QUART)
        OR A
        JR NZ,M2_RAW_PART
        LD A,B
        CP 4
        JR C,M2_RAW_PART
        LD C,080H
        XOR A
        CALL M2_XFER
        JR NZ,M2_RAW_EXIT
        POP DE
        POP BC
        INC E
        INC E
        INC E
        DEC B
        DEC B
        DEC B
        JR M2_RAW_ADV
M2_RAW_PART:
        PUSH HL
        LD HL,LY_BUF+512
        LD C,080H
        XOR A
        CALL M2_XFER
        POP DE
        JR NZ,M2_RAW_EXIT
        LD A,(M2_QUART)
        RRCA
        LD L,0
        RR L
        OR HIGH (LY_BUF+512)
        LD H,A
        LD BC,128
        LDIR
        EX DE,HL
        JR M2_POP
M2_RAW_ONE:
        LD C,080H
        XOR A
        CALL M2_XFER
        JR NZ,M2_RAW_EXIT
M2_POP:
        POP DE
        POP BC
M2_RAW_ADV:
        INC E
        DJNZ M2_RAW_NEXT
        XOR A
        RET
M2_RAW_EXIT:
        POP DE
        POP BC
        RET
M2_RAW_BAD:
        LD A,1
        OR A
        RET
M2_QUART: DB 0
