; Pure pre-operation queries, option validation and transient-only hints.
; HL/B is the untouched argument span. Preserve it for ordinary resident parsing.
RH_VERSION:
        PUSH HL
        LD HL,BC_COMMAND
        ADD HL,DE
        EX DE,HL
        POP HL
        LD (RH_ACTIVE),DE          ; rebuilt with this CPX; never persistent state
        CALL UH_QUERY             ; exact /H or /HELP takes precedence
        RET C
        CALL UV_QUERY
        RET C
        ; Fall through only after standalone /VER handling.
RH_CHECK:
        PUSH BC
        PUSH DE
        PUSH IX
        PUSH HL
        LD HL,(BC_CMDPTR)
        LD D,(HL)                 ; canonical command's first letter
        LD A,D
        AND 0DFH
        LD D,A
        POP HL
        PUSH HL
RH_SCAN:
        LD A,B
        OR A
        JR Z,RH_NONE
        LD A,(HL)
        CP ' '
        JR Z,RH_SPACE
        CP '/'
        JR NZ,RH_SKIP
        PUSH BC
        PUSH HL
        INC HL
        DEC B
        LD C,0
RH_LEN:
        LD A,B
        OR A
        JR Z,RH_TSTART
        LD A,(HL)
        CP ' '
        JR Z,RH_TSTART
        INC C
        INC HL
        DJNZ RH_LEN
RH_TSTART:
        POP HL
        PUSH HL
        INC HL
        LD IX,RH_OPTABLE
RH_ENTRY:
        LD A,(IX+0)
        OR A
        JR Z,RH_MISS
        CP D
        JR NZ,RH_NEXT
        LD A,(IX+1)
        CP C
        JR NZ,RH_NEXT
        PUSH HL
        PUSH IX
        INC IX
        INC IX
        LD E,C
RH_COMPARE:
        LD A,(IX+0)
        CP (HL)
        JR NZ,RH_DIFFERENT
        INC IX
        INC HL
        DEC E
        JR NZ,RH_COMPARE
        POP IX
        POP HL
        POP HL
        POP BC
        JR RH_HINT
RH_DIFFERENT:
        POP IX
        POP HL
RH_NEXT:
        LD A,(IX+1)
        ADD A,2
        LD E,A
RH_ADV:
        INC IX
        DEC E
        JR NZ,RH_ADV
        JR RH_ENTRY
RH_MISS:
        CALL RH_OPTOK
        JR C,RH_BADPOP
        POP HL
        POP BC
RH_SKIP:
        LD A,(HL)
        CP ' '
        JR Z,RH_SPACE
        INC HL
        DJNZ RH_SKIP
        JR RH_NONE
RH_SPACE:
        INC HL
        DJNZ RH_SCAN
RH_NONE:
        POP HL
        POP IX
        POP DE
        POP BC
        LD A,B
        OR A
        RET NZ
        ; Empty DIR, CLS and VER are operations; other commands need operands.
        ; DE still points to the canonical resident identification string.
        LD A,(DE)
        CP 'D'
        RET Z
        CP 'V'
        RET Z
        CP 'C'
        JR NZ,RH_REJECT
        INC DE
        LD A,(DE)
        DEC DE
        CP 'L'
        RET Z
        JR RH_REJECT
RH_BADPOP:
        POP HL
        POP BC
        POP HL
        POP IX
        POP DE
        POP BC
RH_REJECT:
        CALL RH_SHORT
        SCF
        RET
RH_HINT:
        LD E,13
        LD C,2
        CALL 00005H
        LD E,10
        LD C,2
        CALL 00005H
        CALL RH_NAME
        LD DE,RH_MSG
        LD C,9
        CALL 00005H
        CALL RH_NAME
        LD DE,RH_SUFFIX
        LD C,9
        CALL 00005H
        POP HL
        POP IX
        POP DE
        POP BC
        SCF
        RET
RH_NAME:
        LD HL,(BC_CMDPTR)
        LD A,(BC_KEYLEN)
        LD B,A
RH_NLOOP:
        LD E,(HL)
        LD C,2
        PUSH BC
        PUSH HL
        CALL 00005H
        POP HL
        POP BC
        INC HL
        DJNZ RH_NLOOP
        RET
RH_MSG: DB ': Use :','$'
RH_SUFFIX: DB '. Additional transient features.',13,10,'$'
; Only these one-letter options belong to resident operations. Recognized
; transient-only options have already selected RH_HINT. CF means invalid.
RH_OPTOK:
        LD A,C
        CP 1
        JR NZ,RH_OPBAD
        LD A,(HL)
        AND 0DFH
        CP 'P'
        JR NZ,RH_COPT
        LD A,D
        CP 'T'
        JR Z,RH_OPGOOD
        JR RH_OPBAD
RH_COPT:
        CP 'O'
        JR NZ,RH_VOPT
        LD A,D
        CP 'C'
        JR Z,RH_OPGOOD
        CP 'M'
        JR Z,RH_OPGOOD
        JR RH_OPBAD
RH_VOPT:
        CP 'V'
        JR NZ,RH_OPBAD
        LD A,D
        CP 'V'
        JR NZ,RH_OPBAD
RH_OPGOOD:
        OR A
        RET
RH_OPBAD:
        SCF
        RET
RH_OPTABLE:
        DB 'V',6,'BANNER'
        DB 'D',7,'WHEREIS'
        DB 'D',1,'A'
        DB 'D',1,'P'
        DB 'D',1,'Z'
        DB 'D',3,'Z=K'
        DB 'D',3,'Z=S'
        DB 'D',3,'Z=E'
        DB 'D',3,'C=1'
        DB 'D',3,'C=2'
        DB 'D',3,'C=4'
        DB 'D',3,'S=N'
        DB 'D',4,'S=N+'
        DB 'D',4,'S=N-'
        DB 'D',3,'S=T'
        DB 'D',4,'S=T+'
        DB 'D',4,'S=T-'
        DB 'D',3,'S=Z'
        DB 'D',4,'S=Z+'
        DB 'D',4,'S=Z-'
        DB 'D',3,'S=U'
        DB 'E',1,'Y'
        DB 'E',1,'Q'
        DB 'E',1,'C'
        DB 'E',1,'R'
        DB 'E',1,'D'
        DB 'T',1,'7'
        DB 'T',1,'T'
        DB 'T',3,'CTL'
        DB 'R',1,'C'
        DB 'R',1,'Y'
        DB 'R',1,'N'
        DB 'R',3,'DRY'
        DB 'R',1,'P'
        DB 'R',1,'Q'
        DB 'R',2,'QQ'
        DB 'C',1,'B'
        DB 'C',1,'V'
        DB 'C',6,'BACKUP'
        DB 0
