; Strip and validate destination attribute qualifiers before ordinary DU parsing.
CTDSCOPE:
        XOR A
        LD (CTD_SET),A
        LD (CTD_CLR),A
        CALL OQ_SPLIT
        JR C,CTD_BAD
        LD (CTD_PTR),HL
        LD A,B
        LD (CTD_LEN),A
        OR A
        JR Z,CTD_BAD
        LD A,(OQ_LEN)
        OR A
        JR Z,CTD_PARSE
        LD B,A
        LD HL,(OQ_PTR)
        CALL AT_STATE
        JR C,CTD_BAD
        LD A,(AT_SET)
        LD (CTD_SET),A
        LD A,(AT_CLEAR)
        LD (CTD_CLR),A
CTD_PARSE:
        LD HL,(CTD_PTR)
        LD A,(CTD_LEN)
        LD B,A
        LD DE,BC_NEWFCB
        JP BC_COPAR
CTD_BAD:
        XOR A
        RET

; Apply only RO/SYS/ARC overrides after source attribute inheritance and /V.
CTDATTR:
        LD HL,BC_NEWFCB+9
        LD B,3
        LD C,1
CTD_BYTE:
        LD E,(HL)
        LD A,(CTD_CLR)
        AND C
        JR Z,CTD_TEST
        LD A,E
        AND 7FH
        LD E,A
CTD_TEST:
        LD A,(CTD_SET)
        AND C
        JR Z,CTD_STORE
        LD A,E
        OR 80H
        LD E,A
CTD_STORE:
        LD (HL),E
        INC HL
        LD A,C
        ADD A,A
        LD C,A
        DJNZ CTD_BYTE
        LD A,(CT_BACK)
        OR A
        RET Z
        LD HL,BC_NEWFCB+11
        RES 7,(HL)
        RET
CTD_SET: DB 0
CTD_CLR: DB 0
CTD_PTR: DW 0
CTD_LEN: DB 0
