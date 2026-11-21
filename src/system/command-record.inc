; IX = BCST buffer; return Z valid, NZ invalid. No writes to the record.
PC_VALIDATE:
        PUSH IX
        POP HL
        LD DE,PC_MAGIC
        LD B,4
PC_MLOOP:
        LD A,(DE)
        CP (HL)
        JP NZ,PC_BAD
        INC DE
        INC HL
        DJNZ PC_MLOOP
        LD A,(IX+4)
        DEC A
        CP 2
        JP NC,PC_BAD
        LD A,(IX+5)
        OR A
        JP NZ,PC_BAD
        LD A,(IX+6)
        CP 16
        JP NZ,PC_BAD
        LD A,(IX+7)
        CP 2
        JP NC,PC_BAD
        LD A,(IX+8)
        CP 127
        JP NC,PC_BAD
        LD C,A
        OR A
        LD A,(IX+7)
        JR NZ,PC_ENABLED
        OR A
        JP NZ,PC_BAD
        JR PC_CAP
PC_ENABLED:
        DEC A
        JP NZ,PC_BAD
PC_CAP:
        LD A,(IX+9)
        CP 126
        JP NZ,PC_BAD
        LD L,(IX+10)
        LD H,(IX+11)
        LD A,H
        DEC A
        OR L
        JR NZ,PC_BAD
        LD L,(IX+14)
        LD H,(IX+15)
        LD DE,LY_SYS
        OR A
        SBC HL,DE
        JR NZ,PC_BAD
        PUSH IX
        POP HL
        CALL PW_SUM256
        JR NZ,PC_BAD
        PUSH IX
        POP HL
        LD DE,16
        ADD HL,DE
        LD B,C
        LD A,B
        OR A
        JR Z,PC_RESERVED
PC_TEXT:
        LD A,(HL)
        CP 32
        JR C,PC_BAD
        CP 127
        JR NC,PC_BAD
        INC HL
        DJNZ PC_TEXT
PC_RESERVED:
        LD A,126
        SUB C
        LD B,A
        CALL PC_ZERO
        RET NZ
        LD A,(IX+4)
        CP 1
        LD B,114
        JR Z,PC_ZERO
        LD A,(HL)
        CP 'C'
        JR NZ,PC_BAD
        INC HL
        LD A,(HL)
        CP 'E'
        JR NZ,PC_BAD
        INC HL
        LD A,(HL)
        DEC A
        JR NZ,PC_BAD
        INC HL
        LD A,(HL)
        CP 4
        JR NC,PC_BAD
        INC HL
        LD A,(HL)
        CP 2
        JR NC,PC_BAD
        INC HL
        LD A,(HL)
        CP 4
        JR NC,PC_BAD
        INC HL
        LD B,108
PC_ZERO:
        LD A,B
        OR A
        RET Z
PC_ZLOOP:
        LD A,(HL)
        OR A
        RET NZ
        INC HL
        DJNZ PC_ZLOOP
        RET
PC_BAD:
        LD A,1
        OR A
        RET
PC_MAGIC: DB 'BCST'
