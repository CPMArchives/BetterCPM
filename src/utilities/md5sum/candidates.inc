; One MD5 value per reference entry, no size or algorithm selection filtering.
CANDIDAT:
        LD A,(LISTMODE)
        OR A
        RET Z
        CP 2
        JP Z,MISSCAND
        LD HL,ENAME
        LD DE,LASTNAME
        CALL CMPNAME
        RET NZ
        LD A,1
        LD (FOUNDENT),A
        LD (USABLEEN),A
        LD (SIZEENTR),A
        LD A,(LISTMODE)
        CP 3
        RET Z
        LD HL,EVALUES
        LD DE,CVALUES
        LD B,16
MDMATCH:
        LD A,(DE)
        CP (HL)
        JR NZ,CANDDIFF
        INC HL
        INC DE
        DJNZ MDMATCH
        LD A,1
        LD (MATCHENT),A
        RET
CANDDIFF:
        LD A,1
        LD (DIFFENTR),A
        CALL NEWLINE
        LD HL,MSGCAND
        CALL PUTS
        LD HL,LISTLI01
        XOR A
        CALL PUTDEC
        CALL ENDLINE
        CALL NEWLINE
        LD HL,MSGRECVA
        CALL PUTS
        LD HL,EVALUES
        CALL MDDIGEST
        CALL ENDLINE
        CALL NEWLINE
        LD HL,MSGACTVA
        CALL PUTS
        LD HL,CVALUES
        CALL MDDIGEST
        JP ENDLINE
FIELDS:
        CALL SPACE2
        LD HL,CVALUES
        JP MDDIGEST
MSGCAND: DB '  Candidate at line ',0
MSGRECVA: DB '  Recorded: ',0
MSGACTVA: DB '  Actual: ',0
