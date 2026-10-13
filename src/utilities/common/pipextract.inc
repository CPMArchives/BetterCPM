; DRI GETSOURCE extraction: matching does not retry overlaps and succeeds
; on the character AFTER the string. Original operand strings remain read-only.
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
        JP HH_PUT
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

; This increment qualifies extraction only for text sources. Reject object
; extraction before any transfer I/O rather than assume peripheral EOF rules.
PE_VALID:
        LD HL,(PC_PTR)
        LD DE,51
        ADD HL,DE
        LD A,(HL)
        INC HL
        OR (HL)
        LD E,A
        LD HL,(PC_PTR)
        LD BC,60
        ADD HL,BC
        LD A,(HL)
        OR E
        INC HL
        INC HL
        OR (HL)
        RET Z
        LD HL,(PC_PTR)
        LD DE,58
        ADD HL,DE
        LD A,(HL)
        OR A
        JR NZ,PE_VBAD
        LD HL,(PC_PTR)
        LD DE,17
        ADD HL,DE
        LD A,(HL)
        AND 7FH
        CP 'C'
        JR NZ,PE_VOK
        INC HL
        LD A,(HL)
        AND 7FH
        CP 'O'
        JR NZ,PE_VOK
        INC HL
        LD A,(HL)
        AND 7FH
        CP 'M'
        JR Z,PE_VBAD
PE_VOK:
        OR A
        RET
PE_VBAD:
        SCF
        RET
