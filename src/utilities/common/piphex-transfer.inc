; Text H/I transfer integration. The bounded validator handles complete
; records; this layer scans colon boundaries and drains zero-length tails.
HH_INIT:
        XOR A
        LD (HH_COUNT),A
        LD (HH_STATE),A
        LD (HH_DONE),A
        LD A,(OP_DATA+131)
        LD HL,OP_DATA+132
        OR (HL)
        LD (HH_MODE),A
        LD A,(OP_DATA+80)
        CP 4
        RET NZ
        LD A,(OP_DATA+81)
        CP 19
        JR NC,HH_PSEUD
        CP 5                         ; high-speed readers precede RDR
        RET NC
        LD A,(OP_DATA)
        CP 2                         ; named disk destination
        RET NZ
        LD A,(OP_DATA+17)
        CP 'H'
        RET NZ
        LD A,(OP_DATA+18)
        CP 'E'
        RET NZ
        LD A,(OP_DATA+19)
        CP 'X'
        RET NZ
        LD A,1
        LD (OP_DATA+131),A            ; effective H also enables reader polling
        LD (HH_MODE),A
        RET
HH_PSEUD:
        XOR A                       ; pseudo-sources bypass READTAPE
        LD (HH_MODE),A
        RET
HH_PUT:
        LD (HH_CHAR),A
        LD A,(HH_MODE)
        OR A
        LD A,(HH_CHAR)
        JP Z,PF_PUT
        CP 13H
        JR NZ,HH_NOTX
        ; Complete records are already flushed by PI_PUT. Preserve the
        ; partial record in PT_DATA, just as DRI CLEARBUFF does.
        XOR A
        RET
HH_NOTX:
        LD A,(HH_STATE)
        OR A
        JR NZ,HH_APPEND
        LD A,(HH_CHAR)
        CP ':'
        JR Z,HH_START
        XOR A
        RET
HH_START:
        LD A,1
        LD (HH_STATE),A
HH_APPEND:
        CALL HH_STORE
        OR A
        JR NZ,HH_TOO
        LD A,(HH_STATE)
        CP 2
        JR Z,HH_OK
        LD HL,HH_INPUT
        LD A,(HH_COUNT)
        LD B,A
        CALL PH_PARSE
        CP 5
        JR Z,HH_OK
        OR A
        JR Z,HH_DATA
        CP 1
        JR NZ,HH_RECOVER
        LD A,2
        LD (HH_STATE),A
HH_OK:
        XOR A
        RET
HH_TOO:
        LD A,4
        JR HH_RECOVER
HH_DATA:
        CALL HH_EMIT
        OR A
        RET NZ
        JP HH_RESET
HH_STORE:
        LD A,(HH_COUNT)
        CP 79
        JR NC,HH_FULL
        LD E,A
        LD D,0
        LD HL,HH_INPUT
        ADD HL,DE
        LD A,(HH_CHAR)
        LD (HL),A
        LD HL,HH_COUNT
        INC (HL)
        LD A,(HL)
        CP 79
        JR NC,HH_FULL
        XOR A
        RET
HH_FULL:
        LD A,4
        RET
HH_EMIT:
        LD HL,HH_INPUT
        LD (HH_PTR),HL
        LD A,(HH_COUNT)
        LD (HH_LEFT),A
HH_ELOOP:
        LD A,(HH_LEFT)
        OR A
        JR Z,HH_CRLF
        LD HL,(HH_PTR)
        LD A,(HL)
        INC HL
        LD (HH_PTR),HL
        CALL PF_PUT
        OR A
        RET NZ
        LD HL,HH_LEFT
        DEC (HL)
        JR HH_ELOOP
HH_CRLF:
        LD A,13
        CALL PF_PUT
        OR A
        RET NZ
        LD A,10
        JP PF_PUT
HH_RESET:
        XOR A
        LD (HH_STATE),A
        LD (HH_COUNT),A
        RET
HH_RECOVER:
        LD DE,HH_DIGMSG
        CP 2
        JR Z,HH_REPORT
        LD DE,HH_CSUM
        CP 3
        JR Z,HH_REPORT
        LD DE,HH_LONG
HH_REPORT:
        CALL P_PRINT
        LD DE,P_NL
        CALL P_PRINT
        LD HL,HH_INPUT
        LD (HH_PTR),HL
        LD A,(HH_COUNT)
        LD (HH_LEFT),A
HH_RLOOP:
        LD A,(HH_LEFT)
        OR A
        JR Z,HH_ASK
        LD HL,(HH_PTR)
        LD E,(HL)
        INC HL
        LD (HH_PTR),HL
        LD C,2
        CALL 5
        LD HL,HH_LEFT
        DEC (HL)
        JR HH_RLOOP
HH_ASK:
        LD DE,HH_RMSG
        CALL P_PRINT
        LD C,1
        CALL 5
        CP 1AH
        JR NZ,HH_RETRY
        LD A,1
        LD (HH_DONE),A
        LD (PE_DONE),A
HH_RETRY:
        JP HH_RESET
HH_EOF:
        LD A,(HH_MODE)
        OR A
        RET Z
        LD A,(HH_DONE)
        OR A
        JR NZ,HH_OKEND
        LD A,(HH_STATE)
        CP 2
        JR Z,HH_TERMINAL
        OR A
        JR Z,HH_CONFIRM
        LD A,2
        CALL HH_RECOVER
        LD A,(HH_DONE)
        OR A
        JR NZ,HH_OKEND
HH_CONFIRM:
        LD DE,HH_ZMSG
        CALL P_PRINT
        LD C,1
        CALL 5
        CP 1AH
        JR NZ,HH_CONFIRM
HH_OKEND:
        XOR A
        RET
HH_TERMINAL:
        LD A,1AH
        LD (HH_CHAR),A
        CALL HH_STORE
        OR A
        JR NZ,HH_TERLONG
        LD A,(OP_DATA+132)           ; I suppresses zero-length tail
        OR A
        JP Z,HH_EMIT
        JP HH_CRLF
HH_TERLONG:
        LD A,4
        JP HH_RECOVER
HH_MODE: DB 0
HH_STATE: DB 0
HH_COUNT: DB 0
HH_DONE: DB 0
HH_CHAR: DB 0
HH_PTR: DW 0
HH_LEFT: DB 0
HH_INPUT: DS 80
HH_DIGMSG: DB 'INVALID DIGIT$'
HH_CSUM: DB 'CHECKSUM ERROR$'
HH_LONG: DB 'RECORD TOO LONG$'
HH_RMSG: DB 13,10,'CORRECT ERROR, TYPE RETURN OR CTL-Z',13,10,'$'
HH_ZMSG: DB 'END OF FILE, CTL-Z?$'
