; One console turn. Caller owns file streams and the command loop.
; Carry clear A=0: reprompt; A=E/H/O/Q: authorized standalone file action.
; Carry A=1: fatal stream diagnostic printed and caller DU/DMA ready for exit.
EU_READ:
        CALL EU_PROMPT
        LD DE,EU_BUFFER
        LD C,10
        CALL 5
        LD A,10
        CALL ET_TTY
        XOR A
        LD (ET_COL),A
        LD A,(EU_BUFFER+1)
        CP 1
        JP NZ,EU_NORMAL
        LD A,(EU_BUFFER+2)
        CALL EI_UP
        CP 'E'
        RET Z
        CP 'H'
        RET Z
        CP 'O'
        JP Z,EU_ASK
        CP 'Q'
        JP Z,EU_ASK
EU_NORMAL:
        LD A,(EU_BUFFER+1)
        OR A
        JP NZ,EU_RUN
        LD HL,EU_BLANK
        LD B,1
        JP EU_EXEC
EU_RUN:
        LD B,A
        LD HL,EU_BUFFER+2
EU_EXEC:
        CALL EC_RUN
        JP NC,EU_DONE
        CP 1
        JP Z,EU_INSERT
        CP 2
        JP Z,EU_MEMORY
EU_ERROR:
        LD (EU_FLAG),A
        LD A,(EC_IOERR)
        OR A
        JP NZ,FD_FATAL
        CALL IN_CRLF
        LD HL,EU_BREAK
        CALL EU_SAY
        LD A,(EU_FLAG)
        CALL ET_PRINT
        LD HL,EU_AT
        CALL EU_SAY
        LD A,(EC_WHERE)
        CALL ET_PRINT
        CALL IN_CRLF
EU_DONE:
        XOR A
        RET
EU_INSERT:
        CALL IN_START
EU_KEY:
        LD C,1
        CALL 5
        LD C,A
        CALL IN_FEED
        JP C,EU_ERROR
        OR A
        JP Z,EU_KEY
        JP EU_DONE
EU_ASK:
        LD (EU_REQ),A
        CALL IN_CRLF
        LD A,(EU_REQ)
        CALL ET_TTY
        LD HL,EU_YN
        CALL EU_SAY
        LD C,1
        CALL 5
        CALL EI_UP
        LD (EU_REPLY),A
        CALL IN_CRLF
        LD A,(EU_REPLY)
        CP 'Y'
        JP NZ,EU_DONE
        LD A,(EU_REQ)
        OR A
        RET
EU_PROMPT:
        LD A,(EC_VERIFY)
        OR A
        JP Z,EU_STAR
        LD A,(ET_COL)
        OR A
        JP NZ,EU_STAR
        CALL IN_LINE
        LD HL,(EB_BACK)
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        JP NZ,EU_NUMBER
        LD (ET_LINE),HL             ; empty suffix uses blank/zero prompt
EU_NUMBER:
        LD A,'*'
        LD (ET_LABEL),A
        CALL ET_NUMBER
        LD A,' '
        LD (ET_LABEL),A
        RET
EU_STAR:
        LD A,'*'
        JP ET_TTY
EU_MEMORY:
        LD HL,(EB_BACK)
        LD DE,(EB_FRONT)
        OR A
        SBC HL,DE
        LD (ET_LINE),HL
        CALL ET_DECIMAL
        LD A,'/'
        CALL ET_TTY
        LD HL,(EB_LIMIT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        LD (ET_LINE),HL
        CALL ET_DECIMAL
        CALL IN_CRLF
        JP EU_DONE
EU_SAY:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        CALL ET_TTY
        JP EU_SAY
EU_BREAK: DB 'BREAK "',0
EU_AT: DB '" AT ',0
EU_YN: DB '-(Y/N)?',0
EU_BLANK: DB 13
EU_FLAG: DB 0
EU_REQ: DB 0
EU_REPLY: DB 0
EU_BUFFER: DB 128,0
        DS 129
