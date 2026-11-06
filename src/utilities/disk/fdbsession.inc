; Working and import snapshots are independent of the converter's scratch RAM.
IMPORTBUF EQU 03600H
WORKBUF EQU 05B00H
WORKMAX EQU 02500H
SESSIONSTART:
        LD HL,(6)
        LD DE,EDITOREND
        OR A
        SBC HL,DE
        JP C,MEMERR
        LD HL,EDITORBASE
        LD (ARENALIMIT),HL
        LD HL,IMAGEEND
        LD DE,EDITORBASE
        LD BC,EDITOREND-EDITORBASE
        LDIR
        LD A,1
        LD (SESSION),A
        CALL EMPTYWORK
        LD A,(INPUT+1)
        CP ' '
        JR NZ,STARTNAMED
        LD HL,DISKNAME
        LD DE,INPUT
        LD BC,12
        LDIR
STARTNAMED:
        XOR A
        LD (VIEWACTIVE),A
        LD (VIEWCOMPARE),A
        LD (ACTION),A
        JP READSOURCE
MENU:   LD SP,STACKTOP
        XOR A
        LD (NAMEACTIVE),A
        LD (INOPEN),A
        LD (OUTOPEN),A
        LD (COMPAREOUT),A
        LD (RAWANSWER),A
        LD (ACTION),A
        LD (EDAFTER),A
        LD HL,MENUTITLE
        CALL PUTS
        LD HL,HEADMSG
        CALL PUTS
        LD HL,DEFAULTNAME
        LD A,(DEFAULTNAME+1)
        OR A
        JR NZ,SHOWDEFAULT
        LD HL,UNTITLED
        CALL PUTS
        JR SHOWCOUNT
SHOWDEFAULT: CALL SHOWNAME
SHOWCOUNT:
        LD HL,COUNTMSG
        CALL PUTS
        LD A,(WORKBUF+8)
        CALL COUNTDEC
        LD HL,CLEANSTATE
        LD A,(DIRTY)
        OR A
        JR Z,SHOWSTATE
        LD HL,MODSTATE
SHOWSTATE: CALL PUTS
        LD A,(EDPENDING)
        OR A
        LD HL,EDPENDMSG
        CALL NZ,PUTS
        LD HL,MENUMSG
        CALL ASKCHOICE
        CP 'A'
        JP Z,EDFROMDRIVE
        CP 'B'
        JP Z,EDFROMCAT
        CP 'C'
        JP Z,EDBLANK
        CP 'E'
        JP Z,EDRESUME
        CP 'S'
        JP Z,SAVECAT
        CP 'I'
        JP Z,IMPORTCAT
        CP 'D'
        JP Z,DETAILMENU
        CP 'P'
        JP Z,COMPAREMENU
        CP 'O'
        JP Z,EXPORTMENU
        CP 'L'
        JP Z,LISTCAT
        CP 'N'
        JR Z,NEWCAT
        CP 'F'
        JR Z,OPENCAT
        CP 3
        JR Z,QUITCAT
        CP 'Q'
        JP NZ,MENU
QUITCAT: CALL EDEXITCHECK
        CALL PENDING
        JP EXIT
NEWCAT: CALL PENDING
        CALL EMPTYWORK
        JP MENU
OPENCAT: CALL PENDING
        LD HL,OPENMSG
        CALL ASKNAME
        CALL TOINPUT
        XOR A
        LD (ACTION),A
        JR READSOURCE
IMPORTCAT:
        LD HL,IMPORTMSG
        CALL PUTS
        LD A,(WORKBUF+8)
        OR A
        JR Z,IMPORTASK
        LD HL,NEWHINT
        CALL PUTS
IMPORTASK: LD HL,SOURCEMSG
        CALL ASKNAME
        CALL TOINPUT
        LD A,1
        LD (ACTION),A
READSOURCE:
        LD HL,INPUT+1
        LD B,11
SRCWILD:LD A,(HL)
        CP '?'
        JP Z,BADNAME
        INC HL
        DJNZ SRCWILD
        LD HL,INPUT+9
        LD DE,FDBEXT
        CALL MATCH3
        JP Z,READBINARY
        LD HL,INPUT+9
        LD DE,FDFEXT
        CALL MATCH3
        JP NZ,BADNAME
        LD A,128
        LD (INCOUNT),A
        XOR A
        LD (ATEOF),A
        JP COMPILE
STAGED: LD A,(ACTION)
        CP 2
        JP Z,EDCATREADY
        CALL FITCHECK
        LD A,(ACTION)
        OR A
        CP 4
        JP Z,EXPORTBASE
        OR A
        JP NZ,MERGEIMPORT
        JP CHECKNAMES
OPENACCEPT:LD HL,INPUT
        LD DE,DEFAULTNAME
        LD BC,12
        LDIR
        CALL COMMITWORK
        XOR A
        LD (DIRTY),A
        JP MENU
FITCHECK:
        LD HL,WORKMAX
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        JP C,MEMERR
        LD A,(FCOUNT)
        CP MAXFORM+1
        JP NC,MEMERR
        RET
COMMITWORK:
        LD BC,(FDBLEN)
        LD (WORKLEN),BC
        LD DE,WORKBUF
        LD HL,FDFRAM
        LDIR
        RET
EMPTYWORK:
        LD HL,FDFRAM
        LD DE,FDFRAM+1
        LD BC,127
        LD (HL),0
        LDIR
        LD HL,HEADER
        LD DE,FDFRAM
        LD BC,16
        LDIR
        LD HL,POOLRAM
        LD (POOLPTR),HL
        XOR A
        LD (FCOUNT),A
        LD (DIRTY),A
        LD (DEFAULTNAME+1),A
        CALL PACKCAT
        JP COMMITWORK
PENDING:
        LD A,(DIRTY)
        OR A
        RET Z
        LD HL,PENDINGMSG
        CALL ASKCHOICE
        CP 'D'
        RET Z
        CP 'S'
        JP NZ,MENU
        JP DOSAVE
; Build a pointer table, resolving IDs before writing the proposed catalogue.
MERGEIMPORT:
        LD HL,FDFRAM
        LD DE,IMPORTBUF
        LD BC,(FDBLEN)
        LDIR
        LD HL,WORKBUF+128
        LD A,(WORKBUF+8)
INITREFS:LD DE,REFS
        LD (REFCOUNT),A
        OR A
        JR Z,SELECTIMPORT
        LD B,A
REFINIT:LD A,L
        LD (DE),A
        INC DE
        LD A,H
        LD (DE),A
        INC DE
        PUSH DE
        LD DE,64
        ADD HL,DE
        POP DE
        DJNZ REFINIT
SELECTIMPORT:
        LD A,(ACTION)
        CP 4
        JP Z,EXPORTMATCH
        LD A,(ACTION)
        CP 3
        JR NZ,ASKIMPORTID
        XOR A
        LD (ANSWER),A
        JR SELECTCHECK
ASKIMPORTID:
        LD HL,SELECTMSG
        CALL ASK
SELECTCHECK:LD A,(ANSWER)
        CP 3
        JP Z,MENU
        ; Only an empty line selects all records. A leading space in a
        ; mistyped ID must never widen a single-entry import.
        LD HL,ANSWER
        LD A,(HL)
        CP ' '
        JP Z,BADNAME
        LD DE,ANSWER
        LD B,8
PADSEL: LD A,(HL)
        OR A
        JR Z,SELSPACE
        INC HL
        LD (DE),A
        INC DE
        DJNZ PADSEL
        LD A,(HL)
        OR A
        JP NZ,BADNAME
        JR SELREADY
SELSPACE: LD A,' '
SELPAD: LD (DE),A
        INC DE
        DJNZ SELPAD
SELREADY:
        LD HL,ANSWER
        LD DE,SELECTED
        LD BC,8
        LDIR
        XOR A
        LD (ADDED),A
        LD (REPLACED),A
        LD IX,IMPORTBUF+128
        LD A,(IMPORTBUF+8)
        LD (REMAIN),A
MERGENEXT:
        LD A,(REMAIN)
        OR A
        JP Z,REBUILD
        LD A,(SELECTED)
        CP ' '
        JR Z,MATCHREF
        PUSH IX
        POP HL
        LD DE,SELECTED
        LD B,8
        CALL CMPFIELD
        JP NZ,SKIPREF
MATCHREF:
        LD IY,REFS
        LD A,(REFCOUNT)
        OR A
        JR Z,ADDREF
        LD C,A
FINDREF:
        LD E,(IY+0)
        LD D,(IY+1)
        PUSH IX
        POP HL
        LD B,8
        CALL CMPFIELD
        JR Z,DUPREF
        INC IY
        INC IY
        DEC C
        JR NZ,FINDREF
ADDREF: LD A,(REFCOUNT)
        CP MAXFORM
        JP NC,MEMERR
        INC A
        LD (REFCOUNT),A
        LD HL,ADDED
        INC (HL)
        JR PUTREF
DUPREF: PUSH IX
        POP HL
        LD B,8
DUPSHOW:LD A,(HL)
        CALL PUTC
        INC HL
        DJNZ DUPSHOW
        PUSH IX
        PUSH IY
        LD HL,DUPMSG
        CALL ASKCHOICE
        POP IY
        POP IX
        CP 'U'
        JR NZ,REPLACEREF
        PUSH IX
        LD HL,IDMSG
        CALL ASK
        POP IX
        LD HL,ANSWER
        PUSH IX
        POP DE
        LD B,8
        LD C,0
NEWIDCHAR:
        LD A,(HL)
        OR A
        JR Z,NEWIDEND
        CP '0'
        JP C,BADNAME
        CP '9'+1
        JR C,NEWIDOK
        CP 'A'
        JP C,BADNAME
        CP 'Z'+1
        JP NC,BADNAME
NEWIDOK:LD (DE),A
        INC HL
        INC DE
        INC C
        DJNZ NEWIDCHAR
        LD A,(HL)
        OR A
        JP NZ,BADNAME
        JP MATCHREF
NEWIDEND:LD A,C
        OR A
        JP Z,MENU
        LD A,' '
NEWIDPAD:LD (DE),A
        INC DE
        DJNZ NEWIDPAD
        JP MATCHREF
REPLACEREF:CP 'R'
        JP NZ,MENU
        LD HL,REPLACED
        INC (HL)
PUTREF: PUSH IX
        POP HL
        LD (IY+0),L
        LD (IY+1),H
SKIPREF:LD DE,64
        ADD IX,DE
        LD HL,REMAIN
        DEC (HL)
        JP MERGENEXT
CMPFIELD: LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DJNZ CMPFIELD
        RET
REBUILD:
        LD A,(ADDED)
        LD HL,REPLACED
        OR (HL)
        JP Z,NOIMPORT
        LD HL,POOLRAM
        LD (POOLPTR),HL
        XOR A
        LD (FCOUNT),A
        LD IY,REFS
COPYREF:
        LD A,(FCOUNT)
        LD HL,REFCOUNT
        CP (HL)
        JP Z,MERGED
        CALL GETDESC
        LD L,(IY+0)
        LD H,(IY+1)
        INC IY
        INC IY
        LD DE,BIND
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JR Z,REFWORK
        LD DE,IMPORTBUF
        LD A,H
        CP 05BH
        JR C,HASBASE
REFWORK:LD DE,WORKBUF
HASBASE:LD (SRCBASE),DE
        PUSH IX
        POP DE
        LD BC,64
        LDIR
        LD L,(IX+60)
        LD H,(IX+61)
        LD DE,(SRCBASE)
        ADD HL,DE
        LD (OBJSTART),HL
        LD E,(IX+55)
        LD D,0
        ADD HL,DE
        BIT 7,(IX+58)
        JR Z,OBJEND
TLVSKIP:LD A,(HL)
        INC HL
        LD E,(HL)
        INC HL
        OR A
        JR Z,OBJEND
        ADD HL,DE
        JR TLVSKIP
OBJEND: LD DE,(OBJSTART)
        OR A
        SBC HL,DE
        LD B,H
        LD C,L
        LD HL,(POOLPTR)
        ADD HL,BC
        LD DE,EDITORBASE
        OR A
        SBC HL,DE
        JP NC,MEMERR
        LD HL,(POOLPTR)
        LD DE,0-FDFRAM
        ADD HL,DE
        LD (IX+60),L
        LD (IX+61),H
        BIT 7,(IX+58)
        JR Z,COPYOBJ
        LD E,(IX+55)
        LD D,0
        ADD HL,DE
        LD (IX+62),L
        LD (IX+63),H
COPYOBJ:LD HL,(OBJSTART)
        LD DE,(POOLPTR)
        LDIR
        LD (POOLPTR),DE
        LD HL,FCOUNT
        INC (HL)
        JP COPYREF
MERGED: LD HL,0
        LD (FDFRAM+14),HL
        CALL PACKCAT
        CALL FITCHECK
        CALL FDBVALID
        JP C,BADFDB
        CALL SEMANTICS
; Reject ambiguous descriptions before changing the session.
CHECKNAMES:LD A,(FCOUNT)
        OR A
        JP Z,NAMESOK
        LD C,A
        LD IX,FDFRAM+128
NAMENEXT: DEC C
        JP Z,NAMESOK
        PUSH IX
        POP HL
        LD DE,64
        ADD HL,DE
        LD B,C
NAMEPAIR: PUSH BC
        PUSH HL
        LD DE,8
        ADD HL,DE
        EX DE,HL
        PUSH IX
        POP HL
        LD BC,8
        ADD HL,BC
        LD B,32
NAMECMP:LD A,(DE)
        CALL UPPER
        LD C,A
        LD A,(HL)
        CALL UPPER
        CP C
        JR NZ,NAMEDIFF
        INC DE
        INC HL
        DJNZ NAMECMP
        POP HL
        POP BC
        LD A,(ACTION)
        OR A
        JP Z,AMBIGFAIL
        ; C = remaining pairs at IX, B = remaining pairs from HL.
        LD A,(REFCOUNT)
        SUB C
        DEC A
        LD L,A
        LD H,0
        ADD HL,HL
        LD DE,REFS
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD A,D
        CALL CANRENAME
        JR C,EDITDESCRIPTION
        LD A,(REFCOUNT)
        SUB B
        LD L,A
        LD H,0
        ADD HL,HL
        LD DE,REFS
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD A,D
        CALL CANRENAME
        JP NC,AMBIGFAIL
EDITDESCRIPTION:
        EX DE,HL
        LD B,8
        CALL NAMEOUT
        PUSH HL
        LD A,1
        LD (RAWANSWER),A
        LD HL,AMBIGMSG
        CALL ASK
        XOR A
        LD (RAWANSWER),A
        POP DE
        LD HL,ANSWER
        LD A,(HL)
        OR A
        JP Z,MENU
        CP 3
        JP Z,MENU
        LD B,32
DESCFILL:
        LD A,(HL)
        OR A
        JR Z,DESCPAD
        CP 34
        JP Z,BADNAME
        INC HL
        JR DESCSTORE
DESCPAD:LD A,' '
DESCSTORE:LD (DE),A
        INC DE
        DJNZ DESCFILL
        JP REBUILD
AMBIGFAIL:LD HL,AMBIGBAD
        JP EXITMSG
NAMEDIFF:POP HL
        LD DE,64
        ADD HL,DE
        POP BC
        DEC B
        JP NZ,NAMEPAIR
        ADD IX,DE
        JP NAMENEXT
NAMESOK:LD A,(ACTION)
        OR A
        JP Z,OPENACCEPT
        CP 4
        JP Z,EXPORTREADY
        CALL COMMITWORK
        LD A,1
        LD (DIRTY),A
        LD A,(ADDED)
        CALL COUNTDEC
        LD HL,ADDMSG
        CALL PUTS
        LD A,(REPLACED)
        CALL COUNTDEC
        LD HL,REPLMSG
        CALL PUTS
        LD A,(ACTION)
        CP 3
        JP NZ,MENU
        JP EDCOMMITTED
NOIMPORT:LD HL,NONEFOUND
        JP EXITMSG
; Write, close and compare every record (including EOF) before publication.
SAVECAT:LD A,(EDSOURCE)
        OR A
        JP NZ,EDSAVE
EDWRITECAT:CALL EDINCLUDE
        CALL DOSAVE
        JP MENU
DOSAVE: LD A,(DEFAULTNAME+1)
        OR A
        LD HL,NEEDNAMEMSG
        JR Z,SAVEASK
        LD HL,DEFAULTNAME
        CALL SHOWNAME
        CALL CRLF
        LD HL,DESTMSG
SAVEASK:
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        OR A
        JR NZ,SAVENAME
        LD A,(DEFAULTNAME+1)
        OR A
        JR Z,DOSAVE
        LD HL,DEFAULTNAME
        LD DE,DESTFCB
        LD BC,12
        LDIR
        JR DESTREADY
SAVENAME:CALL PARSENAME
DESTREADY:XOR A
        LD (TEXTDEST),A
        LD HL,DESTFCB+9
        LD DE,FDBEXT
        CALL MATCH3
        JR Z,SHOWDEST
        LD HL,DESTFCB+9
        LD DE,FDFEXT
        CALL MATCH3
        JP NZ,BADNAME
        LD A,1
        LD (TEXTDEST),A
SHOWDEST:LD DE,DESTFCB
        CALL PRESENT
        LD A,0
        JR Z,DESTABSENT
        INC A
DESTABSENT:LD (HADDEST),A
        LD A,(ACTION)
        CP 4
        JP Z,EXPORTREAD
SHOWCONFIRM:
        LD HL,DESTFCB
        CALL SHOWNAME
        LD HL,WRITEMSG
        LD A,(HADDEST)
        OR A
        JR Z,CONFIRMSAVE
        LD HL,REPLACEMSG
CONFIRMSAVE:
        CALL ASKCHOICE
        CP 'Y'
        JP NZ,MENU
        LD A,(ACTION)
        CP 4
        JR Z,SAVEVALID
        LD HL,WORKBUF
        LD DE,FDFRAM
        LD BC,(WORKLEN)
        LD (FDBLEN),BC
        LDIR
SAVEVALID:CALL FDBVALID
        JP C,BADFDB
        CALL SEMANTICS
        LD HL,DESTFCB
        LD DE,TEMPFCB
        LD BC,9
        LDIR
        LD HL,DESTFCB
        LD DE,BACKFCB
        LD BC,9
        LDIR
        LD HL,TEMPEXT
        LD DE,TEMPFCB+9
        LD BC,3
        LDIR
        LD HL,BACKEXT
        LD DE,BACKFCB+9
        LD BC,3
        LDIR
        LD DE,TEMPFCB
        CALL PRESENT
        JP NZ,RECEXIST
        LD DE,BACKFCB
        CALL PRESENT
        JP NZ,RECEXIST
        LD HL,TEMPFCB
        LD DE,OUTPUT
        CALL COPYFCB
        CALL CREATEOUT
        LD A,(TEXTDEST)
        OR A
        JR Z,SAVEBIN
        CALL WRITETEXT
        JR VERIFYOPEN
SAVEBIN:LD HL,FDFRAM
        LD BC,(FDBLEN)
SAVEREC:PUSH HL
        PUSH BC
        CALL POLLBREAK
        POP BC
        POP HL
        PUSH BC
        PUSH HL
        EX DE,HL
        CALL SETDMA
        LD DE,OUTPUT
        LD C,21
        CALL BDOS
        OR A
        JP NZ,IOERR
        POP HL
        LD DE,128
        ADD HL,DE
        POP BC
        PUSH HL
        LD HL,-128
        ADD HL,BC
        LD B,H
        LD C,L
        POP HL
        LD A,B
        OR C
        JR NZ,SAVEREC
        CALL FINISHOUT
VERIFYOPEN:LD HL,TEMPFCB
        LD DE,INPUT
        CALL COPYFCB
        CALL OPENIN
        LD A,(TEXTDEST)
        OR A
        JR Z,VERIFYBIN
        LD (COMPAREOUT),A
        CALL WRITETEXT
        XOR A
        LD (COMPAREOUT),A
        JR VERIFYEOF
VERIFYBIN:LD HL,FDFRAM
        LD BC,(FDBLEN)
VERIFYREC:
        PUSH BC
        PUSH HL
        CALL READTEMP
        OR A
        JP NZ,VERIFYERR
        POP HL
        LD DE,INBUF
        LD B,128
        CALL CMPFIELD
        JP NZ,VERIFYERR
        POP BC
        PUSH HL
        LD HL,-128
        ADD HL,BC
        LD B,H
        LD C,L
        POP HL
        LD A,B
        OR C
        JR NZ,VERIFYREC
VERIFYEOF:CALL READTEMP
        CP 1
        JP NZ,VERIFYERR
        CALL CLOSEIN
        LD A,(HADDEST)
        OR A
        JR Z,PROMOTE
        LD HL,DESTFCB
        LD DE,BACKFCB
        CALL RENAMEFILE
        JP Z,RECFILES
PROMOTE:LD HL,TEMPFCB
        LD DE,DESTFCB
        CALL RENAMEFILE
        JR NZ,PUBLISHED
        LD A,(HADDEST)
        OR A
        JP Z,RECFILES
        LD HL,BACKFCB
        LD DE,DESTFCB
        CALL RENAMEFILE
        JP RECFILES
PUBLISHED:
        LD A,(ACTION)
        CP 4
        JR NC,EXPORTCLEAN
        LD HL,DESTFCB
        LD DE,DEFAULTNAME
        LD BC,12
        LDIR
        XOR A
        LD (DIRTY),A
EXPORTCLEAN:LD A,(HADDEST)
        OR A
        JR Z,SAVED
        LD DE,BACKFCB
        LD C,19
        CALL BDOS
        CP 255
        JR NZ,SAVED
        LD HL,KEEPBACK
        CALL PUTS
SAVED:  LD A,(ACTION)
        CP 4
        JP NC,EXPORTED
        LD HL,SAVEDMSG
        JP PUTS
READTEMP:LD DE,INBUF
        CALL SETDMA
        LD DE,INPUT
        LD C,20
        JP BDOS
VERIFYERR:LD HL,TEMPFCB
        CALL SHOWNAME
        CALL CRLF
        LD HL,VERIFYMSG
        JP EXITMSG
RECEXIST:LD HL,RECEXISTMSG
        CALL PUTS
RECFILES:LD HL,RECMSG
        CALL PUTS
        LD HL,DESTFCB
        CALL SHOWNAME
        CALL CRLF
        LD HL,BACKFCB
        CALL SHOWNAME
        CALL CRLF
        LD HL,TEMPFCB
        CALL SHOWNAME
        CALL CRLF
        LD HL,EMPTYMSG
        JP EXITMSG
; Never rename over an existing target, including a recovery file.
RENAMEFILE:
        PUSH HL
        PUSH DE
        CALL PRESENT
        POP DE
        POP HL
        JR Z,RENFREE
        XOR A
        RET
RENFREE:PUSH DE
        LD DE,RENFCB
        CALL COPYFCB
        POP HL
        LD DE,RENFCB+16
        LD BC,12
        LDIR
        LD DE,RENFCB
        LD C,23
        CALL BDOS
        CP 255
        RET
PRESENT:PUSH DE
        LD DE,INBUF
        CALL SETDMA
        POP DE
        PUSH DE
        POP HL
        LD DE,SEARCHFCB
        CALL COPYFCB
        LD DE,SEARCHFCB
        LD C,17
        CALL BDOS
        CP 255
        RET
TOINPUT:LD HL,DESTFCB
        LD DE,INPUT
COPYFCB:LD BC,12
        LDIR
        XOR A
        LD B,24
FCBZERO:LD (DE),A
        INC DE
        DJNZ FCBZERO
        RET
ASKNAME:CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
PARSENAME:LD (NAMESTACK),SP
        LD A,1
        LD (NAMEACTIVE),A
NAMEPARSE:
        LD HL,DESTFCB
        LD (HL),0
        LD B,11
PADNAME:INC HL
        LD (HL),' '
        DJNZ PADNAME
        LD HL,ANSWER
        LD A,(ANSWER+1)
        CP ':'
        JR Z,NAMEDRIVEPREFIX
        CP '0'
        JR C,NAMEBASE
        CP '9'+1
        JR NC,NAMEBASE
        LD A,(ANSWER+2)
        CP ':'
        JR Z,NAMEDU
        LD A,(ANSWER+3)
        CP ':'
        JR NZ,NAMEBASE
NAMEDU:
        LD A,(HL)
        SUB 'A'
        CP 16
        JP NC,BADNAME
        INC A
        LD (DESTFCB),A
        INC HL
        LD A,(HL)
        SUB '0'
        LD E,A
        INC HL
        LD A,(HL)
        CP ':'
        JR Z,NAMEUSER
        CP '0'
        JP C,BADNAME
        CP '9'+1
        JP NC,BADNAME
        SUB '0'
        LD D,A
        LD A,E
        CP 1
        JP NZ,BADNAME
        LD A,D
        ADD A,10
        LD E,A
        INC HL
        LD A,(HL)
        CP ':'
        JP NZ,BADNAME
NAMEUSER:PUSH HL
        PUSH DE
        LD E,255
        LD C,32
        CALL BDOS
        POP DE
        POP HL
        CP E
        JP NZ,BADNAME
        INC HL
        JR NAMEBASE
NAMEDRIVEPREFIX:
        LD A,(HL)
        SUB 'A'
        CP 16
        JP NC,BADNAME
        INC A
        LD (DESTFCB),A
        INC HL
        INC HL
NAMEBASE:LD DE,DESTFCB+1
        LD B,8
        CALL NAMEPART
        LD A,(HL)
        CP '.'
        JP NZ,BADNAME
        INC HL
        LD DE,DESTFCB+9
        LD B,3
        CALL NAMEPART
        LD A,(HL)
        OR A
        JR NZ,BADNAME
        LD (NAMEACTIVE),A
        RET
BADNAME:LD A,(NAMEACTIVE)
        OR A
        JR Z,NAMEERROR
        LD SP,(NAMESTACK)
        LD HL,NAMEMSG
        CALL PUTS
        LD HL,NAMEHINT
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        JP NAMEPARSE
NAMEERROR:LD HL,NAMEMSG
        JP EXITMSG
NAMEPART:
        LD C,0
NAMELOOP:LD A,(HL)
        OR A
        JR Z,NAMEEND
        CP '.'
        JR Z,NAMEEND
        CP 'A'
        JR C,NAMEDIG
        CP 'Z'+1
        JR C,NAMEOK
NAMEDIG:CP '-'
        JR Z,NAMEOK
        CP '0'
        JP C,BADNAME
        CP '9'+1
        JR C,NAMEOK
        CP '_'
        JR Z,NAMEOK
        CP '-'
        JP NZ,BADNAME
NAMEOK: LD (DE),A
        INC HL
        INC DE
        INC C
        DJNZ NAMELOOP
NAMEEND:LD A,C
        OR A
        JP Z,BADNAME
        RET
SHOWNAME:
        PUSH HL
        LD A,(HL)
        OR A
        JR NZ,NAMEDRIVE
        LD C,25
        CALL BDOS
        INC A
NAMEDRIVE: ADD A,'A'-1
        CALL PUTC
        LD E,255
        LD C,32
        CALL BDOS
        CALL COUNTDEC
        LD A,':'
        CALL PUTC
        POP HL
        INC HL
        LD B,8
        CALL NAMEOUT
        LD A,'.'
        CALL PUTC
        LD B,3
NAMEOUT:LD A,(HL)
        CP ' '
        CALL NZ,PUTC
        INC HL
        DJNZ NAMEOUT
        RET
COUNTDEC:LD C,0
HUNDREDS:CP 100
        JR C,TENS
        SUB 100
        INC C
        JR HUNDREDS
TENS:   LD B,A
        LD A,C
        OR A
        JR Z,SMALLNUM
        ADD A,'0'
        CALL PUTC
SMALLNUM:LD A,B
        LD B,0
TENLOOP:CP 10
        JR C,ONES
        SUB 10
        INC B
        JR TENLOOP
ONES:   PUSH AF
        LD A,B
        OR C
        JR Z,ONLYONE
        LD A,B
        ADD A,'0'
        CALL PUTC
ONLYONE:POP AF
        ADD A,'0'
        JP PUTC
CRLF:   LD A,13
        CALL PUTC
        LD A,10
        JP PUTC
UPPER:  CP 'a'
        RET C
        CP 'z'+1
        RET NC
        SUB 32
        RET
ASKCHOICE:PUSH HL
        CALL ASK
        POP HL
        LD A,(ANSWER+1)
        OR A
        JR Z,CHOICEOK
        PUSH HL
        CALL BADCHOICE
        POP HL
        JR ASKCHOICE
CHOICEOK:
        LD A,(ANSWER)
        RET
BADCHOICE:LD HL,CHOICEMSG
        JP PUTS
; Read directly so BREAK returns to the session and can protect dirty work.
ASK:    CALL PUTS
        CALL CRLF
        LD HL,ANSWER
        LD B,0
ASKKEY: PUSH BC
        PUSH HL
        LD E,255
        LD C,6
        CALL BDOS
ASKREAD:POP HL
        POP BC
        OR A
        JR Z,ASKKEY
        CP 3
        JR Z,ASKBREAK
        CP 27
        JR Z,ASKBREAK
        CP 13
        JR Z,ASKDONE
        CP 8
        JR Z,ASKBACK
        CP 127
        JR Z,ASKBACK
        CP 32
        JR C,ASKKEY
        LD C,A
        LD A,B
        CP 32
        JR NC,ASKOVER
        LD A,(RAWANSWER)
        OR A
        LD A,C
        CALL Z,UPPER
        LD (HL),A
        INC HL
        INC B
        CALL PUTC
        JR ASKKEY
; Drain the rest of an overlong line before returning to the menu.
; Otherwise its suffix could be interpreted as an independent command.
ASKOVER:LD A,7
        CALL PUTC
        JR ASKKEY
ASKBACK:LD A,B
        OR A
        JR Z,ASKKEY
        DEC B
        DEC HL
        LD A,8
        CALL PUTC
        LD A,' '
        CALL PUTC
        LD A,8
        CALL PUTC
        JR ASKKEY
ASKBREAK:LD HL,ANSWER
        LD (HL),3
        INC HL
ASKDONE:
        LD (HL),0
        JP CRLF
SESSION:DB 0
DIRTY:  DB 0
ACTION: DB 0
TEXTDEST:DB 0
COMPAREOUT:DB 0
HADDEST:DB 0
REMAIN: DB 0
ADDED:  DB 0
REPLACED:DB 0
REFCOUNT:DB 0
WORKLEN:DW 0
SRCBASE:DW 0
OBJSTART:DW 0
DEFAULTNAME:DS 12
DESTFCB:DS 36
BACKFCB:DS 36
TEMPFCB:DS 36
SEARCHFCB EQU LINE+331
RENFCB EQU LINE+367
; Parsing finishes before interactive merge/list/input scratch becomes live.
REFS EQU LINE
SELECTED EQU LINE+323
ANSWER EQU LINE+256
RAWANSWER: DB 0
NAMEACTIVE:DB 0
NAMESTACK:DW 0
DISKNAME:DB 0,'DISK    FDB'
TEMPEXT:DB '$$$'
BACKEXT:DB 'BAK'
HEADMSG:DB 13,10,'Working catalogue: ',0
UNTITLED:DB 'Untitled',0
COUNTMSG:DB '   Entries: ',0
MODSTATE:DB '   Modified',13,10,0
CLEANSTATE:DB '   Unmodified',13,10,0
MENUTITLE: DB 13,10,
; @fdb-main-menu-title@
MENUMSG:
        DB 13,10
        DB '[ F ] Open a catalogue from disk',13,10
        DB '[ N ] New empty working catalogue',13,10
        DB 13,10
        DB '[ L ] List or find formats',13,10
        DB '[ D ] Display format details',13,10
        DB '[ P ] Compare two formats',13,10
        DB 13,10
        DB '[ A ] Edit the format of an active logical drive',13,10
        DB '[ B ] Load a catalogue entry into the editor',13,10
        DB '[ C ] Create a new format',13,10
        DB '[ E ] Resume the working format editor',13,10
        DB 13,10
        DB '[ I ] Import into the working catalogue (.FDB or .FDF)',13,10
        DB '[ O ] Export from the working catalogue (.FDB or .FDF)',13,10
        DB '[ S ] Save catalogue or apply working format to a drive',13,10
        DB 13,10
        DB 'Select [ F, N, L, D, P, A-C, E, I, O, S or Q ]; BREAK (^C) exits.',13,10
        DB 'Your choice: [ ]',0
; @fdb-message-dictionary@
PENDINGMSG:DB 'Unsaved catalogue: S Save, D Discard, C Cancel: ',0
OPENMSG:DB 'Open catalogue filename: ',0
IMPORTMSG:DB 'Import into working catalogue',13,10,0
NEWHINT:DB 'For an empty catalogue, choose N first.',13,10,0
SOURCEMSG:DB 'Source .FDB or .FDF: ',0
SELECTMSG:DB 'ID to import (Return for entire catalogue): ',0
DUPMSG: DB ' exists. R Replace, U Use new ID, C Cancel: ',0
AMBIGMSG:DB ' duplicate. Description (Enter=cancel): ',0
AMBIGBAD:DB 'Duplicate display names. Working catalogue preserved.',13,10,0
IDMSG: DB 'New ID (1-8 letters/digits): ',0
NONEFOUND:DB 'ID not found; working data preserved.',13,10,0
ADDMSG: DB ' added, ',0
REPLMSG:DB ' replaced. Changes are unsaved.',13,10,0
DESTMSG:DB 'Write file (Return uses name above): ',0
WRITEMSG:DB '  Create (Y/N)? ',0
REPLACEMSG:DB '  Replace entire file (Y/N)? ',0
SAVEDMSG:DB 'Catalogue saved and verified.',13,10,0
KEEPBACK:DB 'Published. Old catalogue retained as .BAK.',13,10,0
RECMSG: DB 'Save stopped; keep/inspect these files:',13,10,0
RECEXISTMSG:DB 'Recovery file already exists.',13,10,0
EMPTYMSG:DB 0
VERIFYMSG:DB 'Temporary file failed readback. Inspect .$$$; original preserved.',13,10,0
NAMEMSG:DB 'Invalid filename or ID.',13,10,0

EDNUMMSG:DB 'Value (decimal or 0x hex): ',0
EDBYTEMSG:DB 'Value 0-255 (decimal/0x): ',0
EDWORDMSG:DB 'Value 0-65535 (decimal/0x): ',0
EDFLAGMSG:DB 'Value 0 or 1: ',0

; A=zero-based first slot, B=total; inclusive visible range and total.
MAPRANGE:LD C,A
        LD A,B
        OR A
        LD A,C
        JR NZ,MAPRBEGIN
        LD A,255
MAPRBEGIN:PUSH AF
        PUSH BC
        INC A
        CALL COUNTDEC
        LD A,'-'
        CALL PUTC
        POP BC
        POP AF
        ADD A,8
        JR C,MAPRMAX
        CP B
        JR C,MAPREND
MAPRMAX:LD A,B
MAPREND:PUSH BC
        CALL COUNTDEC
        LD A,'/'
        CALL PUTC
        POP BC
        LD A,B
        CALL COUNTDEC
        JP CRLF

CHOICEMSG:DB 'Invalid choice; try again.',13,10,0
EDNUMBAD:DB 'Invalid number. ',0
EDIDMISSING:DB 'Set I ID and N Name first.',13,10,0
EDSPTMSG:DB 'Page 3 A SPT / expected: ',0
EDRULEBLOCK:DB 'Page 3 B-D: BSH=3..7; BLM=2^BSH-1; check EXM.',13,10,0
EDRULEIDS:DB 'Page 2: side/track/sector numbering or IDs invalid.',13,10,0
EDRULEDIR:DB 'Page 3 F-H: AL bitmap must cover DRM+1 entries.',13,10,0
EDRULEALLOC:DB 'Page 3 E/J: DSM+OFF allocation must fit geometry.',13,10,0
