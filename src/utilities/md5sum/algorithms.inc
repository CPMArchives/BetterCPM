; RFC 1321 MD5. CUPDATE consumes A, preserves IX (the file-stream pointer).
; State is serialized little endian; count is the original 64-bit bit length.
CINIT:
        LD HL,MDINITIAL
        LD DE,CVALUES
        LD BC,16
        LDIR
        LD HL,MDLENGTH
        LD BC,8
        CALL ZERO
        XOR A
        LD (MDPOS),A
        RET
CUPDATE:
        PUSH AF
        LD HL,MDLENGTH
        LD A,(HL)
        ADD A,8
        LD (HL),A
        JR NC,MDCOUNTED
        LD B,7
MDLENCARRY:
        INC HL
        INC (HL)
        JR NZ,MDCOUNTED
        DJNZ MDLENCARRY
MDCOUNTED:
        POP AF
MDABSORB:
        LD C,A
        LD A,(MDPOS)
        LD E,A
        LD D,0
        LD HL,MDBLOCK
        ADD HL,DE
        LD (HL),C
        INC A
        AND 63
        LD (MDPOS),A
        RET NZ
        JP MDCOMPRESS
CFINISH:
        LD HL,MDLENGTH
        LD DE,MDFINLEN
        LD BC,8
        LDIR
        LD A,080H
        CALL MDABSORB
MDPAD:
        LD A,(MDPOS)
        CP 56
        JR Z,MDPUTLEN
        XOR A
        CALL MDABSORB
        JR MDPAD
MDPUTLEN:
        LD HL,MDFINLEN
        LD B,8
MDLENBYTE:
        PUSH HL
        PUSH BC
        LD A,(HL)
        CALL MDABSORB
        POP BC
        POP HL
        INC HL
        DJNZ MDLENBYTE
        RET
MDCOMPRESS:
        LD HL,CVALUES
        LD DE,MDWORK
        LD BC,16
        LDIR
        LD HL,MDSCHEDULE
        LD (MDTPTR),HL
        XOR A
        LD (MDOP),A
MDSTEP:
        LD HL,MDTEMP
        LD DE,MDWORK+4
        LD B,4
MDFBYTE:
        LD A,(DE)
        LD C,A
        LD A,(MDOP)
        CP 16
        JR C,MDF1
        CP 32
        JR C,MDF2
        CP 48
        JR C,MDF3
        ; I(B,C,D) = C XOR (B OR NOT D).
        PUSH HL
        PUSH DE
        EX DE,HL
        LD DE,8
        ADD HL,DE
        LD A,(HL)
        CPL
        OR C
        LD C,A
        LD DE,-4
        ADD HL,DE
        LD A,(HL)
        XOR C
        JR MDFSTORE
MDF1:
        ; F = D XOR (B AND (C XOR D)).
        PUSH HL
        PUSH DE
        EX DE,HL
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        LD DE,4
        ADD HL,DE
        XOR (HL)
        AND C
        XOR (HL)
        JR MDFSTORE
MDF2:
        ; G = C XOR (D AND (B XOR C)).
        PUSH HL
        PUSH DE
        EX DE,HL
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        XOR C
        LD C,A
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        AND C
        LD C,A
        LD DE,-4
        ADD HL,DE
        LD A,(HL)
        XOR C
        JR MDFSTORE
MDF3:
        PUSH HL
        PUSH DE
        EX DE,HL
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        XOR C
        LD C,A
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        XOR C
MDFSTORE:
        POP DE
        POP HL
        LD (HL),A
        INC HL
        INC DE
        DEC B
        JP NZ,MDFBYTE
        LD HL,MDTEMP
        LD DE,MDWORK
        CALL MDADD
        LD HL,(MDTPTR)
        LD E,(HL)
        LD D,0
        INC HL
        LD A,(HL)
        LD (MDROTATE),A
        INC HL
        LD (MDTPTR),HL
        LD HL,MDBLOCK
        ADD HL,DE
        EX DE,HL
        LD HL,MDTEMP
        CALL MDADD
        LD DE,(MDTPTR)
        LD HL,MDTEMP
        CALL MDADD
        LD HL,(MDTPTR)
        LD DE,4
        ADD HL,DE
        LD (MDTPTR),HL
        LD A,(MDROTATE)
        LD B,A
MDROTL:
        LD HL,MDTEMP
        SLA (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        LD A,(MDTEMP)
        ADC A,0
        LD (MDTEMP),A
        DJNZ MDROTL
        LD HL,MDTEMP
        LD DE,MDWORK+4
        CALL MDADD
        ; A<-D, D<-C, C<-B, B<-new value; bytewise disjoint copies.
        LD HL,MDWORK+12
        LD DE,MDWORK
        LD BC,4
        LDIR
        LD HL,MDWORK+8
        LD DE,MDWORK+12
        LD BC,4
        LDIR
        LD HL,MDWORK+4
        LD DE,MDWORK+8
        LD BC,4
        LDIR
        LD HL,MDTEMP
        LD DE,MDWORK+4
        LD BC,4
        LDIR
        LD A,(MDOP)
        INC A
        LD (MDOP),A
        CP 64
        JP NZ,MDSTEP
        LD HL,CVALUES
        LD DE,MDWORK
        CALL MDADD
        CALL MDADD
        CALL MDADD
        JP MDADD
; HL destination word += DE source word, advance both by four. Modulo 2^32.
MDADD:
        LD B,4
        OR A
MDADDB:
        LD A,(DE)
        ADC A,(HL)
        LD (HL),A
        INC HL
        INC DE
        DJNZ MDADDB
        RET
MDINITIAL: DB 001H,023H,045H,067H,089H,0ABH,0CDH,0EFH
        DB 0FEH,0DCH,0BAH,098H,076H,054H,032H,010H
; @md5-schedule@
CVALUES: DS 16
MDWORK: DS 16
MDTEMP: DS 4
MDLENGTH: DS 8
MDFINLEN: DS 8
MDBLOCK: DS 64
MDPOS: DB 0
MDOP: DB 0
MDROTATE: DB 0
MDTPTR: DW 0
