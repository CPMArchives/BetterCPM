; Validate lengths against the exact cold choices and checksum before arithmetic.
PH_VALIDATE:
        LD HL,(LY_PD2)
        LD DE,04450H
        OR A
        SBC HL,DE
        JR NZ,PH_BAD
        LD HL,(LY_PD2+2)
        LD DE,00C02H
        OR A
        SBC HL,DE
        JR NZ,PH_BAD
        LD HL,LY_PD2
        LD B,6
        CALL PW_SUM
        RET NZ
        LD IX,LY_PD2+4
        LD HL,PW_HSIZES
        CALL PH_CHOICE
        RET NZ
        LD HL,PW_MSIZES
        CALL PH_CHOICE
        RET NZ
        LD HL,PW_VSIZES
        CALL PH_CHOICE
        RET NZ
        LD HL,LY_PD2
        LD DE,(LY_PD2+4)
        OR A
        SBC HL,DE
        LD DE,(LY_PD2+6)
        SBC HL,DE
        LD DE,(LY_PD2+8)
        SBC HL,DE
        JR C,PH_BAD
        XOR A
        RET
PH_CHOICE:
        LD E,(IX+0)
        LD D,(IX+1)
        LD B,4
PH_LOOP:
        LD A,(HL)
        INC HL
        CP E
        JR NZ,PH_SKIP
        LD A,(HL)
        CP D
        JR Z,PH_FOUND
PH_SKIP:
        INC HL
        DJNZ PH_LOOP
        JR PH_BAD
PH_FOUND:
        INC IX
        INC IX
        XOR A
        RET
PW_MSIZES: DW 0,128,0,128
PH_BAD:
        LD A,1
        OR A
        RET
PW_HSIZES: DW 0,128,192,384
PW_VSIZES: DW 0,128,256,512
PW_SUM256:
        LD B,128
PW_SUM:
        LD DE,0
PW_SUMLOOP:
        LD A,(HL)
        ADD A,E
        LD E,A
        INC HL
        LD A,(HL)
        ADC A,D
        LD D,A
        INC HL
        DJNZ PW_SUMLOOP
        LD A,D
        OR E
        RET
