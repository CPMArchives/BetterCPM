; Establish the caller's stack before entering this private build gate.
P12CHECK:
        LD A,(0)
        CP 0C3H
        JR NZ,P12BAD
        LD HL,(1)
        LD DE,LY_BIOS+3
        OR A
        SBC HL,DE
        JR NZ,P12BAD
        LD HL,LY_CID
        LD DE,P12ID
        LD B,16
P12LOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,P12BAD
        INC HL
        INC DE
        DJNZ P12LOOP
        RET
P12BAD:
        IF P12CONFIG EQ 1
        LD HL,ABIMSG
        CALL PUTS
        ELSE
        LD DE,P12MSG
        LD C,9
        CALL 5
        ENDIF
        JP 0
        IF P12CONFIG EQ 0
P12MSG: DB 'Private utility build mismatch.',13,10,'$'
        ENDIF
P12ID: DB BP_ID0,BP_ID1,BP_ID2,BP_ID3,BP_ID4,BP_ID5,BP_ID6,BP_ID7
       DB BP_ID8,BP_ID9,BP_ID10,BP_ID11,BP_ID12,BP_ID13,BP_ID14,BP_ID15
