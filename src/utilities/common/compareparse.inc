; Tokenize the bounded tail once. Exact query precedence precedes all services.
TOKENIZE:
        LD HL,0081H
        LD DE,TAIL
        LD A,(0080H)
        AND 127
        LD C,A
        LD B,0
        OR A
        JR Z,TOKEMPTY
        LDIR
TOKEMPTY:
        XOR A
        LD (DE),A
        LD HL,TAIL
        LD DE,TOKENS
TOKNEXT:
        LD A,(HL)
        OR A
        RET Z
        CP ' '
        JR Z,TOKSPACE
        CP 9
        JR Z,TOKSPACE
        LD A,L
        LD (DE),A
        INC DE
        LD A,H
        LD (DE),A
        INC DE
        LD A,(NTOK)
        INC A
        LD (NTOK),A
TOKWORD:
        LD A,(HL)
        OR A
        RET Z
        CP ' '
        JR Z,TOKSPACE
        CP 9
        JR Z,TOKSPACE
        CALL UPPER
        LD (HL),A
        INC HL
        JR TOKWORD
TOKSPACE:
        LD (HL),0
        INC HL
        JR TOKNEXT
; HL query; Z if any exact token matches. No filesystem access.
QUERY:
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        EX DE,HL
        LD IX,TOKENS
        LD A,(NTOK)
        LD B,A
        OR A
        JR Z,QNO
QLOOP:
        LD L,(IX+0)
        LD H,(IX+1)
        CALL EQZ
        JR Z,QDONE
        INC IX
        INC IX
        DJNZ QLOOP
QNO:
        LD A,1
        OR A
QDONE:
        POP IX
        POP HL
        POP DE
        POP BC
        RET
EQZ:
        PUSH HL
        PUSH DE
EQLOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,EQDONE
        OR A
        JR Z,EQDONE
        INC DE
        INC HL
        JR EQLOOP
EQDONE:
        POP DE
        POP HL
        RET
; Prefix match, advancing HL only on success. DE is zero-terminated prefix.
PREFIX:
        PUSH HL
        PUSH DE
PRELOOP:
        LD A,(DE)
        OR A
        JR Z,PREOK
        CP (HL)
        JR NZ,PREFAIL
        INC HL
        INC DE
        JR PRELOOP
PREOK:
        POP DE
        POP BC
        XOR A
        RET
PREFAIL:
        POP DE
        POP HL
        LD A,1
        OR A
        RET
PARSE:
        LD HL,TOKENS
        LD (SCAN),HL
        LD A,(NTOK)
        LD B,A
        OR A
        JP Z,NEEDFILES
PARSELOOP:
        PUSH BC
        LD HL,(SCAN)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD (SCAN),HL
        EX DE,HL
        LD (TOKEN),HL
        CALL PARSETOKEN
        POP BC
        JP C,BADTOKEN
        DJNZ PARSELOOP
        LD A,(FILECOUNT)
        CP 2
        JP NZ,NEEDFILES
        LD A,(MODE)
        OR A
        JR Z,PARSECOMPACT
        LD A,(COUNTSET)
        OR A
        JP NZ,BADCOUNT
        LD A,(ALLSET)
        OR A
        JP NZ,BADALL
PARSECOMPACT:
        LD A,(COMPACT)
        OR A
        JR Z,PARSEPAGE
        LD A,(MODE)
        CP 1
        JP NZ,BAD40
PARSEPAGE:
        LD A,(MODE)
        CP 2
        JR NZ,PARSEALL
        LD A,(PAGED)
        OR A
        JP NZ,BADPAGE
PARSEALL:
        LD A,(COUNTSET)
        OR A
        JR Z,PARSEOFFSETS
        LD A,(ALLSET)
        OR A
        JP NZ,BADALL
PARSEOFFSETS:
        LD A,(FROM2SET)
        OR A
        JR NZ,PARSEOK
        LD HL,START1
        LD DE,START2
        CALL COPY32
PARSEOK:
        OR A
        RET
BADCOUNT:
        LD HL,(COUNTTOK)
        JR BADPOINT
BADALL:
        LD HL,(ALLTOK)
        JR BADPOINT
BAD40:
        LD HL,(NARROWTK)
        JR BADPOINT
BADPAGE:
        LD HL,(PAGETOK)
BADPOINT:
        LD (TOKEN),HL
BADTOKEN:
        LD HL,BADMSG
        CALL TEXT
        LD HL,(TOKEN)
        CALL TEXT
        CALL LINE
        SCF
        RET
NEEDFILES:
        LD HL,NEEDMSG
        CALL TEXT
        CALL LINE
        SCF
        RET
PARSETOKEN:
        LD A,(HL)
        CP '/'
        JP NZ,PARSEFILE
        LD DE,OPLIST
        CALL EQZ
        LD A,0
        JP Z,SETMODE
        LD DE,OPSIDE
        CALL EQZ
        LD A,1
        JP Z,SETMODE
        LD DE,OPSUM
        CALL EQZ
        LD A,2
        JP Z,SETMODE
        LD DE,OPSUMMARY
        CALL EQZ
        LD A,2
        JP Z,SETMODE
        LD DE,OPALL
        CALL EQZ
        JR Z,SETALL
        LD DE,OPPAGE
        CALL EQZ
        JR Z,SETPAGE
        LD DE,OP40
        CALL EQZ
        JR Z,SET40
        LD DE,OPFROM
        CALL PREFIX
        JR Z,SETFROM
        LD DE,OPFROM2
        CALL PREFIX
        JR Z,SETFROM2
        LD DE,OPLEN
        CALL PREFIX
        JR Z,SETLEN
        LD DE,OPCOUNT
        CALL PREFIX
        JP Z,SETCOUNT
        SCF
        RET
SETMODE:
        LD B,A
        LD A,(MODESET)
        OR A
        JR Z,MODEOK
        LD A,(MODE)
        CP B
        JR NZ,PARSEFAIL
MODEOK:
        LD A,B
        LD (MODE),A
        LD A,1
        LD (MODESET),A
        OR A
        RET
PARSEFAIL:
        SCF
        RET
SETALL:
        LD HL,(TOKEN)
        LD (ALLTOK),HL
        LD A,1
        LD (ALLSET),A
        OR A
        RET
SETPAGE:
        LD HL,(TOKEN)
        LD (PAGETOK),HL
        LD A,1
        LD (PAGED),A
        OR A
        RET
SET40:
        LD HL,(TOKEN)
        LD (NARROWTK),HL
        LD A,1
        LD (COMPACT),A
        LD A,4
        LD (WIDTH),A
        OR A
        RET
SETFROM:
        CALL PARSEHEX
        RET C
        LD DE,START1
        LD A,1
        LD (FROMSET),A
        JR SETVALUE
SETFROM2:
        CALL PARSEHEX
        RET C
        LD DE,START2
        LD A,1
        LD (FROM2SET),A
        JR SETVALUE
SETLEN:
        CALL PARSEHEX
        RET C
        LD DE,LENGTH
        LD A,1
        LD (LENSET),A
SETVALUE:
        LD HL,NVAL
        CALL COPY32
        OR A
        RET
SETCOUNT:
        LD HL,(TOKEN)
        LD (COUNTTOK),HL
        LD DE,OPCOUNT
        CALL PREFIX
        CALL PARSEDEC
        RET C
        LD A,(NVAL+2)
        LD B,A
        LD A,(NVAL+3)
        OR B
        JR NZ,PARSEFAIL
        LD HL,(NVAL)
        LD A,H
        OR L
        JR Z,PARSEFAIL
        LD (LIMIT),HL
        LD A,1
        LD (COUNTSET),A
        OR A
        RET
; 1..8 hexadecimal digits, with optional terminal H. Never truncate.
PARSEHEX:
        PUSH HL
        LD HL,NVAL
        CALL ZERO32
        POP HL
        LD B,0
HEXLOOP:
        LD A,(HL)
        OR A
        JR Z,HEXEND
        CP 'H'
        JR Z,HEXSUFFIX
        SUB '0'
        JP C,PARSEFAIL
        CP 10
        JR C,HEXDIGITOK
        SUB 7
        CP 10
        JP C,PARSEFAIL
        CP 16
        JP NC,PARSEFAIL
HEXDIGITOK:
        LD C,A
        INC B
        LD A,B
        CP 9
        JP NC,PARSEFAIL
        PUSH HL
        PUSH BC
        LD HL,NVAL
        LD B,4
HEXSHIFT:
        SLA (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        LD HL,NVAL
        DJNZ HEXSHIFT
        POP BC
        LD A,(NVAL)
        OR C
        LD (NVAL),A
        POP HL
        INC HL
        JR HEXLOOP
HEXSUFFIX:
        INC HL
        LD A,(HL)
        OR A
        JP NZ,PARSEFAIL
HEXEND:
        LD A,B
        OR A
        JP Z,PARSEFAIL
        RET
; Accumulate decimal in 32 bits, checking every multiply and addition.
PARSEDEC:
        PUSH HL
        LD HL,NVAL
        CALL ZERO32
        POP HL
        LD A,(HL)
        OR A
        JP Z,PARSEFAIL
DECLOOP:
        LD A,(HL)
        OR A
        RET Z
        SUB '0'
        JP C,PARSEFAIL
        CP 10
        JP NC,PARSEFAIL
        PUSH HL
        PUSH AF
        LD HL,NVAL
        LD DE,NOLD
        CALL COPY32
        CALL ZERO32
        LD B,10
DECMULT:
        LD HL,NOLD
        LD DE,NVAL
        CALL ADD32
        JR C,DECBAD
        DJNZ DECMULT
        POP AF
        LD HL,NVAL
        LD B,A
        OR A
        JR Z,DECNEXT
DECADD:
        CALL INC32
        DJNZ DECADD
        ; Input constrained to 16 bits after each digit; catches huge tails.
DECNEXT:
        LD A,(NVAL+2)
        LD B,A
        LD A,(NVAL+3)
        OR B
        JR NZ,DECBADPOP
        POP HL
        INC HL
        JR DECLOOP
DECBAD:
        POP AF
DECBADPOP:
        POP HL
        SCF
        RET
PARSEFILE:
        LD A,(FILECOUNT)
        CP 2
        JP NC,PARSEFAIL
        LD IX,FILE1
        OR A
        JR Z,FILEDESC
        LD IX,FILE2
FILEDESC:
        LD (IX+FN),L
        LD (IX+FN+1),H
        PUSH HL
        LD B,0
FILELEN:
        LD A,(HL)
        OR A
        JR Z,FILELENEND
        CP '['
        JR Z,FILEBADPOP
        CP ']'
        JR Z,FILEBADPOP
        INC B
        INC HL
        JR FILELEN
FILELENEND:
        POP HL
        LD A,(ODRIVE)
        LD D,A
        LD A,(OUSER)
        LD E,A
        CALL DU_PARSE
        RET C
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JR C,FILEBADTWO
        LD A,E
        LD (IX+FU),A
        LD A,D
        INC A
        LD (IX+0),A
        CALL DU_NEXT
        JR NC,FILEBADTWO
        POP BC
        POP HL
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE
        JR C,FILEBADTWO
        POP BC
        POP HL
        PUSH HL
        PUSH IX
        POP HL
        INC HL
        LD B,11
        LD A,' '
FILEFILL:
        LD (HL),A
        INC HL
        DJNZ FILEFILL
        PUSH IX
        POP DE
        INC DE
        POP HL
FILENAME:
        LD A,(HL)
        OR A
        JR Z,FILEGOOD
        CP '.'
        JR Z,FILEEXT
        LD (DE),A
        INC DE
        INC HL
        JR FILENAME
FILEEXT:
        PUSH IX
        POP DE
        PUSH HL
        LD HL,9
        ADD HL,DE
        EX DE,HL
        POP HL
        INC HL
        JR FILENAME
FILEGOOD:
        LD A,(FILECOUNT)
        INC A
        LD (FILECOUNT),A
        OR A
        RET
FILEBADTWO:
        POP BC
FILEBADPOP:
        POP HL
        SCF
        RET
