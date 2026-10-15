; ED invocation only: capture caller DU once, then validate both operands.
; No drive/user changes or file operations. Carry means invalid syntax.
EI_PARSE:
        LD C,25
        CALL 5
        LD (EI_CDRV),A
        LD E,255
        LD C,32
        CALL 5
        LD (EI_CUSR),A
        LD HL,81H
        LD (EI_CUR),HL
        LD A,(80H)
        LD (EI_LEFT),A
        CALL EI_NEXT
        RET C
        OR A
        JP Z,EI_BAD
        CALL EI_LOC
        RET C
        LD A,(EI_DRV)
        LD (EI_SDRV),A
        LD (EI_ODRV),A
        LD A,(EI_USR)
        LD (EI_SUSR),A
        LD (EI_OUSR),A
        CALL EI_FILE
        RET C
        CALL EI_NEXT
        RET C
        OR A
        RET Z
        CALL EI_LOC
        RET C
        LD A,(EI_QUAL)
        OR A
        JP Z,EI_BAD
        LD HL,(EI_REST)
        LD A,(HL)
        OR A
        JP NZ,EI_BAD
        LD A,(EI_DRV)
        LD (EI_ODRV),A
        LD A,(EI_USR)
        LD (EI_OUSR),A
        CALL EI_NEXT
        RET C
        OR A
        JP NZ,EI_BAD
        RET
EI_BAD:
        SCF
        RET
EI_NEXT:
        LD HL,(EI_CUR)
        LD A,(EI_LEFT)
        LD B,A
EI_SKIP:
        LD A,B
        OR A
        JP Z,EI_EMPTY
        LD A,(HL)
        CP ' '
        JP Z,EI_SP
        CP 9
        JP NZ,EI_COPY
EI_SP:
        INC HL
        DEC B
        JP EI_SKIP
EI_COPY:
        LD DE,EI_TOKEN
        LD C,0
EI_CHAR:
        LD A,B
        OR A
        JP Z,EI_DONE
        LD A,(HL)
        CP ' '
        JP Z,EI_DONE
        CP 9
        JP Z,EI_DONE
        LD A,C
        CP 16
        JP NC,EI_BAD
        LD A,(HL)
        OR A
        JP Z,EI_BAD
        LD (DE),A
        INC DE
        INC HL
        INC C
        DEC B
        JP EI_CHAR
EI_DONE:
        XOR A
        LD (DE),A
        LD A,C
        JP EI_SAVE
EI_EMPTY:
        XOR A
        LD (EI_TOKEN),A
EI_SAVE:
        LD (EI_CUR),HL
        LD C,A
        LD A,B
        LD (EI_LEFT),A
        LD A,C
        OR A
        RET
EI_LOC:
        LD A,(EI_CDRV)
        LD (EI_DRV),A
        LD A,(EI_CUSR)
        LD (EI_USR),A
EI_LOCREST:
        XOR A
        LD (EI_QUAL),A
        LD HL,EI_TOKEN
        LD (EI_REST),HL
        LD DE,EI_TOKEN
EI_COLON:
        LD A,(DE)
        OR A
        RET Z
        CP ':'
        JP Z,EI_PREFIX
        INC DE
        JP EI_COLON
EI_PREFIX:
        LD HL,EI_TOKEN
        LD A,(HL)
        CALL EI_UP
        CP 'A'
        JP C,EI_USER
        CP 'P'+1
        JP NC,EI_BAD
        SUB 'A'
        LD (EI_DRV),A
        LD A,1
        LD (EI_QUAL),A
        INC HL
EI_USER:
        XOR A
        LD (EI_NUM),A
        LD (EI_DIG),A
EI_DIGIT:
        LD A,(HL)
        CP ':'
        JP Z,EI_PEND
        CP '0'
        JP C,EI_BAD
        CP '9'+1
        JP NC,EI_BAD
        SUB '0'
        LD C,A
        LD A,(EI_NUM)
        CP 4
        JP NC,EI_BAD
        LD E,A
        ADD A,A
        ADD A,A
        ADD A,E
        ADD A,A
        ADD A,C
        CP 32
        JP NC,EI_BAD
        LD (EI_NUM),A
        LD A,1
        LD (EI_DIG),A
        LD (EI_QUAL),A
        INC HL
        JP EI_DIGIT
EI_PEND:
        LD A,(EI_QUAL)
        OR A
        JP Z,EI_BAD
        LD A,(EI_DIG)
        OR A
        JP Z,EI_REND
        LD A,(EI_NUM)
        LD (EI_USR),A
EI_REND:
        INC HL
        LD (EI_REST),HL
        OR A
        RET
EI_FILE:
        LD HL,EI_FCB
        LD B,36
        XOR A
EI_ZERO:
        LD (HL),A
        INC HL
        DJNZ EI_ZERO
        LD HL,EI_FCB+1
        LD B,11
        LD A,' '
EI_BLANK:
        LD (HL),A
        INC HL
        DJNZ EI_BLANK
        LD A,(EI_SDRV)
        INC A
        LD (EI_FCB),A
        LD HL,(EI_REST)
        LD DE,EI_FCB+1
        LD B,8
        LD C,0
EI_NAME:
        LD A,(HL)
        OR A
        JP Z,EI_FEND
        CP '.'
        JP Z,EI_DOT
        CALL EI_FCHR
        RET C
        LD (DE),A
        INC DE
        INC HL
        INC C
        DJNZ EI_NAME
        LD A,(HL)
        OR A
        JP Z,EI_FEND
        CP '.'
        JP NZ,EI_BAD
EI_DOT:
        LD A,C
        OR A
        JP Z,EI_BAD
        INC HL
        LD DE,EI_FCB+9
        LD B,3
EI_EXT:
        LD A,(HL)
        OR A
        RET Z
        CALL EI_FCHR
        RET C
        LD (DE),A
        INC DE
        INC HL
        DJNZ EI_EXT
        LD A,(HL)
        OR A
        JP NZ,EI_BAD
        RET
EI_FEND:
        LD A,C
        OR A
        JP Z,EI_BAD
        RET
EI_FCHR:
        CP 33
        JP C,EI_BAD
        CP 127
        JP NC,EI_BAD
        LD (EI_CH),A
        PUSH HL
        LD HL,EI_FORB
EI_CHECK:
        LD A,(HL)
        OR A
        JP Z,EI_ALLOW
        LD A,(EI_CH)
        CP (HL)
        JP Z,EI_NOCHAR
        INC HL
        JP EI_CHECK
EI_NOCHAR:
        POP HL
        JP EI_BAD
EI_ALLOW:
        POP HL
        LD A,(EI_CH)
        CALL EI_UP
        OR A
        RET
EI_UP:
        CP 'a'
        RET C
        CP 'z'+1
        RET NC
        SUB 32
        OR A
        RET
EI_FORB: DB '<>.,;:=?*[]/\',34,'|',0
EI_CH: DB 0
EI_CDRV: DB 0
EI_CUSR: DB 0
EI_SDRV: DB 0
EI_SUSR: DB 0
EI_ODRV: DB 0
EI_OUSR: DB 0
EI_DRV: DB 0
EI_USR: DB 0
EI_QUAL: DB 0
EI_NUM: DB 0
EI_DIG: DB 0
EI_CUR: DW 0
EI_REST: DW 0
EI_LEFT: DB 0
EI_TOKEN: DS 17
EI_FCB: DS 36
