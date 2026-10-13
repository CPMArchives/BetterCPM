; Exact disk/device concatenation, sharing the staging transaction with fast copies.
; All operand kinds/options and staging aliases are checked before transfer I/O.
PC_CHECK:
        LD A,(PP_COUNT)
        DEC A
        LD (PC_LEFT),A
        LD HL,OP_DATA+80
        LD (PC_PTR),HL
        XOR A
        LD (PC_OPOS),A
PC_CLOOP:
        LD HL,(PC_PTR)
        LD A,(HL)
        CP 4
        JR Z,PC_CDEVICE
        CP 2
        JP NZ,PC_BAD
        INC HL
        INC HL
        LD A,(HL)
        CP 4
        JP NC,PC_DRIVE
        INC HL
        INC HL
        LD A,(HL)
        OR A
        JP NZ,PC_BAD
        JR PC_CPARAM
PC_CDEVICE:
        INC HL
        LD A,(HL)
        CALL PI_VALID
        JP C,PC_DEVICE
PC_CPARAM:
        LD HL,(PC_PTR)
        LD DE,44
        ADD HL,DE
        LD B,26
        LD C,0
PC_COPT:
        LD A,(HL)
        OR A
        JR Z,PC_CSKIP
        LD A,C
        CP 1
        JR Z,PC_CSKIP
        CP 7
        JR Z,PC_CSKIP
        CP 8
        JR Z,PC_CSKIP
        CP 4
        JR Z,PC_CSKIP
        CP 13
        JR Z,PC_CSKIP
        CP 15
        JR Z,PC_CSKIP
        CP 3
        JR Z,PC_CSKIP
        CP 5
        JR Z,PC_CSKIP
        CP 19
        JR Z,PC_CSKIP
        CP 16
        JR Z,PC_CSKIP
        CP 18
        JR Z,PC_CSKIP
        CP 11
        JR Z,PC_CSKIP
        CP 20
        JR Z,PC_CSKIP
        CP 25
        JR Z,PC_CSKIP
        PUSH HL
        LD HL,(PC_PTR)
        LD A,(HL)
        POP HL
        CP 4
        JR Z,PC_CDEVOPT
        LD A,C
        CP 6
        JR Z,PC_CSKIP
        CP 14
        JR Z,PC_CSKIP
        CP 17
        JR Z,PC_CSKIP
PC_CDEVOPT:
        LD A,(PD_ACTIVE)
        OR A
        JP NZ,PC_BAD
        LD A,C
        CP 21
        JR Z,PC_CSKIP
        CP 22
        JP NZ,PC_BAD
PC_CSKIP:
        INC HL
        INC C
        DJNZ PC_COPT
        CALL PE_VALID
        JP C,PC_BAD
        LD HL,(PC_PTR)
        LD A,(HL)
        CP 4
        JR Z,PC_CNEXT
        INC HL
        INC HL
        LD A,(PD_ACTIVE)
        OR A
        JR NZ,PC_CNEXT
        LD A,(OP_DATA+2)
        CP (HL)
        JR NZ,PC_CNEXT
        INC HL
        LD A,(OP_DATA+3)
        CP (HL)
        JR NZ,PC_CNEXT
        LD HL,(PC_PTR)
        LD DE,9
        ADD HL,DE
        LD DE,PT_DFCB+1
        CALL PT_EQUAL
        JP Z,PC_IDENT
        LD HL,(PC_PTR)
        LD DE,9
        ADD HL,DE
        LD DE,PT_TFCB+1
        CALL PT_EQUAL
        JP Z,PC_IDENT
PC_CNEXT:
        LD HL,(PC_PTR)
        LD DE,80
        ADD HL,DE
        LD (PC_PTR),HL
        LD HL,PC_LEFT
        DEC (HL)
        JP NZ,PC_CLOOP
        LD A,(PP_COUNT)
        DEC A
        LD (PC_LEFT),A
        LD HL,OP_DATA+80
        LD (PC_PTR),HL
        XOR A
        RET
PC_BAD:
        LD A,1
        RET
PC_IDENT:
        LD A,2
        RET
PC_DEVICE:
        LD A,4
        RET
PC_DRIVE:
        LD A,3
        RET
PC_BEGIN:
        CALL PE_INIT
        XOR A
        LD (PC_BINARY),A
        LD A,(OP_DATA+138)
        OR A
        JR NZ,PC_BIN
        LD HL,PT_SFCB+9
        LD A,(HL)
        AND 7FH
        CP 'C'
        JR NZ,PC_TEXT
        INC HL
        LD A,(HL)
        AND 7FH
        CP 'O'
        JR NZ,PC_TEXT
        INC HL
        LD A,(HL)
        AND 7FH
        CP 'M'
        JR NZ,PC_TEXT
PC_BIN:
        LD A,1
        LD (PC_BINARY),A
PC_TEXT:
PC_READ:
        CALL PT_SOURCE
        LD DE,PC_INPUT
        LD C,26
        CALL 5
        LD DE,PT_SFCB
        LD C,20
        CALL 5
        CP 1
        JP Z,PC_NEXT
        OR A
        JP NZ,PT_READERR
        XOR A
        LD (PC_IPOS),A
PC_CHAR:
        LD A,(PC_IPOS)
        LD E,A
        LD D,0
        LD HL,PC_INPUT
        ADD HL,DE
        LD A,(HL)
        CALL PX_CHAR
        LD (PC_CHARV),A
        LD A,(PC_BINARY)
        OR A
        JR NZ,PC_PUT
        LD A,(PC_CHARV)
        CP 01AH
        JP Z,PC_NEXT
PC_PUT:
        LD A,(PC_CHARV)
        CALL PE_FEED
        OR A
        JP NZ,PT_WFAIL
        LD A,(PE_DONE)
        OR A
        JP NZ,PC_NEXT
        LD HL,PC_IPOS
        INC (HL)
PC_CONT:
        LD A,(PC_IPOS)
        CP 128
        JP Z,PC_READ
        JR PC_CHAR
PC_NEXT:
        CALL HH_EOF
        OR A
        JP NZ,PT_WFAIL
        CALL PE_CHECK
        JP C,PT_FAIL
        LD A,(PT_SRCOPEN)
        OR A
        JR Z,PC_NOCLOSE
        CALL PT_SOURCE
        LD DE,PT_SFCB
        LD C,16
        CALL 5
        XOR A
        LD (PT_SRCOPEN),A
PC_NOCLOSE:
        LD HL,PC_LEFT
        DEC (HL)
        JP Z,PC_END
        LD HL,(PC_PTR)
        LD DE,80
        ADD HL,DE
        LD (PC_PTR),HL
        LD DE,OP_DATA+80
        LD BC,80
        LDIR
        LD HL,OP_DATA+88
        LD DE,PT_SFCB
        LD BC,36
        LDIR
PC_OPEN:
        LD A,(OP_DATA+80)
        CP 4
        JP Z,PI_BEGIN
        XOR A
        LD (PI_ACTIVE),A
        CALL PT_SOURCE
        LD DE,PT_SFCB
        LD C,15
        CALL 5
        CP 0FFH
        JP Z,PT_NOFILE
        LD A,1
        LD (PT_SRCOPEN),A
        LD A,(PT_SFCB+10)
        AND 80H
        JP Z,PC_BEGIN
        LD A,(OP_DATA+141)
        OR A
        JP Z,PT_NOFILE
        JP PC_BEGIN
PC_END:
        LD A,(PD_ACTIVE)
        OR A
        JP NZ,PT_CLEAN
        LD A,(PC_OPOS)
        OR A
        JR Z,PC_CLOSED
        LD E,A
        LD D,0
        LD HL,PT_DATA
        ADD HL,DE
        LD A,128
        SUB E
        LD (PC_UNUSED),A
        LD B,A
PC_PAD:
        LD (HL),01AH
        INC HL
        DJNZ PC_PAD
        CALL PT_FLUSH
        OR A
        JP NZ,PT_WFAIL
        LD A,(PC_UNUSED)
PC_CLOSED:
        LD (PT_TFCB+13),A
        CALL PT_DEST
        JP PT_FINAL
PC_MULTI: DB 0
PC_LEFT: DB 0
PC_PTR: DW 0
PC_BINARY: DB 0
PC_OPOS: DB 0
PC_IPOS: DB 0
PC_CHARV: DB 0
PC_UNUSED: DB 0
PC_INPUT: DS 128
