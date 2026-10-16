; Full-tail parser. A drive-only operand denotes protected system tracks;
; an exact 8.3 filename denotes a package. No CCP FCB trust or selector syntax.
PARSEARGS:
        LD A,(TAIL)
        LD C,A
        LD HL,TAIL+1
        CALL PASKIP
        JP C,PABAD
        LD DE,XARG1
        CALL XTOKEN
        JP C,PABAD
        LD (XKIND),A
        CALL PASKIP
        JR NC,XSECONDARG
        LD A,(XKIND)
        CP 1
        JP NZ,PABAD
        LD HL,XDEFAULT
        LD DE,XARG2
        LD BC,36
        LDIR
        LD A,(XARG1)
        DEC A
        LD (SOURCEDEV),A
        JP XTOFILE
XSECONDARG:
        LD DE,XARG2
        CALL XTOKEN
        JP C,PABAD
        LD (XSECOND),A
        CALL PASKIP
        JP NC,PABAD
        LD A,(XKIND)
        OR A
        JR Z,XFROMFILE
        LD A,(XARG1)
        DEC A
        LD (SOURCEDEV),A
        LD A,(XSECOND)
        OR A
        JR Z,XTOFILE
        LD A,(XARG2)
        DEC A
        CP 4
        JR NC,PABAD
        OR A
        JR Z,PABAD
        LD (DEST),A
        CALL LOADDISK
        RET Z
        LD (STATUS),A
        LD A,3
        OR A
        RET
XFROMFILE:
        LD A,(XSECOND)
        CP 1
        JR NZ,PABAD
        LD A,(XARG2)
        DEC A
        CP 4
        JR NC,PABAD
        OR A
        JR Z,PABAD
        LD (DEST),A
        LD A,1
        LD (FILEMODE),A
        JP LOADFILE
XTOFILE:
        LD A,1
        LD (XEXPORT),A
        CALL LOADDISK
        RET Z
        LD (STATUS),A
        LD A,3
        OR A
        RET
PABAD: LD A,1
        OR A
        RET
PASKIP:LD A,C
        OR A
        SCF
        RET Z
        LD A,(HL)
        CP ' '
        JR NZ,PANONSP
        INC HL
        DEC C
        JR PASKIP
PANONSP:OR A
        RET
; HL/C counted tail, DE 36-byte private FCB. Return A=1 drive-only,
; A=0 file, carry invalid. At least one space separates operands.
XTOKEN:
        LD (XTARG),DE
        PUSH HL
        PUSH BC
        PUSH DE
        LD B,36
        XOR A
XTZERO:LD (DE),A
        INC DE
        DJNZ XTZERO
        POP DE
        INC DE
        LD B,11
        LD A,' '
XTSPACE:LD (DE),A
        INC DE
        DJNZ XTSPACE
        POP BC
        POP HL
        LD DE,(XTARG)
        LD A,C
        CP 2
        JR C,XTNAME
        INC HL
        LD A,(HL)
        DEC HL
        CP ':'
        JR NZ,XTNAME
        LD A,(HL)
        AND 05FH
        SUB 'A'
        CP 4
        JP NC,XTFAIL
        INC A
        LD (DE),A
        INC HL
        INC HL
        DEC C
        DEC C
XTNAME:INC DE
        LD B,8
        XOR A
        LD (XDOT),A
        LD (XCOUNT),A
XTLOOP:LD A,C
        OR A
        JR Z,XTEND
        LD A,(HL)
        CP ' '
        JR Z,XTEND
        CP '.'
        JR Z,XTDOT
        CALL XTCHAR
        JR C,XTFAIL
        LD (XCHAR),A
        LD A,B
        OR A
        JR Z,XTFAIL
        LD A,(XCHAR)
        LD (DE),A
        INC DE
        DEC B
        LD A,(XCOUNT)
        INC A
        LD (XCOUNT),A
XTNEXT:INC HL
        DEC C
        JR XTLOOP
XTDOT: LD A,(XDOT)
        OR A
        JR NZ,XTFAIL
        LD A,(XCOUNT)
        OR A
        JR Z,XTFAIL
        LD A,1
        LD (XDOT),A
        XOR A
        LD (XCOUNT),A
        LD DE,(XTARG)
        PUSH HL
        LD HL,9
        ADD HL,DE
        EX DE,HL
        POP HL
        LD B,3
        JR XTNEXT
XTEND: LD A,(XCOUNT)
        OR A
        JR Z,XTEMPTY
        XOR A
        RET
XTEMPTY:
        LD A,(XDOT)
        OR A
        JR NZ,XTFAIL
        LD DE,(XTARG)
        LD A,(DE)
        OR A
        JR Z,XTFAIL
        LD A,1
        OR A
        RET
XTFAIL:SCF
        RET
; Preserve parser registers while rejecting separators, wildcards and options.
XTCHAR:CP 33
        JR C,XTFAIL
        CP 127
        JR NC,XTFAIL
        CP 'a'
        JR C,XTCHECK
        CP 'z'+1
        JR NC,XTCHECK
        AND 05FH
XTCHECK:PUSH HL
        PUSH BC
        LD HL,XTINVALID
XTCLOOP:LD B,(HL)
        INC HL
        INC B
        DEC B
        JR Z,XTCGOOD
        CP B
        JR Z,XTCBAD
        JR XTCLOOP
XTCGOOD:POP BC
        POP HL
        OR A
        RET
XTCBAD:POP BC
        POP HL
        SCF
        RET
XTINVALID:DB '<>,;:=?*[]/\|',34,0
XTARG: DW 0
XKIND: DB 0
XSECOND:DB 0
XDOT: DB 0
XCOUNT:DB 0
XCHAR: DB 0
XEXPORT:DB 0
XARG1: DS 36
XARG2: DS 36

XDEFAULT:DB 0,'SYSTEM  SYS'
        DS 24
