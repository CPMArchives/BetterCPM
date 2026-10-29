; Reference traversal is intentionally replayed for each actual file. It bounds
; storage independently of both the directory and reference-list lengths.
CHECKDU:
        XOR A
        LD (REFREADY),A
        LD (REFFAIL),A
        CALL DISCOVER
        JP C,DUNEXT
        LD A,1
        LD (REFREADY),A
        LD HL,MSGREFER
        CALL TEXT
        CALL DUCONSOL
        LD HL,REFFCB+1
        LD B,11
REFPRINT:
        LD A,(HL)
        CALL CHAR
        INC HL
        DJNZ REFPRINT
        CALL NL
        XOR A
        LD (LISTMODE),A
        CALL LISTSCAN
        LD A,(REFFAIL)
        OR A
        JP NZ,DUNEXT
        LD HL,LASTNAME
        LD BC,11
        CALL ZERO
CHECKFIL:
        CALL POLL
        LD A,(CANCEL)
        OR A
        JP NZ,RUNEND
        CALL NEXTFILE
        JR C,CHECKMIS
        ; Reject impossible sizes before opening/reading the target data.
        CALL MAKEFCB
        LD DE,FILEFCB
        LD C,35
        CALL BDOS
        CALL QUERYSIZ
        LD HL,EXPECTED
        LD DE,RECS
        CALL COPY4
        LD A,3
        LD (LISTMODE),A
        CALL CHECKCLR
        CALL LISTSCAN
        LD A,(SIZEENTR)
        OR A
        JR Z,CHECKRPT
        CALL SCANFILE
        JR C,CHECKREA
        LD HL,FILES
        CALL INC32
        LD A,1
        LD (LISTMODE),A
        CALL CHECKCLR
        CALL LISTSCAN
CHECKRPT:
        CALL CHECKRES
        JR CHECKFIL
CHECKCLR:
        XOR A
        LD (FOUNDENT),A
        LD (MATCHENT),A
        LD (USABLEEN),A
        LD (SIZEENTR),A
        RET
CHECKREA:
        CALL FILEDIAG
        JR CHECKFIL
CHECKMIS:
        ; Iterate reference names alphabetically, so duplicate entries count once.
        LD HL,MISSLAST
        LD BC,11
        CALL ZERO
MISSPASS:
        XOR A
        LD (MISSFOUN),A
        LD A,2
        LD (LISTMODE),A
        CALL LISTSCAN
        LD A,(MISSFOUN)
        OR A
        JP Z,DUNEXT
        LD HL,MISSBEST
        LD DE,MISSLAST
        LD BC,11
        LDIR
        LD HL,MISSFCB
        LD BC,36
        CALL ZERO
        LD HL,MISSBEST
        LD DE,MISSFCB+1
        LD BC,11
        LDIR
        LD DE,MISSFCB
        LD C,15
        CALL BDOS
        CP 255
        JR Z,MISSINGF
        LD C,16
        CALL BDOS
        JR MISSPASS
MISSINGF:
        LD HL,MISSING
        CALL INC32
        LD HL,MISSBEST
        LD DE,LASTNAME
        LD BC,11
        LDIR
        LD HL,MSGNOTFO
        CALL CHECKDIA
        JR MISSPASS
CHECKRES:
        LD A,(FOUNDENT)
        OR A
        JR NZ,CHECKFOU
        LD HL,UNLISTED
        CALL INC32
        LD HL,MSGNOTLI
        JP CHECKDIA
CHECKFOU:
        LD A,(MATCHENT)
        OR A
        JR Z,CHECKNOM
        LD HL,VERIFIED
        CALL INC32
        LD HL,LASTNAME
        CALL PRINTNAM
        LD HL,MSGMATCH
        CALL TEXT
        LD A,(MATCHMAS)
        LD B,8
        LD C,0
MATCHCNT:
        RRCA
        JR NC,MCHNEXT
        INC C
MCHNEXT:
        DJNZ MATCHCNT
        LD A,C
        ADD A,'0'
        CALL CHAR
        LD HL,MCHEND
        CALL TEXT
        CALL NL
        LD A,(DIFFENTR)
        OR A
        RET Z
        LD HL,MSGALTER
        JP TEXT
CHECKNOM:
        LD A,(USABLEEN)
        OR A
        JR NZ,CHECKM01
        LD HL,SKIPPED
        CALL INC32
        LD HL,MSGSKIPP
        JP CHECKDIA
CHECKM01:
        LD HL,FAILED
        CALL INC32
        LD A,(SIZEENTR)
        OR A
        LD HL,MSGSIZEM
        JR Z,CHECKDIA
        LD HL,MSGCRCMI
CHECKDIA:
        PUSH HL
        CALL NEWLINE
        CALL PUTNAME
        POP HL
        CALL PUTS
        JP ENDLINE
; Discovery scans only the current tier and never falls through ambiguity.
DISCOVER:
        LD A,(REFSET)
        OR A
        JR Z,DISCDEFA
        LD HL,REFNAME
        LD DE,REFFCB
        LD BC,36
        LDIR
        OR A
        RET
DISCDEFA:
        LD IX,DISCOV01
DISCTIER:
        LD HL,DIRFCB
        LD BC,36
        CALL ZERO
        LD A,(DRIVE)
        INC A
        LD (DIRFCB),A
        PUSH IX
        POP HL
        LD DE,DIRFCB+1
        LD BC,11
        LDIR
        XOR A
        LD (DISCCOUN),A
        LD DE,DIRDMA
        LD C,26
        CALL BDOS
        LD DE,DIRFCB
        LD C,17
        CALL BDOS
DISCENT:
        CP 255
        JR Z,DISCTI01
        CP 4
        JP NC,DISCFAIL
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD L,A
        LD H,0
        LD DE,DIRDMA+1
        ADD HL,DE
        LD DE,DISCCAND
        LD B,11
DISCCOPY:
        LD A,(HL)
        AND 127
        LD (DE),A
        INC HL
        INC DE
        DJNZ DISCCOPY
        LD A,(DISCCOUN)
        OR A
        JR Z,DISCFIRS
        LD HL,DISCCAND
        LD DE,REFFCB+1
        CALL CMPNAME
        JR Z,DISCNEXT
        ; More than one distinct candidate, irrespective of extent entries.
        LD A,2
        LD (DISCCOUN),A
        JR DISCNEXT
DISCFIRS:
        LD HL,REFFCB
        LD BC,36
        CALL ZERO
        LD HL,DISCCAND
        LD DE,REFFCB+1
        LD BC,11
        LDIR
        LD A,1
        LD (DISCCOUN),A
DISCNEXT:
        LD DE,DIRFCB
        LD C,18
        CALL BDOS
        JR DISCENT
DISCTI01:
        LD A,(DISCCOUN)
        CP 1
        RET Z
        CP 2
        LD HL,MSGAMBIG
        JR Z,DISCAMB
        LD DE,11
        ADD IX,DE
        LD A,(IX+0)
        OR A
        JP NZ,DISCTIER
        LD HL,MSGNOREF
        JR DISCERRO
DISCFAIL:
        LD HL,MSGLISTE
DISCERRO:
        CALL TEXT
DISCERCT:
        LD HL,DUERRORS
        CALL INC32
        SCF
        RET
DISCAMB:
        CALL TEXT
        ; Reuse sorted directory replay with this tier's pattern. The DU is
        ; abandoned after ambiguity, so its operand map need not be restored.
        LD HL,DIRFCB+1
        LD DE,ACTIVE
        LD BC,11
        LDIR
        LD A,255
        LD (DE),A
        LD A,1
        LD (ACTIVECO),A
        LD HL,LASTNAME
        LD BC,11
        CALL ZERO
DISCAMNX:
        CALL NEXTFILE
        JR C,DISCERCT
        CALL DUCONSOL
        LD HL,LASTNAME
        CALL PRINTNAM
        CALL NL
        JR DISCAMNX
EXREFERE:
        LD A,(CHECK)
        OR A
        RET Z
        LD A,(REFREADY)
        OR A
        RET Z
        LD HL,CANDNAME
        LD DE,REFFCB+1
        CALL CMPNAME
        JR NZ,EXREFNO
        ; A literal active operand can explicitly request the reference itself.
        LD IX,ACTIVE
        LD A,(ACTIVECO)
        LD (SELLEFT),A
EXREFLOO:
        LD HL,CANDNAME
        LD B,11
        PUSH IX
EXREFCHA:
        LD A,(IX+0)
        CP (HL)
        JR NZ,EXREFNEX
        INC IX
        INC HL
        DJNZ EXREFCHA
        POP IX
EXREFNO:
        XOR A
        RET
EXREFNEX:
        POP IX
        LD DE,12
        ADD IX,DE
        LD A,(SELLEFT)
        DEC A
        LD (SELLEFT),A
        JR NZ,EXREFLOO
        LD A,1
        OR A
        RET
LISTSCAN:
        ; Keep reference name only; open state never leaks between replays.
        LD HL,REFFCB
        LD DE,LISTFCB
        LD BC,12
        LDIR
        LD HL,LISTFCB+12
        LD BC,24
        CALL ZERO
        LD DE,LISTFCB
        LD C,15
        CALL BDOS
        CP 255
        JP Z,REFOPENERR
        XOR A
        LD (LISTFORM),A
        LD (LISTPEND),A
        LD (LISTEOF),A
        LD (LISTANY),A
        LD (CATCRC),A
        LD (CATORDER),A
        LD (DIFFENTR),A
        LD HL,LISTLI01
        LD BC,4
        CALL ZERO
        LD A,128
        LD (LISTPOS),A
LISTNEXT:
        CALL POLL
        LD A,(CANCEL)
        OR A
        JR NZ,LISTFINI
        CALL READLINE
        JR C,LISTFINI
        LD A,(LLTOOLON)
        OR A
        JR NZ,LISTNEXT
        LD HL,LISTLI01
        CALL INC32
        LD HL,LISTLINE
        CALL SKIPSPAC
        LD A,(HL)
        OR A
        JR Z,LISTNEXT
        CP ';'
        JR Z,LISTNEXT
        CALL PARSELIN
        JR C,LISTBADL
        OR A
        JR Z,LISTNEXT
        LD A,1
        LD (LISTANY),A
        CALL CANDIDAT
        JR LISTNEXT
LISTBADL:
        CALL LISTBAD
        JR LISTNEXT
LISTFINI:
        LD DE,LISTFCB
        LD C,16
        CALL BDOS
        CP 255
        CALL Z,LISTIOER
        LD A,(LISTPEND)
        OR A
        CALL NZ,LISTBAD
        LD A,(LISTANY)
        OR A
        CALL Z,LISTBAD
        RET
LISTBAD:
        LD A,(LISTMODE)
        OR A
        RET NZ
        LD HL,LISTERRO
        CALL INC32
        LD HL,MSGLISTE
        CALL TEXT
        LD HL,LISTLI01
        CALL DECIMAL
        LD HL,(NUMPTR)
        CALL TEXT
        JP NL
REFOPENERR:
        LD A,1
        LD (REFFAIL),A
        LD HL,DUERRORS
        CALL INC32
        LD HL,MSGREFOPEN
        CALL TEXT
        CALL NL
        RET
REFFAIL: DB 0
MSGREFOPEN: DB 'Cannot open reference list',0
LISTIOER:
        CALL LISTBAD
        LD A,1
        LD (LISTEOF),A
        RET
; Read text into a bounded 255-character line. Overlong lines are consumed and
; diagnosed; their tail must not become a plausible independent entry.
READLINE:
        LD HL,LISTLINE
        LD (LLPTR),HL
        XOR A
        LD (LLTOOLON),A
RLCHAR:
        CALL LISTGET
        JR C,RLEOF
        CP 13
        JR Z,RLCHAR
        CP 10
        JR Z,RLDONE
        LD HL,(LLPTR)
        LD DE,LISTLINE+255
        PUSH AF
        OR A
        SBC HL,DE
        POP AF
        JR Z,RLOVER
        LD HL,(LLPTR)
        LD (HL),A
        INC HL
        LD (LLPTR),HL
        JR RLCHAR
RLOVER:
        LD A,1
        LD (LLTOOLON),A
        JR RLCHAR
RLEOF:
        LD HL,(LLPTR)
        LD DE,LISTLINE
        OR A
        SBC HL,DE
        SCF
        RET Z
RLDONE:
        LD HL,(LLPTR)
        LD (HL),0
        LD A,(LLTOOLON)
        OR A
        CALL NZ,LISTBAD
        OR A
        RET
LISTGET:
        LD A,(LISTEOF)
        OR A
        SCF
        RET NZ
        LD A,(LISTPOS)
        CP 128
        JR C,LGREADY
        LD DE,LISTDMA
        LD C,26
        CALL BDOS
        LD DE,LISTFCB
        LD C,20
        CALL BDOS
        OR A
        JR Z,LGREAD
        CP 1
        CALL NZ,LISTIOER
        JR LGEOF
LGREAD:
        XOR A
        LD (LISTPOS),A
LGREADY:
        LD E,A
        LD D,0
        LD HL,LISTDMA
        ADD HL,DE
        LD A,(HL)
        AND 127
        CP 26
        JR Z,LGEOF
        LD B,A
        LD A,(LISTPOS)
        INC A
        LD (LISTPOS),A
        LD A,B
        CP 'a'
        JR C,LGRETURN
        CP 'z'+1
        JR NC,LGRETURN
        SUB 32
LGRETURN:
        OR A
        RET
LGEOF:
        LD A,1
        LD (LISTEOF),A
        SCF
        RET
SKIPSPAC:
        LD A,(HL)
        CP ' '
        JR Z,SKIPONE
        CP 9
        RET NZ
SKIPONE:
        INC HL
        JR SKIPSPAC
; Parsed entry: ENAME11, EMASK, EVALUES16, ESIZE4, ESIZETYPE0/1recs/2K.
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
        LD A,(EMASK)
        LD B,A
        LD A,(ALGSEL)
        AND B
        LD (EMATCHMA),A
        JR NZ,CMUSABLE
        LD A,(LISTMODE)
        CP 1
        RET Z
        LD HL,SKIPENTS
        CALL INC32
        RET
CMUSABLE:
        LD A,1
        LD (USABLEEN),A
        CALL SIZECOMP
        JR C,CANDDIFF
        LD A,1
        LD (SIZEENTR),A
        LD A,(LISTMODE)
        CP 3
        RET Z
        LD HL,EVALUES
        LD DE,CVALUES
        LD A,1
        LD (CMBIT),A
CMALGORI:
        LD B,1
        LD A,(CMBIT)
        CP 16
        JR Z,CMSIZE
        CP 64
        JR Z,CMSIZE
        LD B,2
        LD A,(CMBIT)
        CP 8
        JR NZ,CMSIZE
        LD B,4
CMSIZE:
        LD A,(EMATCHMA)
        LD C,A
        LD A,(CMBIT)
        AND C
        JR Z,CMSKIP
CMBYTE:
        LD A,(DE)
        CP (HL)
        JR NZ,CANDDIFF
        INC HL
        INC DE
        DJNZ CMBYTE
        JR CMNEXT
CMSKIP:
        INC HL
        INC DE
        DJNZ CMSKIP
CMNEXT:
        LD A,(CMBIT)
        ADD A,A
        LD (CMBIT),A
        OR A
        JR NZ,CMALGORI
        LD A,1
        LD (MATCHENT),A
        LD A,(EMATCHMA)
        LD (MATCHMAS),A
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
        LD A,(LISTMODE)
        CP 3
        JR Z,CANDSIZE
        LD HL,EVALUES
        LD (DETPTR),HL
        LD HL,MSGRECVA
        CALL CANDVAL
        LD HL,CVALUES
        LD (DETPTR),HL
        LD HL,MSGACTVA
        JP CANDVAL
CANDSIZE:
        CALL NEWLINE
        LD HL,MSGSIZEV
        CALL PUTS
        LD HL,ESIZE
        XOR A
        CALL PUTDEC
        LD A,(ESIZETYP)
        CP 2
        LD HL,MSGEXREC
        JR NZ,CANDSIZL
        LD HL,MSGEXK
CANDSIZL:
        CALL PUTS
        LD HL,RECS
        XOR A
        CALL PUTDEC
        LD HL,MSGRECS
        CALL PUTS
        JP ENDLINE
CANDVAL:
        CALL NEWLINE
        CALL PUTS
        LD IX,FIELDTAB
CANDVLOP:
        LD A,(IX+0)
        OR (IX+1)
        JP Z,ENDLINE
        LD A,(IX+5)
        LD (DETBIT),A
        LD A,(EMATCHMA)
        LD B,A
        LD A,(DETBIT)
        AND B
        JR Z,CANDVNXT
        LD L,(IX+0)
        LD H,(IX+1)
        CALL PUTS
        LD A,'='
        CALL PUT
        LD HL,(DETPTR)
        LD E,(IX+3)
        LD D,0
        ADD HL,DE
        LD B,(IX+4)
        CALL FIELDHEX
        LD A,' '
        CALL PUT
CANDVNXT:
        LD DE,6
        ADD IX,DE
        JR CANDVLOP
MSGCAND: DB '  Candidate at line ',0
MSGRECVA: DB '    Recorded: ',0
MSGACTVA: DB '    Actual:   ',0
MSGSIZEV: DB '    Size: ',0
MSGEXREC: DB ' records; actual ',0
MSGEXK: DB ' rounded K; actual ',0
MSGRECS: DB ' records',0
DETPTR: DW 0
DETBIT: DB 0
SIZECOMP:
        LD A,(ESIZETYP)
        OR A
        RET Z
        CP 1
        JR NZ,SIZEK
        LD HL,RECS
        LD DE,ESIZE
        CALL CMP4
        RET Z
        SCF
        RET
SIZEK:
        ; ceil(RECS/8), using exact logical records, compare rounded K.
        LD HL,RECS
        LD DE,KSIZE
        CALL COPY4
        LD B,3
SIZEKSHI:
        LD HL,KSIZE+3
        SRL (HL)
        DEC HL
        RR (HL)
        DEC HL
        RR (HL)
        DEC HL
        RR (HL)
        DJNZ SIZEKSHI
        LD A,(RECS)
        AND 7
        JR Z,SIZEKCMP
        LD HL,KSIZE
        CALL INC32
SIZEKCMP:
        LD HL,KSIZE
        LD DE,ESIZE
        CALL CMP4
        RET Z
        SCF
        RET
MISSCAND:
        LD HL,ENAME
        LD DE,CANDNAME
        LD BC,11
        LDIR
        XOR A
        LD (CANDATTR),A
        CALL SELECTED
        RET Z
        CALL EXCLUDED
        RET NZ
        LD HL,MISSLAST
        LD DE,ENAME
        CALL CMPNAME
        RET NC
        LD A,(MISSFOUN)
        OR A
        JR Z,MISSACCE
        LD HL,ENAME
        LD DE,MISSBEST
        CALL CMPNAME
        RET NC
MISSACCE:
        LD HL,ENAME
        LD DE,MISSBEST
        LD BC,11
        LDIR
        LD A,1
        LD (MISSFOUN),A
        RET
DISCOV01:
        DB 'CRC     LST','CRCKLIST???','CRCKFILE???','-CATALOG???',0
MSGREFER: DB 'Reference: ',0
MSGNOREF: DB 'No CRC list found',13,10,0
MSGAMBIG: DB 'Ambiguous CRC lists; use /CHECK=filename',13,10,0
MSGLISTE: DB 'LIST ERROR, line ',0
MSGNOTFO: DB ' FILE NOT FOUND',0
MSGNOTLI: DB ' FILE NOT LISTED',0
MSGMATCH: DB ': MATCH (all ',0
MCHEND: DB ' checksums)',0
MSGSKIPP: DB ' SKIPPED (no selected algorithm)',0
MSGSIZEM: DB ' SIZE MISMATCH',0
MSGCRCMI: DB ' CHECKSUM MISMATCH',0
MSGALTER: DB '  Differing alternative entries exist',13,10,0
REFFCB: DS 36
LISTFCB: DS 36
LISTDMA: DS 128
LISTLINE: DS 256
LISTLI01: DS 4
LISTPOS: DB 0
LISTEOF: DB 0
LISTFORM: DB 0
LISTPEND: DB 0
LISTANY: DB 0
LISTMODE: DB 0
REFREADY: DB 0
DISCCOUN: DB 0
DISCCAND: DS 11
LLPTR: DW 0
LLTOOLON: DB 0
FOUNDENT: DB 0
MATCHENT: DB 0
USABLEEN: DB 0
SIZEENTR: DB 0
DIFFENTR: DB 0
MATCHMAS: DB 0
SAVEDALG: DB 0
OLDALG: DB 0
ENAME: DS 11
EMASK: DB 0
EVALUES: DS 16
ESIZE: DS 4
ESIZETYP: DB 0
EMATCHMA: DB 0
CMBIT: DB 0
KSIZE: DS 4
MISSLAST: DS 11
MISSBEST: DS 11
MISSFCB: DS 36
MISSFOUN: DB 0
; @list-parser@
