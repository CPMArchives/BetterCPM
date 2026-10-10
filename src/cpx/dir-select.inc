; Resident DIR setup and iteration; installed only in the RCP build.
BC_DIR:
        LD (BC_DARGP),HL
        LD A,B
        LD (BC_DARGL),A
        LD C,25
        CALL BDOS
        LD (BC_DSAVE),A
        LD E,0FFH
        LD C,32
        CALL BDOS
        LD (BC_USAVE),A
        LD E,A
        LD A,(BC_DSAVE)
        LD D,A
        LD HL,(BC_DARGP)
        LD A,(BC_DARGL)
        LD B,A
        CALL FS_PARSE
        JP C,BC_DBAD
        ; Both supported platform bindings currently expose A: through D:.
        ; Reject the entire selection before changing the caller DU.
        LD HL,DU_MAP+16
        LD B,48
RD_DOMAIN:
        LD A,(HL)
        OR A
        JP NZ,BC_BDERR
        INC HL
        DJNZ RD_DOMAIN
        LD BC,0
        LD (RD_INDEX),BC
RD_NEXT:
        LD BC,(RD_INDEX)
        CALL DU_NEXT
        JP C,BC_DURST
        LD (RD_INDEX),BC
        LD A,E
        LD (RD_USER),A
        LD E,D
        LD C,14
        CALL BDOS
        LD A,(RD_USER)
        LD E,A
        LD C,32
        CALL BDOS
        LD C,31
        CALL BDOS
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        CPL
        LD (BC_EXMASK),A
        XOR A
        LD (BC_DCOL),A
        LD (BC_DFOUND),A
        LD HL,FS_FCB
        LD DE,BC_FCB
        LD BC,36
        LDIR
        JP RD_SEARCH

; Predicate over directory T1/T2/T3 attribute bits, before the usual SYS hiding.
RD_FILTER:
        LD HL,(BC_DIREP)
        LD DE,9
        ADD HL,DE
        LD C,0
        LD B,3
        LD E,1
RD_BITS:
        LD A,(HL)
        AND 80H
        JR Z,RD_BITNEXT
        LD A,C
        OR E
        LD C,A
RD_BITNEXT:
        INC HL
        SLA E
        DJNZ RD_BITS
        LD A,(FS_MASK)
        LD B,C
        INC B
RD_SHIFT:
        RRCA
        DJNZ RD_SHIFT
        RET                         ; carry = predicate matched

RD_PRINTUSER:
        LD A,(RD_USER)
        LD B,0
RD_TENS:
        CP 10
        JR C,RD_DIGITS
        SUB 10
        INC B
        JR RD_TENS
RD_DIGITS:
        PUSH AF
        LD A,B
        OR A
        JR Z,RD_ONES
        ADD A,'0'
        CALL BC_PCHAR
RD_ONES:
        POP AF
        ADD A,'0'
        JP BC_PCHAR
RD_INDEX: DW 0
RD_USER: DB 0
