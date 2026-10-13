; Resident TYPE: shared selection, sequential display and forward paging.
; RF_FIND provides the common unique-file order; rescan after BDOS file reads.
BC_TYPE:
        CALL RE_CAPTURE
        XOR A
        LD (BC_TPAGE),A
        LD (TF_LEN),A
TF_OPTION:
        CALL RF_TRIM
        LD A,B
        OR A
        JR Z,TF_PARSE
        LD DE,0
        PUSH HL
TF_TOKEN:
        LD A,(HL)
        CP ' '
        JR Z,TF_TEND
        INC HL
        INC E
        DJNZ TF_TOKEN
TF_TEND:
        POP IX
        PUSH HL
        PUSH BC
        LD A,(IX+0)
        CP '/'
        JR NZ,TF_OPERAND
        LD A,E
        CP 2
        JR NZ,TF_BADPOP
        LD A,(IX+1)
        CP 'P'
        JR NZ,TF_BADPOP
        LD A,1
        LD (BC_TPAGE),A
        JR TF_CONTINUE
TF_OPERAND:
        LD A,(TF_LEN)
        OR A
        JR NZ,TF_BADPOP
        LD A,E
        LD (TF_LEN),A
        LD (TF_SRC),IX
TF_CONTINUE:
        POP BC
        POP HL
        JR TF_OPTION
TF_BADPOP:
        POP BC
        POP HL
TF_BAD:
        JP BC_DBAD
TF_PARSE:
        LD A,(TF_LEN)
        OR A
        JR Z,TF_BAD
        LD B,A
        LD HL,(TF_SRC)
        LD A,(BC_DSAVE)
        LD D,A
        LD A,(BC_USAVE)
        LD E,A
        CALL FS_PARSE
        JR C,TF_BAD
        CALL RE_DVALID
        JP C,BC_BDERR
        XOR A
        LD (TF_ANY),A
        LD (BC_TLCNT),A
        LD BC,0
        LD (RF_INDEX),BC
TF_DU:
        LD BC,(RF_INDEX)
        CALL DU_NEXT
        JP C,TF_END
        LD (RF_INDEX),BC
        LD A,D
        LD (RF_DRIVE),A
        LD A,E
        LD (RF_USER),A
        CALL RF_SELECT
        LD HL,RF_LAST
        LD B,11
        XOR A
TF_ZERO:
        LD (HL),A
        INC HL
        DJNZ TF_ZERO
TF_NEXT:
        CALL RF_FIND
        JR C,TF_DU
        LD HL,RF_BEST
        LD DE,RF_LAST
        LD BC,11
        LDIR
        CALL RF_FCB
        LD HL,RF_BEST
        LD DE,RF_FILE+1
        LD BC,11
        LDIR
        LD DE,RF_FILE
        LD C,15
        CALL BDOS
        INC A
        JR Z,TF_OPENERR
        LD A,(TF_ANY)
        OR A
        JR Z,TF_FIRST
        LD DE,TF_SEPARATOR
        CALL BC_PRINT
TF_FIRST:
        LD A,1
        LD (TF_ANY),A
TF_READ:
        LD DE,BC_DMA
        LD C,26
        CALL BDOS
        LD DE,RF_FILE
        LD C,20
        CALL BDOS
        OR A
        JR Z,TF_BLOCK
        CP 1
        JR Z,TF_CLOSE
        LD DE,BC_READERR
        CALL BC_PRINT
        JR TF_CLOSE
TF_BLOCK:
        LD HL,BC_DMA
        LD B,128
TF_CHAR:
        LD A,(HL)
        CP 1AH
        JR Z,TF_CLOSE
        PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL BDOS
        POP BC
        POP HL
        LD A,(HL)
        CP 10
        JR NZ,TF_ADVANCE
        PUSH HL
        CALL TF_LINE
        POP HL
        JR C,TF_CANCEL
TF_ADVANCE:
        INC HL
        DJNZ TF_CHAR
        JR TF_READ
TF_CLOSE:
        LD DE,RF_FILE
        LD C,16
        CALL BDOS
TF_RESUME:
        JP TF_NEXT
TF_OPENERR:
        LD DE,TF_CANNOT
        CALL BC_PRINT
        JR TF_RESUME
TF_CANCEL:
        LD DE,RF_FILE
        LD C,16
        CALL BDOS
        JP BC_DURST
TF_END:
        LD A,(TF_ANY)
        OR A
        JP Z,BC_DNOFILE
        JP BC_DURST
TF_LINE:
        LD A,(BC_TPAGE)
        OR A
        RET Z
        PUSH BC
        PUSH DE
        LD HL,BC_TLCNT
        INC (HL)
        LD A,(HL)
        CP 23
        JR C,TF_LNORMAL
        LD (HL),0
        LD DE,BC_MORE
        CALL BC_PRINT
TF_WAIT:
        LD E,0FFH
        LD C,6
        CALL BDOS
        CP 3
        JR Z,TF_LABORT
        CP ' '
        JR Z,TF_LERASE
        CP '.'
        JR NZ,TF_WAIT
TF_LERASE:
        LD DE,BC_MERASE
        CALL BC_PRINT
TF_LNORMAL:
        OR A
TF_LRETURN:
        POP DE
        POP BC
        RET
TF_LABORT:
        LD DE,BC_MERASE
        CALL BC_PRINT
        SCF
        JR TF_LRETURN
TF_SRC: DW 0
TF_LEN: DB 0
TF_ANY: DB 0
TF_SEPARATOR: DB 13,10,'--------------------',13,10,'$'
TF_CANNOT: DB 13,10,'Cannot open.',13,10,'$'
