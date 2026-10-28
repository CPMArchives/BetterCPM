; Strict untagged md5sum input; LISTGET normalizes ASCII letter case only.
PARSELIN:
        LD HL,LISTLINE
        LD DE,EVALUES
        LD B,16
MDPARHEX:
        CALL MDGETHEX
        RET C
        RLCA
        RLCA
        RLCA
        RLCA
        LD C,A
        CALL MDGETHEX
        RET C
        OR C
        LD (DE),A
        INC DE
        DJNZ MDPARHEX
        LD A,(HL)
        CP ' '
        JR NZ,MDPARBAD
        INC HL
        LD A,(HL)
        CP '*'
        JR Z,MDPARNAM
        CP ' '
        JR NZ,MDPARBAD
MDPARNAM:
        INC HL
        PUSH HL
        LD B,0
MDPARLEN:
        LD A,(HL)
        OR A
        JR Z,MDPAREND
        CP ' '
        JR Z,MDPARPOP
        CP 9
        JR Z,MDPARPOP
        CP ':'
        JR Z,MDPARPOP
        CP '/'
        JR Z,MDPARPOP
        CP 05CH
        JR Z,MDPARPOP
        CP 128
        JR NC,MDPARPOP
        INC HL
        INC B
        LD A,B
        CP 13
        JR NC,MDPARPOP
        JR MDPARLEN
MDPAREND:
        POP HL
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE
        POP BC
        POP HL
        RET C
        LD DE,MDPARFCB
        CALL BC_PFCB
        LD HL,MDPARFCB+1
        LD DE,ENAME
        LD BC,11
        LDIR
        LD A,1
        OR A
        RET
MDPARPOP:
        POP HL
MDPARBAD:
        SCF
        RET
MDGETHEX:
        LD A,(HL)
        INC HL
        SUB '0'
        JR C,MDPARBAD
        CP 10
        JR NC,MDHEXLETTER
        OR A
        RET
MDHEXLETTER:
        SUB 'A'-'0'
        JR C,MDPARBAD
        CP 6
        JR NC,MDPARBAD
        ADD A,10
        OR A
        RET
MDPARFCB: DS 36
