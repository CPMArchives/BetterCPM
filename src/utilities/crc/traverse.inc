; Sorted directory replay avoids any directory-size limit or saved BDOS cursor.
RUN:
        CALL WMASTER
DUJOB:
        LD A,(CANCEL)
        OR A
        JP NZ,RUNEND
        LD HL,COUNTERS
        LD DE,SNAPSHOT
        LD BC,COUNTEND-COUNTERS
        LDIR
        XOR A
        LD (DUBAD),A
        LD HL,(DUINDEX)
        LD DE,(DUCOUNT)
        OR A
        SBC HL,DE
        JP Z,RUNEND
        LD HL,(DUINDEX)
        ADD HL,HL
        LD DE,DUORDER
        ADD HL,DE
        LD C,(HL)
        INC HL
        LD B,(HL)
        LD (CURDU),BC
        LD A,C
        AND 31
        LD (USER),A
        SRL B
        RR C
        SRL B
        RR C
        SRL B
        RR C
        SRL B
        RR C
        SRL B
        RR C
        LD A,C
        LD (DRIVE),A
        CALL LOCATION
        JP C,DUNEXT
        CALL ACTIVATE
        CALL DUCONSOL
        CALL NL
        LD A,(CHECK)
        OR A
        JP NZ,CHECKDU
        ; Preflight determines one stable RECS width for the complete section.
        LD HL,LASTNAME
        LD BC,11
        CALL ZERO
        LD HL,RECSMAX
        LD BC,4
        CALL ZERO
PREFLIGH:
        CALL NEXTFILE
        JR C,PREFLI01
        CALL MAKEFCB
        LD DE,FILEFCB
        LD C,35
        CALL BDOS
        CALL QUERYSIZ
        LD HL,EXPECTED
        LD DE,RECSMAX
        CALL CMP4
        JR C,PREFLIGH
        CALL COPY4
        JR PREFLIGH
PREFLI01:
        LD A,(CANCEL)
        OR A
        JP NZ,RUNEND
        LD A,(DUBAD)
        OR A
        JP NZ,DUNEXT
        LD HL,RECSMAX
        CALL DECIMAL
        CP 4
        JR NC,WIDTHSET
        LD A,4
WIDTHSET:
        LD (RECSWIDT),A
        CALL WLOCAL
        CALL HEADERS
        LD HL,LASTNAME
        LD BC,11
        CALL ZERO
CALCULAT:
        CALL POLL
        LD A,(CANCEL)
        OR A
        JP NZ,RUNEND
        CALL NEXTFILE
        JR C,CALCDONE
        CALL SCANFILE
        JR C,CALCFAIL
        CALL RESULTRO
        LD HL,FILES
        CALL INC32
        JR CALCULAT
CALCFAIL:
        CALL FILEDIAG
        CALL WINVALID
        JR CALCULAT
CALCDONE:
        CALL WLOCALEN
DUNEXT:
        LD A,1
        CALL SUMMARY
        LD HL,(DUINDEX)
        INC HL
        LD (DUINDEX),HL
        JP DUJOB
RUNEND:
        JP WEND
LOCATION:
        LD A,(DRIVE)
        LD E,A
        LD C,14
        CALL BDOS
        LD C,25
        CALL BDOS
        LD B,A
        LD A,(DRIVE)
        CP B
        JR NZ,LOCATI01
        LD A,(USER)
        LD E,A
        LD C,32
        CALL BDOS
        LD E,255
        CALL BDOS
        LD B,A
        LD A,(USER)
        CP B
        RET Z
LOCATI01:
        LD A,1
        LD (DUBAD),A
        CALL WINVALID
        LD HL,DUERRORS
        CALL INC32
        LD A,1
        LD (INCOMPLE),A
        LD HL,MSGLOCAT
        CALL TEXT
        SCF
        RET
ACTIVATE:
        XOR A
        LD (ACTIVECO),A
        LD A,(OPERCOUN)
        LD (ACTLEFT),A
        LD HL,OPERANDS
        LD DE,ACTIVE
ACTLOOP:
        PUSH DE
        PUSH HL
        LD BC,(CURDU)
        CALL MAPBIT
        AND (HL)
        POP HL
        POP DE
        PUSH AF
        LD BC,64
        ADD HL,BC
        POP AF
        JR Z,ACTSKIP
        LD BC,12
        LDIR
        LD A,(ACTIVECO)
        INC A
        LD (ACTIVECO),A
        JR ACTNEXT
ACTSKIP:
        LD BC,12
        ADD HL,BC
ACTNEXT:
        LD A,(ACTLEFT)
        DEC A
        LD (ACTLEFT),A
        JR NZ,ACTLOOP
        RET
; CANDNAME/CANDATTR selected by any active pattern and attribute truth mask.
SELECTED:
        LD IX,ACTIVE
        LD A,(ACTIVECO)
        LD (SELLEFT),A
SELECTNE:
        LD HL,CANDNAME
        LD B,11
        PUSH IX
SELECTCH:
        LD A,(IX+0)
        CP '?'
        JR Z,SELECTCO
        CP (HL)
        JR NZ,SELECTNO
SELECTCO:
        INC IX
        INC HL
        DJNZ SELECTCH
        LD A,(CANDATTR)
        LD B,A
        INC B
        LD A,(IX+0)
SELECTAT:
        RRCA
        DJNZ SELECTAT
        AND 128
        POP IX
        RET NZ
        JR SELECTAD
SELECTNO:
        POP IX
SELECTAD:
        LD DE,12
        ADD IX,DE
        LD A,(SELLEFT)
        DEC A
        LD (SELLEFT),A
        JR NZ,SELECTNE
        XOR A
        RET
DIRFIRST:
        LD HL,DIRFCB
        LD BC,36
        CALL ZERO
        LD A,(DRIVE)
        INC A
        LD (DIRFCB),A
        LD HL,DIRFCB+1
        LD B,11
        LD A,'?'
DIRQ:
        LD (HL),A
        INC HL
        DJNZ DIRQ
        LD (DIRFCB+12),A
        LD DE,DIRDMA
        LD C,26
        CALL BDOS
        LD DE,DIRFCB
        LD C,17
        JP BDOS
; Lowest selected/excluded-filtered name strictly greater than LASTNAME.
NEXTFILE:
        XOR A
        LD (BESTSET),A
        CALL DIRFIRST
NEXTENTR:
        CP 255
        JP Z,NEXTEND
        CP 4
        JP NC,NEXTBAD
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD L,A
        LD H,0
        LD DE,DIRDMA+1
        ADD HL,DE
        LD DE,CANDNAME
        LD B,11
        LD C,0
NEXTCOPY:
        LD A,(HL)
        AND 127
        LD (DE),A
        LD A,B
        CP 4
        JR NC,NEXTCO01
        LD A,(HL)
        RLCA
        AND 1
        OR C
        LD C,A
        RR C
NEXTCO01:
        INC HL
        INC DE
        DJNZ NEXTCOPY
        ; Reconstruct R/S/A truth-table index directly from extension bits.
        DEC HL
        LD A,(HL)
        RLCA
        AND 1
        ADD A,A
        LD C,A
        DEC HL
        LD A,(HL)
        RLCA
        AND 1
        OR C
        ADD A,A
        LD C,A
        DEC HL
        LD A,(HL)
        RLCA
        AND 1
        OR C
        LD (CANDATTR),A
        LD HL,LASTNAME
        LD DE,CANDNAME
        CALL CMPNAME
        JR NC,NEXTCONT
        LD A,(BESTSET)
        OR A
        JR Z,NEXTFILT
        LD HL,CANDNAME
        LD DE,BESTNAME
        CALL CMPNAME
        JR NC,NEXTCONT
NEXTFILT:
        CALL SELECTED
        JR Z,NEXTCONT
        CALL EXCLUDED
        JR NZ,NEXTCONT
        LD HL,CANDNAME
        LD DE,BESTNAME
        LD BC,11
        LDIR
        LD A,1
        LD (BESTSET),A
NEXTCONT:
        CALL POLL
        LD A,(CANCEL)
        OR A
        JR Z,NEXTKEEP
        SCF
        RET
NEXTKEEP:
        LD DE,DIRFCB
        LD C,18
        CALL BDOS
        JP NEXTENTR
NEXTEND:
        LD A,(BESTSET)
        OR A
        SCF
        RET Z
        LD HL,BESTNAME
        LD DE,LASTNAME
        LD BC,11
        LDIR
        OR A
        RET
NEXTBAD:
        CALL LOCATI01
        SCF
        RET
MAKEFCB:
        LD HL,FILEFCB
        LD BC,36
        CALL ZERO
        LD A,(DRIVE)
        INC A
        LD (FILEFCB),A
        LD HL,LASTNAME
        LD DE,FILEFCB+1
        LD BC,11
        LDIR
        RET
QUERYSIZ:
        LD HL,FILEFCB+33
        LD DE,EXPECTED
        LD BC,3
        LDIR
        XOR A
        LD (EXPECTED+3),A
        RET
SCANFILE:
        CALL MAKEFCB
        LD DE,FILEFCB
        LD C,15
        CALL BDOS
        CP 255
        JP Z,SCANERRO
        LD A,1
        LD (FILEOPEN),A
        LD C,35
        CALL BDOS
        CALL QUERYSIZ
        LD HL,RECS
        LD BC,4
        CALL ZERO
        CALL CINIT
SCANRECO:
        CALL POLL
        LD A,(CANCEL)
        OR A
        JR NZ,SCANCLOS
        LD DE,FILEDMA
        LD C,26
        CALL BDOS
        LD DE,FILEFCB
        LD C,20
        CALL BDOS
        OR A
        JR Z,SCANDATA
        CP 1
        JR NZ,SCANCLOS
        CALL CLOSEINP
        JR C,SCANERRO
        LD HL,RECS
        LD DE,EXPECTED
        CALL CMP4
        JR NZ,SCANERRO
        CALL CFINISH
        OR A
        RET
SCANDATA:
        LD IX,FILEDMA
        LD A,128
        LD (SCANLEFT),A
SCANBYTE:
        LD A,(IX+0)
        CALL CUPDATE
        INC IX
        LD A,(SCANLEFT)
        DEC A
        LD (SCANLEFT),A
        JR NZ,SCANBYTE
        LD HL,RECS
        CALL INC32
        JR NC,SCANRECO
SCANCLOS:
        CALL CLOSEINP
SCANERRO:
        LD A,1
        LD (INCOMPLE),A
        LD HL,FAILED
        CALL INC32
        SCF
        RET
CLOSEINP:
        XOR A
        LD (FILEOPEN),A
        LD DE,FILEFCB
        LD C,16
        CALL BDOS
        CP 255
        JR Z,CLOSEBAD
        OR A
        RET
CLOSEBAD:
        SCF
        RET
FILEDIAG:
        CALL NEWLINE
        CALL PUTNAME
        LD HL,MSGREAD
        CALL PUTS
        JP ENDLINE
MSGLOCAT: DB 'CRCKSUM: DU unavailable or directory error',13,10,0
ACTLEFT: DB 0
SELLEFT: DB 0

SCANLEFT: DB 0
DUBAD: DB 0
