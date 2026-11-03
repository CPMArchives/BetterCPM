; Inspect the working snapshot directly. No editor, merge or file state is
; borrowed. A filter matches a substring of either ID or display name.
LISTCAT:
        LD HL,LISTFILTER
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        LD HL,ANSWER
        LD DE,LISTTERM
        LD BC,33
        LDIR
        LD IX,WORKBUF+128
        LD A,(WORKBUF+8)
        LD (LISTLEFT),A
        LD A,12
        LD (LISTROOM),A
        XOR A
        LD (LISTFOUND),A
LISTNEXT:
        LD A,(LISTLEFT)
        OR A
        JR Z,LISTDONE
        PUSH IX
        POP HL
        LD B,8
        CALL LISTMATCH
        JR Z,LISTROW
        PUSH IX
        POP HL
        LD DE,8
        ADD HL,DE
        LD B,32
        CALL LISTMATCH
        JR NZ,LISTSKIP
LISTROW:
        LD A,(LISTROOM)
        OR A
        JR NZ,LISTPRINT
        PUSH IX
        LD HL,LISTMORE
        CALL ASK
        POP IX
        LD A,(ANSWER)
        OR A
        JP NZ,MENU
        LD A,12
LISTPRINT:
        DEC A
        LD (LISTROOM),A
        LD A,1
        LD (LISTFOUND),A
        PUSH IX
        POP HL
        LD B,8
        CALL EDFIXED
        LD B,32
        CALL EDFIXED
        LD A,' '
        CALL PUTC
        CALL LISTCAP
        CALL EDBYTES
        CALL CRLF
LISTSKIP:
        LD DE,64
        ADD IX,DE
        LD HL,LISTLEFT
        DEC (HL)
        JR LISTNEXT
LISTDONE:
        LD A,(LISTFOUND)
        OR A
        JP NZ,MENU
        LD HL,LISTNONE
        JP EXITMSG
; Z = match. B bounds the search to this fixed-width field.
LISTMATCH:
        LD DE,LISTTERM
        LD A,(DE)
        OR A
        RET Z
LISTTRY:PUSH BC
        PUSH HL
        LD DE,LISTTERM
LISTCHAR:
        LD A,(HL)
        CALL UPPER
        LD C,A
        LD A,(DE)
        CP C
        JR NZ,LISTMISS
        INC HL
        INC DE
        LD A,(DE)
        OR A
        JR Z,LISTHIT
        DJNZ LISTCHAR
LISTMISS:POP HL
        POP BC
        INC HL
        DJNZ LISTTRY
        LD A,1
        OR A
        RET
LISTHIT:POP HL
        POP BC
        RET
; SPT counts 128-byte records per logical track, including mixed media.
; Cylinder-unit records already include the second side.
LISTCAP:
        LD L,(IX+57)
        LD H,0
        BIT 0,(IX+58)
        JR Z,LISTMULT
        BIT 7,(IX+58)
        JR Z,LISTDOUBLE
        LD E,(IX+62)
        LD D,(IX+63)
        PUSH HL
        LD HL,WORKBUF
        ADD HL,DE
        LD A,(HL)
        CP 081H
        JR NZ,LISTUNIT
        INC HL
        LD E,(HL)
        LD D,0
        INC HL
        ADD HL,DE
LISTUNIT:LD A,(HL)
        CP 082H
        POP HL
        JR Z,LISTMULT
LISTDOUBLE:ADD HL,HL
LISTMULT:LD E,(IX+40)
        LD D,(IX+41)
        JP MULTIPLY
LISTTERM:DS 33
LISTFOUND:DB 0
LISTROOM:DB 0
LISTLEFT:DB 0
LISTFILTER:DB 'Find ID or description (Return lists all; capacity in bytes): ',0
LISTMORE:DB 'Return for more, Q or BREAK to stop: ',0
LISTNONE:DB 'No matching formats.',13,10,0
; O uses a private candidate descriptor. Its pool offsets still refer to
; WORKBUF. Destination descriptors in IMPORTBUF are never edited.
EXPORTMENU:
        LD HL,EXPORTSCOPE
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        OR A
        LD A,5
        JR Z,EXPORTNAME
        LD IX,WORKBUF+128
        LD A,(WORKBUF+8)
        OR A
        JP Z,NOIMPORT
        LD C,A
EXPORTFIND:
        PUSH IX
        POP HL
        LD DE,ANSWER
        LD B,8
EXPORTCMP:
        LD A,(DE)
        OR A
        JR Z,EXPORTPAD
        INC DE
        JR EXPORTCHAR
EXPORTPAD:LD A,' '
EXPORTCHAR:CP (HL)
        JR NZ,EXPORTNEXT
        INC HL
        DJNZ EXPORTCMP
        LD A,(DE)
        OR A
        JR NZ,EXPORTNEXT
        PUSH IX
        POP HL
        LD DE,EXPORTITEM
        LD BC,64
        LDIR
        LD A,4
        JR EXPORTNAME
EXPORTNEXT:
        LD DE,64
        ADD IX,DE
        DEC C
        JR NZ,EXPORTFIND
        JP NOIMPORT
EXPORTNAME:
        LD (ACTION),A
        LD HL,EXPORTDEST
        CALL ASKNAME
        ; The publication path returns to the menu, not a menu caller.
        LD HL,MENU
        PUSH HL
        LD A,(ACTION)
        CP 5
        JR NZ,EXPORTONE
        LD HL,EXPORTALL
        CALL PUTS
        JP DESTREADY
EXPORTONE:LD HL,EXPORTSINGLE
        CALL PUTS
        LD HL,EXPORTITEM
        LD B,8
        CALL NAMEOUT
        CALL CRLF
        JP DESTREADY
EXPORTREAD:
        LD A,(HADDEST)
        OR A
        JR Z,EXPORTEMPTY
        CALL TOINPUT
        JP READSOURCE
EXPORTEMPTY:
        LD HL,WORKBUF
        LD DE,FDFRAM
        LD BC,128
        LDIR
        XOR A
        LD (IMPORTBUF+8),A
        JR EXPORTREFS
EXPORTBASE:
        LD HL,FDFRAM
        LD DE,IMPORTBUF
        LD BC,(FDBLEN)
        LDIR
EXPORTREFS:
        LD HL,IMPORTBUF+128
        LD A,(IMPORTBUF+8)
        JP INITREFS
EXPORTMATCH:
        XOR A
        LD (ADDED),A
        LD (REPLACED),A
        INC A
        LD (REMAIN),A
        LD IX,EXPORTITEM
        JP MATCHREF
EXPORTREADY:JP SHOWCONFIRM
CANRENAME:
        LD A,(ACTION)
        CP 4
        LD A,D
        JR Z,EXPORTMUTABLE
        CP 05BH
        RET
EXPORTMUTABLE:
        ; The only editable export reference is the detached BIND descriptor.
        PUSH HL
        LD HL,BIND
        OR A
        SBC HL,DE
        POP HL
        SCF
        RET Z
        OR A
        RET
EXPORTITEM EQU BIND
EXPORTSCOPE:DB 'Export ID (Return for entire working catalogue): ',0
EXPORTDEST:DB 'Export destination .FDB or .FDF: ',0
EXPORTALL:DB 'Export entire working catalogue',13,10,0
EXPORTSINGLE:DB 'Export format ',0

EXPORTED:LD HL,DESTFCB
        CALL SHOWNAME
        LD HL,EXPORTOK
        JP PUTS
EXPORTOK:DB ' exported and verified.',13,10,0
