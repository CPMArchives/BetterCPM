; Bounded D[0..31]: source prefix shared by RSX and XSUB.
; SD_INIT captures the caller DU. SD_PARSE consumes a prefix in HL/B, leaves
; unqualified text untouched, and returns A=0 or 1 (invalid). No disk selection.
SD_INIT:
        LD C,25
        CALL BDOS
        LD (SD_DRIVE),A
        LD E,255
        LD C,32
        CALL BDOS
        LD (SD_USER),A
        XOR A
        LD (SD_EXPLICIT),A
        RET
SD_PARSE:
        PUSH HL
        PUSH BC
        LD A,B
        CP 4
        JR C,SD_LIMIT
        LD A,4
SD_LIMIT:
        LD C,A
        OR A
        JR Z,SD_NONE
SD_SCAN:
        LD A,(HL)
        CP ':'
        JR Z,SD_FOUND
        INC HL
        DEC C
        JR NZ,SD_SCAN
SD_NONE:
        POP BC
        POP HL
        XOR A
        RET
SD_FOUND:
        POP BC
        POP HL
        LD A,(HL)
        CP 'a'
        JR C,SD_CASE
        CP 'p'+1
        JR NC,SD_CASE
        SUB 32
SD_CASE:
        SUB 'A'
        CP 16
        JR NC,SD_BAD
        LD (SD_DRIVE),A
        INC HL
        DEC B
        LD C,0
        LD D,0
SD_DIGIT:
        LD A,B
        OR A
        JR Z,SD_BAD
        LD A,(HL)
        CP ':'
        JR Z,SD_END
        SUB '0'
        CP 10
        JR NC,SD_BAD
        LD E,A
        INC D
        LD A,D
        CP 3
        JR NC,SD_BAD
        LD A,C
        ADD A,A
        ADD A,A
        ADD A,C
        ADD A,A
        ADD A,E
        CP 32
        JR NC,SD_BAD
        LD C,A
        INC HL
        DEC B
        JR SD_DIGIT
SD_END:
        LD A,D
        OR A
        JR Z,SD_KEEP
        LD A,C
        LD (SD_USER),A
SD_KEEP:
        INC HL
        DEC B
        LD A,1
        LD (SD_EXPLICIT),A
        XOR A
        RET
SD_BAD:
        LD A,1
        OR A
        RET
SD_DRIVE: DB 0
SD_USER: DB 0
SD_EXPLICIT: DB 0
