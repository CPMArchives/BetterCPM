; Host ANSI uses validated, complete SGR packets. Pending sequences stay private.
D_PRINT:
        LD A,C
        OUT (1),A
        RET
D_HOME:
        LD HL,0
        JR D_SET
D_CR:
        CALL D_GET
        LD H,0
D_SET:
        LD (H_RC),HL
        XOR A
        LD (A_WRAP),A
H_POSITION:
        LD HL,(H_RC)
        LD A,'H'
H_PAIR:
        PUSH AF
        PUSH HL
        LD HL,H_CSI
        CALL H_STR
        POP HL
        LD A,L
        INC A
        CALL H_DEC
        LD A,';'
        OUT (1),A
        LD A,H
        INC A
        CALL H_DEC
        POP AF
        OUT (1),A
        XOR A
        RET
H_DEC:
        LD B,'0'
H_TENS:
        CP 10
        JR C,H_UNIT
        SUB 10
        INC B
        JR H_TENS
H_UNIT:
        LD C,A
        LD A,B
        CP '0'
        JR Z,H_LAST
        OUT (1),A
H_LAST:
        LD A,C
        ADD A,'0'
        OUT (1),A
        RET
D_OFF:
        XOR A
        JR D_REVERSE
D_ON:
        LD A,128
D_REVERSE:
        LD (D_REV),A
        LD HL,H_NORMAL
        OR A
        JR Z,H_STR
        LD HL,H_REVERSE
        JR H_STR
D_EOL:
        LD B,1
        JR H_ERASE
D_EOS:
        LD A,(H_RC)
        LD B,A
        LD A,24
        SUB B
        LD B,A
H_ERASE:
        LD A,(H_RC+1)
        LD C,A
        LD A,80
        SUB C
        LD C,A
        LD A,32
H_ERLOOP:
        OUT (1),A
        DEC C
        JR NZ,H_ERLOOP
        DEC B
        JP Z,H_POSITION
        LD HL,H_NEXT
        CALL H_STR
        LD C,80
        LD A,32
        JR H_ERLOOP
D_BELL:
        LD A,7
        OUT (1),A
        RET
D_RSCROL:
        LD C,'M'
        JR H_SCROLL
D_SCROLL:
        LD C,'D'
H_SCROLL:
        PUSH BC
        LD A,(A_TOP)
        LD L,A
        LD A,(A_BOTTOM)
        LD H,A
        LD A,'r'
        CALL H_PAIR
        CALL H_POSITION
        POP BC
        LD A,27
        OUT (1),A
        LD A,C
        OUT (1),A
        LD HL,H_ALL
        CALL H_STR
        JP H_POSITION
H_SAVEREST:
        LD A,27
        OUT (1),A
        LD A,C
        OUT (1),A
        CP '8'
        LD C,'7'
        JR Z,H_SAVEREST
        XOR A
        RET
D_VISSET:
        LD A,(D_VIS)
        LD HL,H_HIDE
        OR A
        JP Z,H_STR
        LD HL,H_SHOW
H_STR:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        OUT (1),A
        JR H_STR
D_GET:
        LD HL,(H_RC)
        RET
H_CSI: DB 27,'[',0
H_NEXT: DB 27,'[E',0
H_NORMAL: DB 27,'[0m',0
H_REVERSE: DB 27,'[0;7m',0
H_ALL: DB 27,'[r',0
H_HIDE: DB 27,'[?25l',0
H_SHOW: DB 27,'[?25h',0
H_RC: DW 0
