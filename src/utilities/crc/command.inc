; Private command tail and token boundaries. No services on query path.
TOKENIZE:
        LD A,(0080H)
        CP 128
        JR C,TOKVALID
        SCF
        RET
TOKVALID:
        LD C,A
        LD B,0
        LD HL,0081H
        LD DE,TAIL
        LD A,C
        OR A
        JR Z,TOKEND
        LDIR
TOKEND:
        XOR A
        LD (DE),A
        LD HL,TAIL
        LD IX,TOKENS
TOKSPACE:
        LD A,(HL)
        OR A
        RET Z
        CP ' '
        JR Z,TOKSKIP
        CP 9
        JR NZ,TOKSTART
TOKSKIP:
        INC HL
        JR TOKSPACE
TOKSTART:
        LD (IX+0),L
        LD (IX+1),H
        LD B,0
TOKBYTE:
        LD A,(HL)
        OR A
        JR Z,TOKSAVE
        CP ' '
        JR Z,TOKSAVE
        CP 9
        JR Z,TOKSAVE
        CP 'a'
        JR C,TOKUP
        CP 'z'+1
        JR NC,TOKUP
        SUB 32
        LD (HL),A
TOKUP:
        INC B
        INC HL
        JR TOKBYTE
TOKSAVE:
        LD (IX+2),B
        INC IX
        INC IX
        INC IX
        LD A,(TOKCOUNT)
        INC A
        LD (TOKCOUNT),A
        LD A,(HL)
        OR A
        RET Z
        LD (HL),0
        INC HL
        JR TOKSPACE
GETTOKEN:
        LD A,(TOKINDEX)
        LD E,A
        LD D,0
        LD HL,TOKENS
        ADD HL,DE
        ADD HL,DE
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD B,(HL)
        EX DE,HL
        LD (TOKENPTR),HL
        LD A,B
        LD (TOKENLEN),A
        RET
; Table matching supports exact flags and value prefixes ending '='.
OPTION:
        LD IX,OPTIONS
OPTNEXT:
        LD C,(IX+0)
        LD A,C
        OR A
        SCF
        RET Z
        LD HL,(TOKENPTR)
        LD A,(TOKENLEN)
        LD B,A
        LD D,(IX+1)
        INC IX
        INC IX
        LD A,B
        CP C
        JR C,OPTSKIP
OPTCHAR:
        LD A,(IX+0)
        CP (HL)
        JR NZ,OPTSKIP
        INC IX
        INC HL
        DEC B
        DEC C
        JR NZ,OPTCHAR
        ; Value options are IDs 5,6,8. Others must consume entire token.
        LD A,D
        CP 5
        JR Z,OPTGOOD
        CP 6
        JR Z,OPTGOOD
        CP 8
        JR Z,OPTGOOD
        LD A,B
        OR A
        JR NZ,OPTNEXT
OPTGOOD:
        LD A,D
        OR A
        RET
OPTSKIP:
        INC IX
        DEC C
        JR NZ,OPTSKIP
        JR OPTNEXT
QUERIES:
        LD A,(TOKCOUNT)
        OR A
        RET Z
        XOR A
        LD (QVER),A
        LD (TOKINDEX),A
QUERYLOO:
        CALL GETTOKEN
        CALL OPTION
        JR C,QUERYNEX
        CP 11
        JR Z,QUERYHEL
        CP 12
        JR NZ,QUERYNEX
        LD (QVER),A
QUERYNEX:
        LD A,(TOKINDEX)
        INC A
        LD (TOKINDEX),A
        LD B,A
        LD A,(TOKCOUNT)
        CP B
        JR NZ,QUERYLOO
        LD A,(QVER)
        OR A
        RET Z
        LD HL,VERSIONT
        JR QUERYPRI
QUERYHEL:
        LD HL,HELPTEXT
QUERYPRI:
        CALL TEXT
        LD A,1
        OR A
        RET
COMMAND:
        LD HL,FIELDTAB
        LD (ALGWRITE),HL
        XOR A
        LD (TOKINDEX),A
        LD HL,OPERANDS
        LD (OPERPTR),HL
CMDLOOP:
        LD A,(TOKINDEX)
        LD B,A
        LD A,(TOKCOUNT)
        CP B
        JP Z,CMDFINIS
        CALL GETTOKEN
        LD A,(HL)
        CP '/'
        JP NZ,CMDOPER
        CALL OPTION
        RET C
        CP 13
        JR C,CMDOLDAL
        SUB 8
        JR CMDALGIN
CMDOLDAL:
        CP 5
        JR NC,CMDOTHER
CMDALGIN:
        DEC A
        LD (CMDALGID),A
        LD B,A
        LD A,1
        JR Z,CMDALGSE
CMDALGBI:
        ADD A,A
        DJNZ CMDALGBI
CMDALGSE:
        LD B,A
        LD A,(ALGSEL)
        AND B
        JP NZ,CMDNEXT
        LD A,(ALGSEL)
        OR B
        LD (ALGSEL),A
        CALL APPENDAL
        JP CMDNEXT
CMDOTHER:
        CP 7
        JR NZ,CMDNOTLE
        LD (LEGACY),A
        JP CMDNEXT
CMDNOTLE:
        CP 9
        JR NZ,CMDNOTCH
        LD (CHECK),A
        JP CMDNEXT
CMDNOTCH:
        CP 10
        JR NZ,CMDVALUE
        LD (NARROW),A
        JP CMDNEXT
CMDVALUE:
        LD (VALUEID),A
        CALL DESTINAT
        RET C
        LD A,(VALUEID)
        CP 5
        JR NZ,CMDLOCAL
        LD HL,FS_FCB
        LD DE,MASTER
        LD BC,36
        LDIR
        LD A,(DESTDRIV)
        LD (MASTER+36),A
        LD A,(DESTUSER)
        LD (MASTER+37),A
        LD A,1
        LD (MASTSET),A
        JP CMDNEXT
CMDLOCAL:
        CP 6
        LD DE,LOCAL
        JR Z,CMDVALCO
        LD A,1
        LD (CHECK),A
        LD (REFSET),A
        LD DE,REFNAME
CMDVALCO:
        LD HL,FS_FCB
        LD BC,36
        LDIR
        LD A,(VALUEID)
        CP 6
        JR NZ,CMDNEXT
        LD A,1
        LD (LOCALSET),A
        JR CMDNEXT
CMDOPER:
        CALL ADDOPERA
        RET C
CMDNEXT:
        LD A,(TOKINDEX)
        INC A
        LD (TOKINDEX),A
        JP CMDLOOP
CMDFINIS:
        LD A,(CHECK)
        OR A
        JR Z,CMDDEFAU
        LD A,(MASTSET)
        LD B,A
        LD A,(LOCALSET)
        OR B
        SCF
        RET NZ
CMDDEFAU:
        LD A,(ALGSEL)
        OR A
        JR NZ,CMDLEGAC
        LD A,255
        LD (ALGSEL),A
        LD HL,ALGTEMPL
        LD DE,FIELDTAB
        LD BC,50
        LDIR
CMDLEGAC:
        LD A,(LEGACY)
        OR A
        JR Z,CMDIMPLI
        LD A,1
        LD (ALGSEL),A
        LD HL,ALGTEMPL
        LD DE,FIELDTAB
        LD BC,6
        LDIR
        XOR A
        LD (DE),A
        INC DE
        LD (DE),A
CMDIMPLI:
        LD A,(OPERCOUN)
        OR A
        RET NZ
        LD HL,BC_ALL
        LD B,3
        JP ADDOPERA
DESTINAT:
        LD A,B
        OR A
        SCF
        RET Z
        LD A,(VALUEID)
        CP 5
        JR Z,DESTPARS
        PUSH HL
        PUSH BC
DESTCOLO:
        LD A,(HL)
        CP ':'
        JR Z,DESTBAD
        INC HL
        DJNZ DESTCOLO
        POP BC
        POP HL
DESTPARS:
        LD A,(ORIGDRIV)
        LD D,A
        LD A,(ORIGUSER)
        LD E,A
        CALL DU_PARSE
        RET C
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JR C,DESTBAD
        LD A,D
        LD (DESTDRIV),A
        LD A,E
        LD (DESTUSER),A
        CALL DU_NEXT
        JR NC,DESTBAD
        POP BC
        POP HL
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE
        JR C,DESTBAD
        POP BC
        POP HL
        LD DE,FS_FCB
        CALL BC_PFCB
        OR A
        RET
DESTBAD:
        POP BC
        POP HL
        SCF
        RET
ADDOPERA:
        LD A,(ORIGDRIV)
        LD D,A
        LD A,(ORIGUSER)
        LD E,A
        CALL FS_PARSE
        RET C
        LD HL,DU_MAP
        LD DE,(OPERPTR)
        LD BC,64
        LDIR
        LD HL,FS_FCB+1
        LD BC,11
        LDIR
        LD A,(FS_MASK)
        LD (DE),A
        INC DE
        LD (OPERPTR),DE
        LD A,(OPERCOUN)
        INC A
        LD (OPERCOUN),A
        LD BC,0
ADDDU:
        CALL DU_NEXT
        JR NC,ADDDUFOU
        OR A
        RET
ADDDUFOU:
        PUSH BC
        DEC BC
        PUSH BC
        LD HL,DUSEEN
        CALL MAPBIT
        LD E,A
        AND (HL)
        JR NZ,ADDDUNEX
        LD A,(HL)
        OR E
        LD (HL),A
        LD HL,(DUCOUNT)
        ADD HL,HL
        LD DE,DUORDER
        ADD HL,DE
        POP DE
        LD (HL),E
        INC HL
        LD (HL),D
        LD HL,(DUCOUNT)
        INC HL
        LD (DUCOUNT),HL
        JR ADDDURES
ADDDUNEX:
        POP BC
ADDDURES:
        POP BC
        JR ADDDU
; HL map / BC logical index -> HL containing byte, A bit. BC/DE scratch.
MAPBIT:
        LD A,C
        AND 7
        LD E,A
        LD A,1
        INC E
MAPSHIFT:
        DEC E
        JR Z,MAPOFFSE
        ADD A,A
        JR MAPSHIFT
MAPOFFSE:
        SRL B
        RR C
        SRL B
        RR C
        SRL B
        RR C
        ADD HL,BC
        RET
OPTIONS:
        DB 5,1,'/CRCK'
        DB 6,2,'/CRCK5'
        DB 5,3,'/CHEK'
        DB 6,4,'/CRC32'
        DB 6,5,'/FILE='
        DB 7,6,'/LOCAL='
        DB 7,7,'/LEGACY'
        DB 7,8,'/CHECK='
        DB 6,9,'/CHECK'
        DB 3,10,'/40'
        DB 5,11,'/HELP'
        DB 4,12,'/VER'
        DB 5,13,'/SUM8'
        DB 6,14,'/SUM16'
        DB 6,15,'/KERM6'
        DB 7,16,'/KERM12'
        DB 0
; Explicit sources cannot also be destinations. Wildcard exclusions are
; handled during traversal, including declined existing destinations.
COLLIDE:
        LD HL,OPERANDS
        LD A,(OPERCOUN)
        LD (COLLLEFT),A
COLLLOOP:
        LD (COLLPTR),HL
        LD BC,64
        ADD HL,BC
        LD (COLLNAME),HL
        LD A,(LOCALSET)
        OR A
        JR Z,COLLMAST
        LD DE,LOCAL+1
        CALL CMPNAME
        SCF
        RET Z
COLLMAST:
        LD A,(MASTSET)
        OR A
        JR Z,COLLNEXT
        LD HL,(COLLNAME)
        LD DE,MASTER+1
        CALL CMPNAME
        JR NZ,COLLNEXT
        LD A,(MASTER+36)
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD A,(MASTER+37)
        LD E,A
        LD D,0
        ADD HL,DE
        LD B,H
        LD C,L
        LD HL,(COLLPTR)
        CALL MAPBIT
        AND (HL)
        SCF
        RET NZ
COLLNEXT:
        LD HL,(COLLPTR)
        LD DE,76
        ADD HL,DE
        LD A,(COLLLEFT)
        DEC A
        LD (COLLLEFT),A
        JR NZ,COLLLOOP
        OR A
        RET
COLLLEFT: DB 0
COLLPTR: DW 0
COLLNAME: DW 0
QVER: DB 0
VALUEID: DB 0
DESTDRIV: DB 0
DESTUSER: DB 0

; Append a newly selected algorithm's descriptor; duplicates never reach here.
; CMDALGID is the canonical accumulator index (0..7).
APPENDAL:
        LD A,(CMDALGID)
        LD L,A
        LD H,0
        ADD HL,HL
        LD D,H
        LD E,L
        ADD HL,HL
        ADD HL,DE
        LD DE,ALGTEMPL
        ADD HL,DE
        LD DE,(ALGWRITE)
        LD BC,6
        LDIR
        LD (ALGWRITE),DE
        XOR A
        LD (DE),A
        INC DE
        LD (DE),A
        RET
CMDALGID: DB 0
ALGWRITE: DW 0
