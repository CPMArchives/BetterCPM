; Three content recognizers share strict numeric/name conversion. All list
; text is bounded to 255 columns; malformed entries never become comments.
PARSELIN:
        LD HL,ENAME
        LD BC,27
        CALL ZERO
        LD HL,LISTLINE
        CALL SKIPSPAC
        LD (PARSESTA),HL
        CALL CATHEAD
        JP NZ,PARSEIGN
        LD HL,(PARSESTA)
        LD A,(LISTPEND)
        OR A
        JP NZ,PARSESEP
        LD DE,NAMEHEAD
        LD B,12
        PUSH HL
HEADERTE:
        LD A,(DE)
        CP (HL)
        JR NZ,NOTHEADE
        INC DE
        INC HL
        DJNZ HEADERTE
        POP HL
        LD DE,HEADERCO
        LD BC,256
        LDIR
        LD A,1
        LD (LISTPEND),A
        XOR A
        RET
NOTHEADE:
        POP HL
        LD A,(LISTFORM)
        CP 1
        JP Z,NATIVERO
        LD A,(HL)
        CP '-'
        JR NZ,NOPREFIX
        INC HL
        LD A,(HL)
        CP '-'
        JR NZ,NOCATALO
        INC HL
        LD A,(HL)
        CP '>'
        JP NZ,PARSEIGN
        LD HL,(PARSESTA)
        LD DE,LEGACYPR
        LD B,11
PREFIXTE:
        LD A,(DE)
        CP (HL)
        JP NZ,PARSEERR
        INC DE
        INC HL
        DJNZ PREFIXTE
        JP LABELLED
NOPREFIX:
        CP '0'
        JR C,NOCATALO
        CP '9'+1
        JP C,CATALOGR
NOCATALO:
        LD HL,(PARSESTA)
        ; An explicit '=' marks a labelled candidate. Other historical prose
        ; is ignored until a checksum-bearing row is recognized.
FINDLABE:
        LD A,(HL)
        OR A
        JR Z,PARSEIGN
        CP '='
        JR Z,LABELFOU
        INC HL
        JR FINDLABE
LABELFOU:
        LD HL,(PARSESTA)
        JP LABELLED
PARSEIGN:
        XOR A
        RET
PARSEERR:
        SCF
        RET
PARSESEP:
        XOR A
        LD (MAPCOUNT),A
        LD (MAPSEEN),A
        LD IX,COLUMNMA
        LD HL,LISTLINE
        LD C,0
SEPSPACE:
        LD A,(HL)
        OR A
        JP Z,SEPDONE
        CP ' '
        JP Z,SEPSKIP
        CP '-'
        JP NZ,PARSEERR
        LD A,(MAPCOUNT)
        CP 7
        JP NC,PARSEERR
        LD (IX+0),C
        LD B,0
SEPDASH:
        INC B
        INC C
        INC HL
        LD A,(HL)
        CP '-'
        JR Z,SEPDASH
        LD (IX+1),B
        PUSH HL
        PUSH BC
        LD HL,HEADERCO
        LD E,(IX+0)
        LD D,0
        ADD HL,DE
        CALL COPYTRIM
        CALL COLUMNID
        JR C,SEPBADPO
        LD (IX+2),A
        LD C,A
        LD B,1
SEPIDBIT:
        DEC C
        JR Z,SEPIDREA
        SLA B
        JR SEPIDBIT
SEPIDREA:
        LD A,(MAPSEEN)
        AND B
        JR NZ,SEPBADPO
        LD A,(MAPSEEN)
        OR B
        LD (MAPSEEN),A
        LD A,(IX+2)
        CP 1
        JR NZ,SEPEXT
        LD A,(IX+1)
        CP 8
        JR NZ,SEPBADPO
        JR SEPVALID
SEPEXT:
        CP 2
        JR NZ,SEPNUM
        LD A,(IX+1)
        CP 3
        JR NZ,SEPBADPO
        JR SEPVALID
SEPNUM:
        CP 3
        JR Z,SEPVALID
        LD B,4
        CP 7
        JR NZ,SEPHEXWI
        LD B,8
SEPHEXWI:
        LD A,(IX+1)
        CP B
        JR C,SEPBADPO
SEPVALID:
        LD HL,HEADERCO
        LD E,(IX+0)
        LD D,0
        ADD HL,DE
        LD B,(IX+1)
SEPHCLEAN:
        LD A,(HL)
        OR A
        JR Z,SEPHEND
        LD (HL),' '
        INC HL
        DJNZ SEPHCLEAN
SEPHEND:
        POP BC
        POP HL
        LD DE,3
        ADD IX,DE
        LD A,(MAPCOUNT)
        INC A
        LD (MAPCOUNT),A
        JP SEPSPACE
SEPSKIP:
        INC HL
        INC C
        JP SEPSPACE
SEPBADPO:
        POP BC
        POP HL
        XOR A
        LD (LISTPEND),A
        SCF
        RET
SEPDONE:
        XOR A
        LD (LISTPEND),A
        LD HL,HEADERCO
        CALL SKIPSPAC
        LD A,(HL)
        OR A
        JP NZ,PARSEERR
        LD A,(MAPSEEN)
        AND 7
        CP 7
        JP NZ,PARSEERR
        LD A,(MAPSEEN)
        AND 078H
        JP Z,PARSEERR
        LD A,1
        LD (LISTFORM),A
        XOR A
        RET
COLUMNID:
        LD DE,COLUMNNA
        LD C,1
COLNEXT:
        LD HL,FIELDTEX
COLCHAR:
        LD A,(DE)
        CP (HL)
        JR NZ,COLSKIP
        OR A
        JR Z,COLMATCH
        INC HL
        INC DE
        JR COLCHAR
COLSKIP:
        LD A,(DE)
        INC DE
        OR A
        JR NZ,COLSKIP
        INC C
        LD A,C
        CP 8
        JR C,COLNEXT
        SCF
        RET
COLMATCH:
        LD A,C
        OR A
        RET
; HL fixed field / B width -> FIELDTEX trimmed, B length, HL FIELDTEX.
COPYTRIM:
        LD DE,FIELDTEX
        LD C,B
COPYFIEL:
        LD A,(HL)
        OR A
        JR Z,COPYFI01
        LD (DE),A
        INC HL
        INC DE
        DJNZ COPYFIEL
COPYFI01:
        XOR A
        LD (DE),A
        LD HL,FIELDTEX
        CALL SKIPSPAC
        LD (FIELDSTA),HL
        LD B,0
COPYFI02:
        LD A,(HL)
        OR A
        JR Z,COPYFI03
        INC B
        INC HL
        JR COPYFI02
COPYFI03:
        LD A,B
        OR A
        JR Z,COPYFI05
        DEC HL
        LD A,(HL)
        CP ' '
        JR Z,COPYFI04
        CP 9
        JR NZ,COPYFI05
COPYFI04:
        LD (HL),0
        DEC B
        JR COPYFI03
COPYFI05:
        LD HL,(FIELDSTA)
        RET
NATIVERO:
        LD IX,COLUMNMA
        LD A,(MAPCOUNT)
        LD (COLLEFT),A
        LD HL,ENAME
        LD B,11
        LD A,' '
NRSPACEN:
        LD (HL),A
        INC HL
        DJNZ NRSPACEN
NRCOLUMN:
        LD HL,LISTLINE
        LD E,(IX+0)
        LD D,0
        ADD HL,DE
        LD B,(IX+1)
        CALL COPYTRIM
        LD A,(IX+2)
        CP 1
        JR Z,NRNAME
        CP 2
        JR Z,NREXT
        CP 3
        JR Z,NRRECS
        SUB 4
        LD (PARSEALG),A
        CALL HEXFIELD
        JP C,PARSEERR
        JR NRCLEAN
NRNAME:
        LD A,B
        OR A
        JP Z,PARSEERR
        LD DE,ENAME
        JR NRNAMECO
NREXT:
        LD A,B
        OR A
        JR Z,NRCLEAN
        LD DE,ENAME+8
NRNAMECO:
        LD C,B
        LD B,0
        LDIR
        JR NRCLEAN
NRRECS:
        CALL DECIMALF
        JP C,PARSEERR
        LD A,1
        LD (ESIZETYP),A
NRCLEAN:
        LD HL,LISTLINE
        LD E,(IX+0)
        LD D,0
        ADD HL,DE
        LD B,(IX+1)
NRCLEANB:
        LD A,(HL)
        OR A
        JR Z,NRNEXT
        LD (HL),' '
        INC HL
        DJNZ NRCLEANB
NRNEXT:
        LD DE,3
        ADD IX,DE
        LD A,(COLLEFT)
        DEC A
        LD (COLLEFT),A
        JP NZ,NRCOLUMN
        LD HL,LISTLINE
        CALL SKIPSPAC
        LD A,(HL)
        OR A
        JP NZ,PARSEERR
        CALL VALIDATE
        RET C
        LD A,1
        OR A
        RET
; Conversion uses checked shifts, so values cannot wrap past 32 bits.
DECIMALF:
        LD A,B
        OR A
        SCF
        RET Z
        LD (DIGPTR),HL
        LD A,B
        LD (DIGLEFT),A
        LD HL,ESIZE
        LD BC,4
        CALL ZERO
DECFIELD:
        LD HL,(DIGPTR)
        LD A,(HL)
        SUB '0'
        CP 10
        CCF
        RET C
        LD (DIGIT),A
        INC HL
        LD (DIGPTR),HL
        ; ESIZE*2 saved, then ESIZE*8 plus saved gives *10.
        LD HL,ESIZE
        CALL SHIFTNUM
        RET C
        LD HL,ESIZE
        LD DE,DECTWICE
        CALL COPY4
        LD HL,ESIZE
        CALL SHIFTNUM
        RET C
        LD HL,ESIZE
        CALL SHIFTNUM
        RET C
        LD HL,ESIZE
        LD DE,DECTWICE
        LD B,4
        OR A
DECADDBY:
        LD A,(DE)
        ADC A,(HL)
        LD (HL),A
        INC HL
        INC DE
        DJNZ DECADDBY
        RET C
        LD A,(DIGIT)
        LD HL,ESIZE
        ADD A,(HL)
        LD (HL),A
        JR NC,DECFIE01
        INC HL
        LD B,3
DECCARRY:
        INC (HL)
        JR NZ,DECFIE01
        INC HL
        DJNZ DECCARRY
        SCF
        RET
DECFIE01:
        LD A,(DIGLEFT)
        DEC A
        LD (DIGLEFT),A
        JR NZ,DECFIELD
        OR A
        RET
SHIFTNUM:
        SLA (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        RET
; B trimmed hex digit count, HL text, PARSEALG 0..3. Fixed conventional hex.
HEXFIELD:
        LD A,(PARSEALG)
        LD C,4
        CP 3
        JR NZ,HFWIDTH
        LD C,8
HFWIDTH:
        LD A,B
        CP C
        SCF
        RET NZ
        LD A,(PARSEALG)
        LD E,A
        LD D,0
        LD A,1
        INC E
HFBIT:
        DEC E
        JR Z,HFMASK
        ADD A,A
        JR HFBIT
HFMASK:
        LD E,A
        LD A,(EMASK)
        AND E
        SCF
        RET NZ
        LD A,(EMASK)
        OR E
        LD (EMASK),A
        LD A,(PARSEALG)
        ADD A,A
        LD E,A
        LD D,0
        PUSH HL
        LD HL,EVALUES
        ADD HL,DE
        LD A,C
        SRL A
        LD B,A
        LD E,A
        LD D,0
        ADD HL,DE
        EX DE,HL
        POP HL
HFBYTE:
        CALL NIBBLE
        RET C
        RLCA
        RLCA
        RLCA
        RLCA
        LD C,A
        INC HL
        CALL NIBBLE
        RET C
        OR C
        DEC DE
        LD (DE),A
        INC HL
        DJNZ HFBYTE
        OR A
        RET
NIBBLE:
        LD A,(HL)
        CP '0'
        JR C,NIBBAD
        CP '9'+1
        JR NC,NIBLETTE
        SUB '0'
        RET
NIBLETTE:
        AND 0DFH
        SUB 'A'
        CP 6
        JR NC,NIBBAD
        ADD A,10
        OR A
        RET
NIBBAD:
        SCF
        RET
; Reconstruct ordinary dotted 8.3 for the shared exact lexical validator.
VALIDATE:
        LD HL,ENAME
        LD DE,NAMETEXT
        LD B,8
        LD C,0
VNBASE:
        LD A,(HL)
        CP ' '
        JR Z,VNBASEEN
        LD (DE),A
        INC DE
        INC C
        INC HL
        DJNZ VNBASE
        JR VNEXT
VNBASEEN:
        LD A,(HL)
        CP ' '
        JP NZ,PARSEERR
        INC HL
        DJNZ VNBASEEN
VNEXT:
        LD A,(HL)
        CP ' '
        JR Z,VNEXTBLK
        LD A,'.'
        LD (DE),A
        INC DE
        INC C
        LD B,3
VNEXTBYT:
        LD A,(HL)
        CP ' '
        JR Z,VNEXTPAD
        LD (DE),A
        INC DE
        INC HL
        INC C
        DJNZ VNEXTBYT
        JR VNVALID
VNEXTBLK:
        LD B,3
VNEXTPAD:
        LD A,(HL)
        CP ' '
        JP NZ,PARSEERR
        INC HL
        DJNZ VNEXTPAD
VNVALID:
        LD HL,NAMETEXT
        LD B,C
        XOR A
        JP FP_VALIDATE
; Historical names: base optionally padded, dot optionally preceded by spaces,
; extension contiguous or padded. Returns HL at first label/size after name.
HISTNAME:
        LD DE,ENAME
        LD B,11
        LD A,' '
HNSPACE:
        LD (DE),A
        INC DE
        DJNZ HNSPACE
        LD DE,ENAME
        LD B,8
HNBASENE:
        LD A,(HL)
        CP '.'
        JR Z,HNDOT
        CP ' '
        JR Z,HNPAD
        CP 9
        JR Z,HNPAD
        OR A
        JP Z,PARSEERR
        LD (DE),A
        INC DE
        INC HL
        DJNZ HNBASENE
HNPAD:
        CALL SKIPSPAC
        LD A,(HL)
        CP '.'
        JR NZ,HNNODOT
HNDOT:
        INC HL
        LD DE,ENAME+8
        LD B,3
HNEXTNEX:
        LD A,(HL)
        OR A
        JR Z,HNEND
        CP ' '
        JR Z,HNEND
        CP 9
        JR Z,HNEND
        LD (DE),A
        INC DE
        INC HL
        DJNZ HNEXTNEX
HNEND:
        CALL SKIPSPAC
        OR A
        RET
HNNODOT:
        ; No-extension names require no dot; next token is label or K size.
        OR A
        RET
LABELLED:
        CALL HISTNAME
        RET C
        LD (HPTR),HL
        PUSH HL
        CALL VALIDATE
        POP HL
        RET C
LABELNEX:
        CALL SKIPSPAC
        LD A,(HL)
        OR A
        JP Z,LABELDON
        LD DE,FIELDTEX
        LD B,0
LABELWOR:
        LD A,(HL)
        CP '='
        JR Z,LABELW01
        CP ' '
        JR Z,LABELW01
        CP 9
        JR Z,LABELW01
        OR A
        JP Z,PARSEERR
        LD (DE),A
        INC DE
        INC HL
        INC B
        LD A,B
        CP 8
        JP NC,PARSEERR
        JR LABELWOR
LABELW01:
        XOR A
        LD (DE),A
        CALL SKIPSPAC
        LD A,(HL)
        CP '='
        JP NZ,PARSEERR
        INC HL
        CALL SKIPSPAC
        LD (HPTR),HL
        CALL LABELID
        RET C
        LD (PARSEALG),A
        LD HL,(HPTR)
        LD DE,HEXTEXT
        LD B,4
        CP 3
        JR NZ,LABELHEX
        LD B,8
LABELHEX:
        ; 16-bit values may contain whitespace between the two bytes.
        CALL NIBBLE
        RET C
        LD A,(HL)
        LD (DE),A
        INC DE
        INC HL
        DJNZ LABELH01
        JR LABELH02
LABELH01:
        LD A,(PARSEALG)
        CP 3
        JR Z,LABELHEX
        LD A,B
        CP 2
        JR NZ,LABELHEX
        CALL SKIPSPAC
        JR LABELHEX
LABELH02:
        LD (HPTR),HL
        LD HL,HEXTEXT
        LD B,4
        LD A,(PARSEALG)
        CP 3
        JR NZ,LABELCON
        LD B,8
LABELCON:
        CALL HEXFIELD
        RET C
        LD HL,(HPTR)
        JP LABELNEX
LABELDON:
        LD A,(EMASK)
        OR A
        JP Z,PARSEERR
        LD A,1
        OR A
        RET
LABELID:
        LD HL,FIELDTEX
        LD DE,LEGCRC
        LD B,4
LICRC:
        LD A,(DE)
        CP (HL)
        JR NZ,LINORMAL
        INC HL
        INC DE
        DJNZ LICRC
        XOR A
        RET
LINORMAL:
        CALL COLUMNID
        RET C
        SUB 4
        RET NC
        SCF
        RET
; Original indexed SIG/M catalog: vol.entry filename K HH HH description.
CATALOGR:
        LD A,(CATCRC)
        OR A
        JP Z,PARSEIGN
        ; A numeric prose line without a numeric index is not an entry.
CATVOL:
        LD A,(HL)
        CP '0'
        JR C,CATDOT
        CP '9'+1
        JR NC,CATDOT
        INC HL
        JR CATVOL
CATDOT:
        CP '.'
        JP NZ,PARSEIGN
        INC HL
        LD B,0
CATINDEX:
        LD A,(HL)
        CP '0'
        JR C,CATIND01
        CP '9'+1
        JR NC,CATIND01
        INC B
        INC HL
        JR CATINDEX
CATIND01:
        LD A,B
        OR A
        JP Z,PARSEIGN
        LD A,(HL)
        CP ' '
        JR Z,CATSPACE
        CP 9
        JP NZ,PARSEIGN
CATSPACE:
        CALL SKIPSPAC
        CALL HISTNAME
        RET C
        LD (HPTR),HL
        PUSH HL
        CALL VALIDATE
        POP HL
        RET C
        LD A,(CATORDER)
        OR A
        JR Z,CATSIZE
        CALL CATVALUE
        RET C
        LD HL,(HPTR)
        CALL SKIPSPAC
CATSIZE:
        LD (DIGPTR),HL
        LD B,0
CATK:
        LD A,(HL)
        CP '0'
        JR C,CATKEND
        CP '9'+1
        JR NC,CATKEND
        INC HL
        INC B
        JR CATK
CATKEND:
        CP 'K'
        JR Z,CATKSFX
        CP 'k'
        JR NZ,CATKNOSF
CATKSFX:
        INC HL
CATKNOSF:
        LD (HPTR),HL
        LD HL,(DIGPTR)
        CALL DECIMALF
        RET C
        LD A,2
        LD (ESIZETYP),A
        LD A,(CATORDER)
        OR A
        JR NZ,CATREADY
        LD HL,(HPTR)
        CALL SKIPSPAC
        CALL CATVALUE
        RET C
CATREADY:
        LD A,1
        OR A
        RET
CATVALUE:
        LD DE,HEXTEXT
        LD B,4
CATHEX:
        CALL NIBBLE
        RET C
        LD A,(HL)
        LD (DE),A
        INC DE
        INC HL
        DEC B
        JR Z,CATHEXEN
        LD A,B
        CP 2
        CALL Z,SKIPSPAC
        JR CATHEX
CATHEXEN:
        LD (HPTR),HL
CATCONVE:
        XOR A
        LD (PARSEALG),A
        LD HL,HEXTEXT
        LD B,4
        CALL HEXFIELD
        RET C
        LD A,1
        OR A
        RET
; Only an original INDEX/NAME/.../CRC heading enables catalog entries. This
; prevents a pre-CRC description beginning with hex letters becoming a CRC.
CATHEAD:
        LD DE,CATINDTX
        LD B,5
        PUSH HL
CATHTEST:
        LD A,(DE)
        CP (HL)
        JR NZ,CATHNO
        INC HL
        INC DE
        DJNZ CATHTEST
        LD A,(HL)
        CP ' '
        JR Z,CATHSTART
        CP 9
        JR NZ,CATHNO
CATHSTART:
        CALL SKIPSPAC
        LD DE,CATHNAME
        LD B,4
CATHNAM:
        LD A,(DE)
        CP (HL)
        JR NZ,CATHNO
        INC HL
        INC DE
        DJNZ CATHNAM
        POP DE
        XOR A
        LD (CATCRC),A
        LD (CATSIZEF),A
CATHTEXT:
        LD A,(HL)
        OR A
        JR Z,CATHDONE
        CP 'S'
        JR NZ,CATHCRC
        INC HL
        LD A,(HL)
        CP 'I'
        JR NZ,CATHTEXT
        LD A,1
        LD (CATSIZEF),A
        JR CATHTEXT
CATHCRC:
        CP 'C'
        JR NZ,CATHNEXT
        INC HL
        LD A,(HL)
        CP 'R'
        JR NZ,CATHTEXT
        INC HL
        LD A,(HL)
        CP 'C'
        JR NZ,CATHTEXT
        LD A,1
        LD (CATCRC),A
        LD A,(CATSIZEF)
        XOR 1
        LD (CATORDER),A
CATHNEXT:
        INC HL
        JR CATHTEXT
CATHDONE:
        LD A,1
        OR A
        RET
CATHNO:
        POP HL
        XOR A
        RET
CATINDTX: DB 'INDEX'
CATHNAME: DB 'NAME'
CATCRC: DB 0
CATORDER: DB 0
CATSIZEF: DB 0
COLUMNNA: DB 'NAME',0,'EXT',0,'RECS',0,'CRCK',0,'CRCK5',0,'CHEK',0,'CRC32',0
LEGCRC: DB 'CRC',0
PARSESTA: DW 0
HEADERCO: DS 256
COLUMNMA: DS 21
MAPCOUNT: DB 0
MAPSEEN: DB 0
COLLEFT: DB 0
FIELDTEX: DS 256
FIELDSTA: DW 0
PARSEALG: DB 0
NAMETEXT: DS 13
HEXTEXT: DS 8
HPTR: DW 0
DIGPTR: DW 0
DIGLEFT: DB 0
DIGIT: DB 0
DECTWICE: DS 4
