; Public BDOS can destroy all scratch registers. Only its A result escapes.
BDOS:
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        CALL 5
        POP IX
        POP HL
        POP DE
        POP BC
        RET
ZERO:
        XOR A
ZLOOP:
        LD (HL),A
        INC HL
        DEC BC
        LD A,B
        OR C
        JR Z,ZDONE
        XOR A
        JR ZLOOP
ZDONE:
        RET
COPY4:
        LD BC,4
        LDIR
        RET
INC32:
        LD B,4
INC32B:
        INC (HL)
        JR NZ,INC32OK
        INC HL
        DJNZ INC32B
        LD A,1
        LD (INCOMPLE),A
        SCF
        RET
INC32OK:
        OR A
        RET
CMP4:
        PUSH HL
        PUSH DE
        LD BC,3
        ADD HL,BC
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD B,4
CMP4B:
        LD A,(DE)
        LD C,A
        LD A,(HL)
        CP C
        JR NZ,CMP4END
        DEC HL
        DEC DE
        DJNZ CMP4B
CMP4END:
        POP DE
        POP HL
        RET
; Canonical names, HL vs DE, unsigned lexical comparison.
CMPNAME:
        LD B,11
CMPNAMEB:
        LD A,(DE)
        LD C,A
        LD A,(HL)
        CP C
        RET NZ
        INC HL
        INC DE
        DJNZ CMPNAMEB
        RET
POLL:
        LD A,(CANCEL)
        OR A
        RET NZ
        LD C,11
        CALL BDOS
        OR A
        RET Z
        LD E,255
        LD C,6
        CALL BDOS
        CP 3
        RET NZ
        LD A,1
        LD (CANCEL),A
        LD (INCOMPLE),A
        RET
CHAR:
        PUSH AF
        PUSH BC
        PUSH DE
        LD B,A
        LD A,(NARROW)
        OR A
        JR Z,CHAREMIT
        LD A,B
        CP 13
        JR Z,CHARZERO
        CP 10
        JR Z,CHARZERO
        LD A,(CONSCOL)
        CP 40
        JR C,CHARINC
        LD E,13
        LD C,2
        CALL BDOS
        LD E,10
        CALL BDOS
        XOR A
CHARINC:
        INC A
        LD (CONSCOL),A
        JR CHAREMIT
CHARZERO:
        XOR A
        LD (CONSCOL),A
CHAREMIT:
        LD E,B
        LD C,2
        CALL BDOS
        POP DE
        POP BC
        POP AF
        RET
TEXT:
        LD A,(HL)
        OR A
        RET Z
        CALL CHAR
        INC HL
        JR TEXT
NL:
        LD A,13
        CALL CHAR
        LD A,10
        JP CHAR
DUCONSOL:
        LD A,(DRIVE)
        ADD A,'A'
        CALL CHAR
        LD A,(USER)
        LD B,'0'-1
DUDECTEN:
        INC B
        SUB 10
        JR NC,DUDECTEN
        ADD A,10
        PUSH AF
        LD A,B
        CP '0'
        CALL NZ,CHAR
        POP AF
        ADD A,'0'
        CALL CHAR
        LD A,':'
        JP CHAR
PRINTNAM:
        LD B,8
PRINTBAS:
        LD A,(HL)
        CP ' '
        CALL NZ,CHAR
        INC HL
        DJNZ PRINTBAS
        LD A,(HL)
        CP ' '
        RET Z
        LD A,'.'
        CALL CHAR
        LD B,3
PRINTEXT:
        LD A,(HL)
        CP ' '
        CALL NZ,CHAR
        INC HL
        DJNZ PRINTEXT
        RET
NEWLINE:
        LD HL,LINE
        LD (LINEPTR),HL
        RET
PUT:
        PUSH HL
        LD HL,(LINEPTR)
        LD (HL),A
        INC HL
        LD (LINEPTR),HL
        POP HL
        RET
PUTS:
        LD A,(HL)
        OR A
        RET Z
        CALL PUT
        INC HL
        JR PUTS
SPACE2:
        LD A,' '
        CALL PUT
        JP PUT
HEXBYTE:
        PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL HEXDIGIT
        POP AF
HEXDIGIT:
        AND 15
        ADD A,'0'
        CP '9'+1
        JR C,HEXPUT
        ADD A,7
HEXPUT:
        JP PUT
; HL little endian value, B number of bytes. Write conventional high first.
HEXVALUE:
        PUSH BC
        LD C,B
        LD B,0
        ADD HL,BC
        POP BC
HEXLOOP:
        DEC HL
        LD A,(HL)
        CALL HEXBYTE
        DJNZ HEXLOOP
        RET
; Decimal 32-bit HL -> NUMBUF, NUMPTR and A=count. Bounded long division.
DECIMAL:
        LD DE,NUMCOPY
        CALL COPY4
        LD HL,NUMBUF+10
        LD (HL),0
        LD (NUMPTR),HL
DECAGAIN:
        LD HL,NUMCOPY+3
        LD B,4
        LD DE,0
DECBYTE:
        LD E,(HL)
        LD C,0
DECDIV:
        LD A,D
        OR A
        JR NZ,DECSUB
        LD A,E
        CP 10
        JR C,DECREM
DECSUB:
        LD A,E
        SUB 10
        LD E,A
        LD A,D
        SBC A,0
        LD D,A
        INC C
        JR DECDIV
DECREM:
        LD (HL),C
        LD D,E
        DEC HL
        DJNZ DECBYTE
        LD HL,(NUMPTR)
        DEC HL
        LD A,D
        ADD A,'0'
        LD (HL),A
        LD (NUMPTR),HL
        LD HL,NUMCOPY
        LD B,4
        XOR A
DECNZ:
        OR (HL)
        INC HL
        DJNZ DECNZ
        JR NZ,DECAGAIN
        LD HL,NUMBUF+10
        LD DE,(NUMPTR)
        OR A
        SBC HL,DE
        LD A,L
        RET
; HL32 value, A minimum width -> append right aligned decimal.
PUTDEC:
        LD (NUMWIDTH),A
        CALL DECIMAL
        LD B,A
        LD A,(NUMWIDTH)
        SUB B
        JR C,PUTDECNU
        JR Z,PUTDECNU
        LD B,A
PUTDECPA:
        LD A,' '
        CALL PUT
        DJNZ PUTDECPA
PUTDECNU:
        LD HL,(NUMPTR)
        JP PUTS
ENDLINE:
        XOR A
        CALL PUT
        LD HL,LINE
        CALL TEXT
        JP NL
MSGCOMMA: DB 'CRCKSUM: invalid command; use /HELP',13,10,0
MSGREAD: DB ' READ ERROR',0
MSGDONE: DB 'Files calculated: ',0
TOTALS:
        XOR A
        CALL SUMMARY
        LD A,(CANCEL)
        OR A
        LD HL,MSGCANCE
        JP NZ,TEXT
        LD A,(CHECK)
        OR A
        RET Z
        LD HL,VERIFIED
        LD B,4
        XOR A
TOTALVN:
        OR (HL)
        INC HL
        DJNZ TOTALVN
        JR Z,TOTALBAD
        LD HL,FAILED
        LD B,24
        XOR A
TOTALFN:
        OR (HL)
        INC HL
        DJNZ TOTALFN
        JR NZ,TOTALBAD
        LD A,(INCOMPLE)
        OR A
        JR NZ,TOTALBAD
        LD HL,MSGOK
        JP TEXT
TOTALBAD:
        LD HL,MSGNOTOK
        JP TEXT
; A=0 overall,1 DU delta. Labels and count order remain a single table.
SUMMARY:
        LD (SUMMODE),A
        LD HL,MSGOVER
        OR A
        JR Z,SUMTITLE
        LD HL,MSGDUTOT
SUMTITLE:
        CALL TEXT
        LD HL,COUNTERS
        LD (SUMCOUNT),HL
        LD HL,SNAPSHOT
        LD (SUMSNAP),HL
        LD IX,SUMTABLE
        LD A,12
        LD (SUMLEFT),A
SUMNEXT:
        LD L,(IX+0)
        LD H,(IX+1)
        CALL TEXT
        LD HL,(SUMCOUNT)
        LD A,(SUMMODE)
        OR A
        JR Z,SUMVALUE
        LD DE,(SUMSNAP)
        LD B,4
        PUSH IX
        LD IX,NUMVALUE
        OR A
SUMSUB:
        LD A,(DE)
        LD C,A
        LD A,(HL)
        SBC A,C
        LD (IX+0),A
        INC HL
        INC DE
        INC IX
        DJNZ SUMSUB
        POP IX
        LD HL,NUMVALUE
SUMVALUE:
        CALL DECIMAL
        LD HL,(NUMPTR)
        CALL TEXT
        CALL NL
        LD HL,(SUMCOUNT)
        LD DE,4
        ADD HL,DE
        LD (SUMCOUNT),HL
        LD HL,(SUMSNAP)
        ADD HL,DE
        LD (SUMSNAP),HL
        INC IX
        INC IX
        LD A,(SUMLEFT)
        DEC A
        LD (SUMLEFT),A
        JR NZ,SUMNEXT
        RET
MSGOVER: DB 'Overall totals:',13,10,0
MSGDUTOT: DB 'DU totals:',13,10,0
SUMTABLE:
        DW MSGDONE,SMVER,SMFAIL,SMMISS,SMUNLIST,SMSKIP,SMLIST,SMDU,SMOUT,SMDCL,SMERR,SMENTRY
SMVER: DB 'Files verified: ',0
SMFAIL: DB 'Files failed: ',0
SMMISS: DB 'Listed files missing: ',0
SMUNLIST: DB 'Files not listed: ',0
SMSKIP: DB 'Files skipped: ',0
SMLIST: DB 'Malformed/list errors: ',0
SMDU: DB 'DU/reference failures: ',0
SMOUT: DB 'Lists completed: ',0
SMDCL: DB 'Lists declined: ',0
SMERR: DB 'Lists failed: ',0
SMENTRY: DB 'Entries skipped: ',0
MSGOK: DB 'Verification complete: all selected files match',13,10,0
MSGNOTOK: DB 'Verification incomplete or failed',13,10,0
SUMMODE: DB 0
SUMLEFT: DB 0
SUMCOUNT: DW 0
SUMSNAP: DW 0
MSGCANCE: DB 'CRCKSUM: cancelled; operation incomplete',13,10,0
