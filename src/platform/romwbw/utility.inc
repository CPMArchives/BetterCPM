; Shared private RomWBW utility helpers. All I/O uses standard HBIOS calls.
U_CHECK:
        LD B,0
        LD C,181
        CALL 5
        LD DE,U_MAGIC
        LD B,8
UC_MAGIC:
        LD A,(DE)
        CP (HL)
        JR NZ,U_BAD
        INC HL
        INC DE
        DJNZ UC_MAGIC
        LD HL,LY_CID
        LD DE,U_ID
        LD B,16
UC_ID:
        LD A,(DE)
        CP (HL)
        JR NZ,U_BAD
        INC HL
        INC DE
        DJNZ UC_ID
        XOR A
        LD (U_REQ),A
        CALL U_GET
        JR NZ,U_BAD
        LD A,(U_REQ+1)
        LD (U_BOOT),A
        RET
U_BAD:
        LD DE,U_MISMATCH
        CALL U_PUTS
        JP 0
U_GET:
        LD B,3
U_API:
        LD DE,U_REQ
        LD C,181
        CALL 5
        LD A,H
        OR L
        RET
U_PUTS:
        LD C,9
        JP 5
U_PUTC:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD C,2
        CALL 5
        POP HL
        POP DE
        POP BC
        POP AF
        RET
U_CRLF:
        LD A,13
        CALL U_PUTC
        LD A,10
        JP U_PUTC
; Decimal byte A, with no leading zeroes.
U_DEC:
        LD B,100
        LD C,'0'
UD_100:
        CP B
        JR C,UD_10
        SUB B
        INC C
        JR UD_100
UD_10:
        LD E,A
        LD A,C
        CP '0'
        JR Z,UD_TENS
        CALL U_PUTC
UD_TENS:
        LD D,A
        LD A,E
        LD C,'0'
UD_SUB:
        CP 10
        JR C,UD_TOUT
        SUB 10
        INC C
        JR UD_SUB
UD_TOUT:
        LD E,A
        LD A,C
        CP '0'
        JR NZ,UD_EMIT
        LD A,D
        CP '0'
        JR Z,UD_ONE
        LD A,C
UD_EMIT:
        CALL U_PUTC
UD_ONE:
        LD A,E
        ADD A,'0'
        JP U_PUTC
; Seek U_LBA and transfer one 512-byte sector. B=13h/14h, C=unit, HL=buffer.
U_IO:
        LD (U_BUFFER),HL
        LD A,B
        LD (U_FUNC),A
        LD A,C
        LD (U_UNIT),A
        LD B,012H
        LD DE,08000H
        LD HL,(U_LBA)
        CALL 0FFF0H
        OR A
        RET NZ
        LD B,0F3H
        CALL 0FFF0H
        OR A
        RET NZ
        LD D,C
        LD A,(U_UNIT)
        LD C,A
        LD A,(U_FUNC)
        LD B,A
        LD E,1
        LD HL,(U_BUFFER)
        CALL 0FFF0H
        OR A
        RET
; Case-insensitive prefix comparison, HL=input DE=uppercase pattern.
; On success HL follows the prefix; otherwise it remains at the mismatch.
U_PREFIX:
        LD A,(DE)
        OR A
        RET Z
        LD C,A
        LD A,(HL)
        CP 'a'
        JR C,UP_CASE
        CP 'z'+1
        JR NC,UP_CASE
        AND 0DFH
UP_CASE:
        CP C
        RET NZ
        INC HL
        INC DE
        JR U_PREFIX
; Sum all 256 little-endian words at HL. Result DE, HL advanced 512.
U_SUM:
        LD DE,0
        LD B,0
US_NEXT:
        LD A,E
        ADD A,(HL)
        INC HL
        LD E,A
        LD A,D
        ADC A,(HL)
        INC HL
        LD D,A
        DJNZ US_NEXT
        LD A,D
        OR E
        RET
; CRC-16/CCITT, DE accumulator, HL pointer, BC byte length.
U_CRC:
        LD A,(HL)
        XOR D
        LD D,A
        PUSH BC
        LD B,8
UR_BIT:
        SLA E
        RL D
        JR NC,UR_NEXT
        LD A,D
        XOR 010H
        LD D,A
        LD A,E
        XOR 021H
        LD E,A
UR_NEXT:
        DJNZ UR_BIT
        POP BC
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,U_CRC
        RET
U_MAGIC: DB 'BDCF',6,4,0,64
U_ID: DB BP_ID0,BP_ID1,BP_ID2,BP_ID3,BP_ID4,BP_ID5,BP_ID6,BP_ID7
      DB BP_ID8,BP_ID9,BP_ID10,BP_ID11,BP_ID12,BP_ID13,BP_ID14,BP_ID15
U_MISMATCH: DB 'Requires matching BetterCP/M RomWBW block API.',13,10,'$'
U_REQ: DS 80
U_BOOT: DB 0
U_LBA: DW 0
U_BUFFER: DW 0
U_FUNC: DB 0
U_UNIT: DB 0
