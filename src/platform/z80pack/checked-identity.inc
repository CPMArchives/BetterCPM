; Checked resident identity service in existing disk padding.
        DS LY_CCMP-$
Z_CMP: LD B,16
Z_CMLP: LD A,(DE)
        SUB (HL)
        RET NZ
        INC DE
        INC HL
        DJNZ Z_CMLP
        RET
Z_ID: DB BP_ID0,BP_ID1,BP_ID2,BP_ID3,BP_ID4,BP_ID5,BP_ID6,BP_ID7
      DB BP_ID8,BP_ID9,BP_ID10,BP_ID11,BP_ID12,BP_ID13,BP_ID14,BP_ID15
