COMMAND:
        LD HL,TOKENS
        LD (SCAN),HL
        LD A,(NTOK)
        OR A
        JP Z,BADCOMMAND
        LD B,A
CMDLOOP:
        PUSH BC
        LD HL,(SCAN)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD (SCAN),HL
        EX DE,HL
        LD (TOKEN),HL
        LD DE,OPVERBOSE
        CALL EQZ
        JR NZ,CMDINPUT
        LD A,1
        LD (VERBOSE),A
        JP CMDNEXT
CMDINPUT:
        LD DE,OPINPUT
        CALL PREFIX
        JR NZ,CMDOUTPUT
        LD IX,SCRATCH
        CALL PARSENAME
        LD A,(INOPT)
        OR A
        JR Z,CMDINNEW
        LD HL,SCRATCH
        LD DE,INFILE
        CALL SAMEFILE
        JP NZ,BADCOMMAND
CMDINNEW:
        LD HL,SCRATCH
        LD DE,INFILE
        CALL COPYDESC
        LD A,1
        LD (INSET),A
        LD (INOPT),A
        JP CMDNEXT
CMDOUTPUT:
        LD HL,(TOKEN)
        LD DE,OPOUTPUT
        CALL PREFIX
        JR NZ,CMDPATCH
        LD IX,SCRATCH
        CALL PARSENAME
        LD A,(OUTOPT)
        OR A
        JR Z,CMDOUTNEW
        LD HL,SCRATCH
        LD DE,OUTFILE
        CALL SAMEFILE
        JP NZ,BADCOMMAND
CMDOUTNEW:
        LD HL,SCRATCH
        LD DE,OUTFILE
        CALL COPYDESC
        LD A,1
        LD (OUTSET),A
        LD (OUTOPT),A
        JP CMDNEXT
CMDPATCH:
        LD HL,(TOKEN)
        LD A,(HL)
        CP '/'
        JP Z,BADCOMMAND
        LD A,(PSET)
        OR A
        JP NZ,BADCOMMAND
        LD IX,PATFILE
        CALL PARSENAME
        LD A,1
        LD (PSET),A
CMDNEXT:
        POP BC
        DEC B
        JP NZ,CMDLOOP
        LD A,(PSET)
        OR A
        JP Z,BADCOMMAND
        RET
; HL points to one terminated exact filespec. DU_PARSE/FP_VALIDATE are shared.
PARSENAME:
        PUSH HL
        PUSH IX
        POP HL
        LD BC,184
        CALL ZERO
        POP HL
        PUSH HL
        LD B,0
PNLEN:
        LD A,(HL)
        OR A
        JR Z,PNEND
        CP '['
        JP Z,SYNTAXERROR
        CP ']'
        JP Z,SYNTAXERROR
        CP ','
        JP Z,SYNTAXERROR
        INC B
        INC HL
        JR PNLEN
PNEND:
        POP HL
        LD A,(ODRIVE)
        LD D,A
        LD A,(OUSER)
        LD E,A
        CALL DU_PARSE
        JP C,SYNTAXERROR
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JP C,SYNTAXERROR
        LD A,D
        INC A
        LD (IX+0),A
        LD A,E
        LD (IX+FU),A
        CALL DU_NEXT
        JP NC,SYNTAXERROR
        POP BC
        POP HL
        PUSH HL
        XOR A
        CALL FP_VALIDATE
        JP C,SYNTAXERROR
        POP HL
        PUSH HL
        PUSH IX
        POP HL
        INC HL
        LD B,11
PNFILL:
        LD (HL),' '
        INC HL
        DJNZ PNFILL
        PUSH IX
        POP DE
        INC DE
        POP HL
PNCOPY:
        LD A,(HL)
        OR A
        RET Z
        CP '.'
        JR Z,PNEXT
        CALL UPPER
        LD (DE),A
        INC DE
        INC HL
        JR PNCOPY
PNEXT:
        PUSH HL
        PUSH IX
        POP HL
        LD DE,9
        ADD HL,DE
        EX DE,HL
        POP HL
        INC HL
        JR PNCOPY
COPYDESC:
        LD BC,184
        LDIR
        RET
; Equal identities: drive, user and all 11 normalized FCB name bytes.
SAMEFILE:
        PUSH HL
        PUSH DE
        PUSH BC
        LD BC,FU
        ADD HL,BC
        EX DE,HL
        ADD HL,BC
        LD A,(DE)
        CP (HL)
        JR NZ,SAMEDONE
        LD BC,-FU
        ADD HL,BC
        EX DE,HL
        ADD HL,BC
        LD B,12
SAMELOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,SAMEDONE
        INC DE
        INC HL
        DJNZ SAMELOOP
SAMEDONE:
        POP BC
        POP DE
        POP HL
        RET
PRINTFILE:
        PUSH IX
        LD A,(IX+0)
        ADD A,'A'-1
        CALL PUT
        LD L,(IX+FU)
        LD H,0
        LD (NUMWORK),HL
        XOR A
        LD (NUMWORK+2),A
        LD (NUMWORK+3),A
        LD HL,NUMWORK
        CALL DECIMAL
        LD A,':'
        CALL PUT
        PUSH IX
        POP HL
        INC HL
        LD B,8
PNPRINT:
        LD A,(HL)
        CP ' '
        CALL NZ,PUT
        INC HL
        DJNZ PNPRINT
        LD A,(HL)
        CP ' '
        JR Z,PNPRINTDONE
        LD A,'.'
        CALL PUT
        LD B,3
PNPRTEXT:
        LD A,(HL)
        CP ' '
        CALL NZ,PUT
        INC HL
        DJNZ PNPRTEXT
PNPRINTDONE:
        POP IX
        RET
LOCATION:
        LD HL,LOCTEXT
        CALL TEXT
        LD IX,PATFILE
        CALL PRINTFILE
        LD HL,LINETEXT
        CALL TEXT
        LD HL,LINENO
        CALL DECIMAL
        JP LINE
