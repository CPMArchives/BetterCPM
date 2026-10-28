; One digest and one outcome per selected file, regardless of candidate count.
CHECKFOU:
        LD A,(MATCHENT)
        OR A
        JR Z,CHECKNOM
        LD HL,VERIFIED
        CALL INC32
        CALL NEWLINE
        CALL PUTNAME
        LD HL,MSGMATCH
        CALL PUTS
        CALL SPACE2
        LD HL,CVALUES
        CALL MDDIGEST
        CALL ENDLINE
        LD A,(DIFFENTR)
        OR A
        RET Z
        LD HL,MSGALTER
        JP TEXT
CHECKNOM:
        LD HL,FAILED
        CALL INC32
        LD HL,MSGCRCMI
        JP CHECKDIA
; MD5 lists have one fixed default name, no wildcard discovery tiers.
DISCOVER:
        LD HL,REFFCB
        LD BC,36
        CALL ZERO
        LD A,(REFSET)
        OR A
        LD HL,REFNAME
        JR NZ,MDREFCOPY
        LD HL,MDDEFAULT
        LD DE,REFFCB+1
        LD BC,11
        LDIR
        JR MDREFOPEN
MDREFCOPY:
        LD DE,REFFCB
        LD BC,36
        LDIR
MDREFOPEN:
        LD DE,REFFCB
        LD C,15
        CALL BDOS
        CP 255
        JR Z,MDREFMISS
        LD C,16
        CALL BDOS
        CP 255
        JR Z,MDREFERR
        OR A
        RET
MDREFMISS:
        LD HL,MSGNOREF
        JR MDREFBAD
MDREFERR:
        LD HL,MSGLISTE
MDREFBAD:
        CALL TEXT
        LD HL,DUERRORS
        CALL INC32
        SCF
        RET
MDDEFAULT: DB 'MD5SUM  LST'
