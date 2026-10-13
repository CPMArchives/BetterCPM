; Historical DEST=SOURCE,... scanner. HL/B span, no BDOS calls, CF=invalid.
; Return operand spans in PP_SPANS (pointer,length), destination first.
; Strings after S/Q inside [] are terminated by 1Ah; punctuation there is data.
PP_PARSE:
        LD (PP_BASE),HL
        LD A,B
        LD (PP_SIZE),A
        XOR A
        LD (PP_COUNT),A
        LD (PP_EQ),A
        LD (PP_BRACK),A
        LD (PP_STRING),A
        LD (PP_LENGTH),A
        LD IX,PP_SPANS
        LD (PP_START),HL
PP_LOOP:
        LD A,B
        OR A
        JP Z,PP_END
        LD A,(HL)
        LD C,A
        LD A,(PP_STRING)
        OR A
        JR Z,PP_NORMAL
        LD A,C
        CP 01AH
        JR NZ,PP_ADV
        XOR A
        LD (PP_STRING),A
        JR PP_ADV
PP_NORMAL:
        LD A,C
        CP '['
        JR Z,PP_OPEN
        CP ']'
        JR Z,PP_CLOSE
        LD A,(PP_BRACK)
        OR A
        JR Z,PP_OUTSIDE
        LD A,C
        AND 0DFH
        CP 'S'
        JR Z,PP_STR
        CP 'Q'
        JR NZ,PP_ADV
PP_STR:
        LD A,1
        LD (PP_STRING),A
        JR PP_ADV
PP_OPEN:
        LD A,(PP_BRACK)
        OR A
        JP NZ,PP_BAD
        INC A
        LD (PP_BRACK),A
        JR PP_ADV
PP_CLOSE:
        LD A,(PP_BRACK)
        OR A
        JP Z,PP_BAD
        XOR A
        LD (PP_BRACK),A
        JR PP_ADV
PP_OUTSIDE:
        LD A,C
        CP '='
        JR Z,PP_EQUALS
        CP '_'
        JR Z,PP_EQUALS
        CP ','
        JR Z,PP_COMMA
PP_ADV:
        INC HL
        LD A,(PP_LENGTH)
        INC A
        LD (PP_LENGTH),A
        DEC B
        JP PP_LOOP
PP_EQUALS:
        LD A,(PP_EQ)
        OR A
        JP NZ,PP_BAD
        INC A
        LD (PP_EQ),A
        JR PP_SEP
PP_COMMA:
        LD A,(PP_EQ)
        OR A
        JP Z,PP_BAD
PP_SEP:
        PUSH BC
        PUSH HL
        CALL PP_STORE
        POP HL
        POP BC
        RET C
        INC HL
        DEC B
        LD (PP_START),HL
        XOR A
        LD (PP_LENGTH),A
        JP PP_LOOP
PP_END:
        LD A,(PP_BRACK)
        OR A
        JP NZ,PP_BAD
        LD A,(PP_STRING)
        OR A
        JP NZ,PP_BAD
        LD A,(PP_EQ)
        OR A
        JP Z,PP_BAD
        CALL PP_STORE
        RET C
        LD A,(PP_COUNT)
        CP 2
        JR C,PP_BAD
        JP OP_PLAN
PP_STORE:
        LD HL,(PP_START)
        LD A,(PP_LENGTH)
        LD E,A
PP_LEAD:
        LD A,E
        OR A
        JR Z,PP_BAD
        LD A,(HL)
        CP ' '
        JR NZ,PP_TRAIL
        INC HL
        DEC E
        JR PP_LEAD
PP_TRAIL:
        PUSH HL
        LD D,0
        ADD HL,DE
        DEC HL
PP_TRIM:
        LD A,(HL)
        CP ' '
        JR NZ,PP_TRIMMED
        DEC E
        DEC HL
        JR PP_TRIM
PP_TRIMMED:
        POP HL
        LD A,(PP_COUNT)
        CP 64
        JR NC,PP_BAD
        INC A
        LD (PP_COUNT),A
        LD (IX+0),L
        LD (IX+1),H
        LD A,E
        LD (IX+2),A
        INC IX
        INC IX
        INC IX
        OR A
        RET
PP_BAD:
        XOR A
        LD (PP_COUNT),A
        SCF
        RET
PP_BASE: DW 0
PP_SIZE: DB 0
PP_START: DW 0
PP_LENGTH: DB 0
PP_COUNT: DB 0
PP_EQ: DB 0
PP_BRACK: DB 0
PP_STRING: DB 0
PP_SPANS: DS 192
