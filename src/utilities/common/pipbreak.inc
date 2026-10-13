; DRI transfer polling, with direct BDOS input so Ctrl-C cannot bypass
; the PIP transaction cleanup through cooked-input WBOOT.
PB_READ:
        LD C,11
        CALL 5
        OR A
        RET Z
        LD E,0FFH
        LD C,6
        CALL 5
        LD (PB_KEY),A
        LD E,A
        LD C,2                       ; explicit echo for the direct read
        CALL 5
        LD A,1
        RET
PB_CHAR:
        LD A,(OP_DATA+80)
        CP 4
        JR NZ,PB_DISK
        LD A,(OP_DATA+81)
        CP 18                        ; CON consumes its own input
        RET Z
PB_DISK:
        LD A,(PC_BINARY)
        OR A
        JR Z,PB_TEXT
        LD HL,PB_COUNT
        INC (HL)
        RET NZ
        JR PB_CHECK
PB_TEXT:
        LD A,(PX_RAW)
        CP 10
        RET NZ
PB_CHECK:
        CALL PB_READ
        OR A
        RET Z
        LD A,(PB_KEY)
        CP 1AH
        JR Z,PB_EOF
        LD A,1
        LD (PB_ABORT),A
PB_EOF:
        LD A,1AH
        LD (PX_RAW),A
        RET
; A: 0 fetch reader, 1 stop reader, 2 synthesize XOFF.
PB_READER:
        LD A,(OP_DATA+80)
        CP 4
        JR NZ,PB_NONE
        LD A,(OP_DATA+81)
        OR A                         ; INP
        JR Z,PB_RMODE
        CP 5                         ; RDR
        JR NZ,PB_NONE
PB_RMODE:
        LD A,(OP_DATA+125)
        LD HL,OP_DATA+131             ; DRI BLOCK or HEXT, not I alone
        OR (HL)
        JR Z,PB_NONE
        CALL PB_READ
        OR A
        RET Z
        LD A,(PB_KEY)
        CP 1AH
        JR Z,PB_STOP
        LD DE,PB_RMSG
        CALL P_PRINT
        LD A,2
        RET
PB_STOP:
        LD A,1
        RET
PB_NONE:
        XOR A
        RET
PB_COUNT: DB 0
PB_ABORT: DB 0
PB_KEY: DB 0
PB_AMSG: DB 'ABORTED',13,10,'$'
PB_RMSG: DB 'READER STOPPING',13,10,'$'
