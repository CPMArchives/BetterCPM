; DRI GETSOURCE extraction: matching does not retry overlaps and succeeds
; on the character AFTER the string. Original operand strings remain read-only.
; Object mode is supplied by the DRI dispatch rules in PC_BEGIN: .COM, or [O]
; on the concatenation/device path. Embedded Ctrl-Z bypasses S/Q matching;
; object READ_EOF copies it and continues to physical EOF. A Q match inserts
; CR/LF/Ctrl-Z and resumes object input after discarding its lookahead. HEX
; instead ends on logical Ctrl-Z, including Q's synthetic EOF.
PE_INIT:
        CALL HH_INIT
        XOR A
        LD (PE_MATCH),A
        LD (PE_DONE),A
        LD A,(OP_DATA+142)
        LD (PE_START),A
        LD A,(OP_DATA+140)
        LD (PE_QUIT),A
        RET
PE_FEED:
        LD (PE_CHAR),A
        CP 1AH                       ; GETSOURCE bypasses matching on Ctrl-Z
        JP Z,HH_PUT
        LD A,(PE_START)
        OR A
        JR Z,PE_QTEST
        LD HL,(OP_DATA+150)
        LD A,(OP_DATA+152)
        CALL PE_TEST
        JR C,PE_SFOUND
        XOR A
        RET
PE_SFOUND:
        XOR A
        LD (PE_START),A
        LD (PE_MATCH),A
        LD HL,(OP_DATA+150)
        LD A,(OP_DATA+152)
        LD (PE_LEFT),A
        LD (PE_PTR),HL
PE_SLOOP:
        LD A,(PE_LEFT)
        OR A
        JR Z,PE_CURRENT
        LD HL,(PE_PTR)
        LD A,(HL)
        INC HL
        LD (PE_PTR),HL
        CALL HH_PUT
        OR A
        RET NZ
        LD HL,PE_LEFT
        DEC (HL)
        JR PE_SLOOP
PE_QTEST:
        LD A,(PE_QUIT)
        OR A
        JR Z,PE_CURRENT
        LD HL,(OP_DATA+153)
        LD A,(OP_DATA+155)
        CALL PE_TEST
        JR NC,PE_CURRENT
        XOR A
        LD (PE_QUIT),A
        LD A,1
        LD (PE_DONE),A
        LD A,13
        CALL HH_PUT
        OR A
        RET NZ
        LD A,10
        CALL HH_PUT
        OR A
        RET NZ
        LD A,(PC_BINARY)
        OR A
        RET Z
        LD A,(HH_MODE)
        OR A
        JR NZ,PE_QDONE
        ; Object READ_EOF ignores the synthetic EOF after Q's CR/LF and
        ; resumes physical input. The consumed lookahead is discarded.
        XOR A
        LD (PE_DONE),A
        LD A,1AH
        JP HH_PUT
PE_QDONE:
        XOR A
        RET
PE_CURRENT:
        LD A,(PE_CHAR)
        JP HH_PUT
PE_TEST:
        LD E,A                       ; length
        LD A,(PE_MATCH)
        CP E
        JR Z,PE_HIT
        LD E,A
        LD D,0
        ADD HL,DE
        LD A,(PE_CHAR)
        CP (HL)
        JR NZ,PE_MISS
        LD HL,PE_MATCH
        INC (HL)
        OR A
        RET
PE_MISS:
        XOR A
        LD (PE_MATCH),A
        RET
PE_HIT:
        SCF
        RET
PE_CHECK:
        LD DE,PE_SERROR
        LD A,(PE_START)
        OR A
        JR NZ,PE_FAILED
        LD DE,PE_QERROR
        LD A,(PE_QUIT)
        OR A
        RET Z
PE_FAILED:
        SCF
        RET
PE_START: DB 0
PE_QUIT: DB 0
PE_MATCH: DB 0
PE_DONE: DB 0
PE_CHAR: DB 0
PE_LEFT: DB 0
PE_PTR: DW 0
PE_SERROR: DB 'START NOT FOUND',13,10,'$'
PE_QERROR: DB 'QUIT NOT FOUND',13,10,'$'
