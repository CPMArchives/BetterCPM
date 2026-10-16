; Complete, validated bounded sequences -> typed SCRN controls.
; Numeric parameters saturate at 65535; list capacity is sixteen words.
; No hardware addresses or host escape generation belong in this dispatcher.
AC_DISP:
        LD A,(AN_COUNT)
        CP 2
        JP Z,AC_ESC
        LD A,(AN_BUFFER+2)
        CP '?'
        JP Z,AC_VIS
        LD A,(AN_COUNT)
        SUB 3
        LD (AC_LEFT),A
        LD HL,AN_BUFFER+2
        LD (AC_PTR),HL
        LD HL,0
        LD (AC_WORD),HL
        XOR A
        LD (AC_NPAR),A
AC_PARSE:
        LD A,(AC_LEFT)
        OR A
        JR Z,AC_LAST
        DEC A
        LD (AC_LEFT),A
        LD HL,(AC_PTR)
        LD A,(HL)
        INC HL
        LD (AC_PTR),HL
        CP ';'
        JR Z,AC_SEMI
        SUB '0'
        LD (AC_DIGIT),A
        LD HL,(AC_WORD)
        LD B,H
        LD C,L
        ADD HL,HL
        JR C,AC_SAT
        ADD HL,HL
        JR C,AC_SAT
        ADD HL,BC
        JR C,AC_SAT
        ADD HL,HL
        JR C,AC_SAT
        LD A,(AC_DIGIT)
        LD E,A
        LD D,0
        ADD HL,DE
        JR NC,AC_STORE
AC_SAT:
        LD HL,65535
AC_STORE:
        LD (AC_WORD),HL
        JR AC_PARSE
AC_SEMI:
        CALL AC_PUT
        OR A
        RET NZ
        JR AC_PARSE
AC_LAST:
        CALL AC_PUT
        OR A
        RET NZ
        LD A,(AN_COUNT)
        DEC A
        LD E,A
        LD D,0
        LD HL,AN_BUFFER
        ADD HL,DE
        LD A,(HL)
        LD (AC_FINAL),A
        SUB 'A'
        CP 4
        JR C,AC_MOVE
        LD A,(AC_FINAL)
        CP 'H'
        JP Z,AC_POS
        CP 'f'
        JP Z,AC_POS
        CP 'J'
        JP Z,AC_ERASE
        CP 'K'
        JP Z,AC_ERASE
        CP 'm'
        JP Z,AC_SGR
        CP 'r'
        JR Z,AC_AREA
        CP 's'
        JP Z,AC_SAVE
        CP 'u'
        JP Z,AC_REST
        RET
AC_PUT:
        LD A,(AC_NPAR)
        CP 16
        JR NC,AC_FULL
        ADD A,A
        LD E,A
        LD D,0
        LD HL,AC_PARAMS
        ADD HL,DE
        LD DE,(AC_WORD)
        LD (HL),E
        INC HL
        LD (HL),D
        LD A,(AC_NPAR)
        INC A
        LD (AC_NPAR),A
        LD HL,0
        LD (AC_WORD),HL
        XOR A
        RET
AC_FULL:
        LD A,255
        RET
AC_ONE:
        LD A,(AC_NPAR)
        CP 1
        RET
AC_MOVE:
        LD B,A
        CALL AC_ONE
        RET NZ
        LD HL,(AC_PARAMS)
        LD A,17
        JP AN_RAW
AC_TWO:
        LD A,(AC_NPAR)
        CP 3
        RET NC
        LD DE,0
        CP 2
        JR NZ,AC_FIRST
        LD DE,(AC_PARAMS+2)
AC_FIRST:
        LD HL,(AC_PARAMS)
        SCF
        RET
AC_POS:
        CALL AC_TWO
        RET NC
        LD A,18
        JP AN_RAW
AC_AREA:
        CALL AC_TWO
        RET NC
        LD A,22
        JP AN_RAW
AC_ERASE:
        CALL AC_ONE
        RET NZ
        LD HL,(AC_PARAMS)
        LD A,H
        OR A
        RET NZ
        LD A,L
        CP 3
        RET NC
        LD C,A
        LD B,0
        LD A,(AC_FINAL)
        CP 'K'
        JR Z,AC_EGO
        INC B
AC_EGO:
        LD A,19
        JP AN_RAW
AC_SGR:
        LD A,(AC_NPAR)
        LD C,A
        LD HL,AC_PARAMS
        CALL AP_ENTRY
        OR A
        RET NZ
        LD A,20
        JP AN_RAW
AC_ESC:
        LD A,(AN_BUFFER+1)
        CP '7'
        JP Z,AC_SAVE
        CP '8'
        JP Z,AC_REST
        LD B,0
        CP 'D'
        JR Z,AC_INDEX
        INC B
        CP 'E'
        JR Z,AC_INDEX
        INC B
AC_INDEX:
        LD A,24
        JP AN_RAW
AC_VIS:
        LD A,(AN_BUFFER+5)
        CP 'h'
        LD C,0
        JR NZ,AC_HIDE
        INC C
AC_HIDE:
        LD A,C
        LD (AN_VISIBLE),A
        LD A,15
        JP AN_RAW
AC_SAVE:
        LD B,0
        LD A,23
        CALL AN_RAW
        OR A
        RET NZ
        LD HL,AP_VALUE
        LD DE,AC_SAVED
        LD BC,9
        LDIR
        LD A,1
        LD (AC_VALID),A
        RET
AC_REST:
        LD A,(AC_VALID)
        OR A
        JR Z,AC_DEFAULT
        LD B,1
        LD A,23
        CALL AN_RAW
        OR A
        RET NZ
        LD HL,AC_SAVED
        LD DE,AP_VALUE
        LD BC,9
        LDIR
        RET
AC_DEFAULT:
        LD HL,AP_VALUE
        LD B,9
        XOR A
AC_ZERO:
        LD (HL),A
        INC HL
        DJNZ AC_ZERO
        LD HL,AP_VALUE
        LD A,20
        CALL AN_RAW
        LD HL,1
        LD DE,1
        LD A,18
        JP AN_RAW
AC_PTR: DW 0
AC_WORD: DW 0
AC_LEFT: DB 0
AC_NPAR: DB 0
AC_DIGIT: DB 0
AC_FINAL: DB 0
AC_PARAMS: DB 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
        DB 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
AC_VALID: DB 0
AC_SAVED: DB 0,0,0,0,0,0,0,0,0
