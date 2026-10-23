; Part 9 experimental single-read command carrier load.
; STAGE is transient storage below the prospective module destination.
STAGE EQU 01000H

CRLOAD:
        LD HL,STAGE
        CALL CRNEXT128
        RET NZ
        LD HL,STAGE
        LD DE,(CRMAGPTR)
        LD B,6
CR9MAG:
        LD A,(DE)
        CP (HL)
        JP NZ,CRBAD
        INC DE
        INC HL
        DJNZ CR9MAG
        LD A,(CRFILE)
        OR A
        JR Z,CR9CCP
        LD HL,(STAGE+6)
        DEC HL
        LD A,H
        OR L
        JP NZ,CRBAD
        LD HL,(STAGE+8)
        LD A,H
        OR L
        JP NZ,CRBAD
        LD HL,STAGE+10
        LD DE,CRMLINK
        LD BC,20
        LDIR
        LD HL,(STAGE+30)
        LD (CR9META),HL
        LD A,(STAGE+42)
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD (CR9EXTRA),HL
        LD HL,(CRMRELTABLE)
        LD DE,48
        OR A
        SBC HL,DE
        JP NZ,CRBAD
        JR CR9NORMAL
CR9CCP:
        LD HL,STAGE+6
        LD DE,CRMLINK
        LD BC,8
        LDIR
        LD HL,(STAGE+14)
        LD (CRMRELOCS),HL
        LD HL,1024
        LD (CRMHEADSZ),HL
        LD (CRMPAYLOAD),HL
        LD HL,16
        LD (CRMRELTABLE),HL
        LD HL,0
        LD (CR9EXTRA),HL
        LD HL,(CRMENTRY)
        LD A,H
        OR L
        JP NZ,CRBAD                ; current CCP handoff enters its base
CR9NORMAL:
        LD HL,(CRMSIZE)
        LD A,H
        OR L
        JP Z,CRBAD
        LD DE,(CRMALLOC)
        OR A
        SBC HL,DE
        JR C,CR9ALLOC
        JP NZ,CRBAD
CR9ALLOC:
        LD HL,(CRMALLOC)
        LD A,L
        OR A
        JP NZ,CRBAD
        LD A,H
        OR A
        JP Z,CRBAD
        LD HL,(CRMHEADSZ)
        LD A,L
        OR A
        JP NZ,CRBAD
        LD A,H
        AND 1
        JP NZ,CRBAD
        LD A,H
        OR A
        JP Z,CRBAD
        CP 7
        JP NC,CRBAD
        LD DE,(CRMPAYLOAD)
        OR A
        SBC HL,DE
        JP NZ,CRBAD
        LD HL,(CRMRELOCS)
        ADD HL,HL
        JP C,CRBAD
        LD DE,(CRMRELTABLE)
        ADD HL,DE
        JP C,CRBAD
        EX DE,HL
        LD HL,(CRMHEADSZ)
        OR A
        SBC HL,DE
        JP C,CRBAD
        LD HL,(CRMHEADSZ)
        LD DE,(CRMSIZE)
        ADD HL,DE
        JP C,CRBAD
        LD (CR9BODYEND),HL
        LD A,(CRFILE)
        OR A
        JR Z,CR9SIZE
        LD DE,(CR9META)
        OR A
        SBC HL,DE
        JP NZ,CRBAD
        LD HL,(CRMSIZE)
        LD DE,8
        OR A
        SBC HL,DE
        JP C,CRBAD                ; live CPX descriptor occupies eight bytes
        LD DE,(CRMENTRY)
        CALL CR9OFFSET
        JP NZ,CRBAD
        LD DE,(CRMINIT)
        CALL CR9LIFE
        JP NZ,CRBAD
        LD DE,(CRMSHUT)
        CALL CR9LIFE
        JP NZ,CRBAD
CR9SIZE:
        LD HL,(CR9BODYEND)
        LD DE,(CR9EXTRA)
        ADD HL,DE
        JP C,CRBAD
        LD (CR9BIND),HL
        LD DE,22
        ADD HL,DE
        JP C,CRBAD
        LD (CR9LENGTH),HL
        LD DE,127
        ADD HL,DE
        JP C,CRBAD
        LD A,L
        AND 080H
        LD L,A
        LD (CR9ROUND),HL
        LD DE,STAGE
        ADD HL,DE
        JP C,CRBAD
        PUSH HL
        LD HL,(CRBOUND)
        LD DE,(CRMALLOC)
        OR A
        SBC HL,DE
        POP DE
        JP C,CRBAD
        LD (CRBASE),HL
        OR A
        SBC HL,DE
        JP C,CRBAD                ; staging must finish below destination
        LD HL,(CR9ROUND)
        LD DE,128
        OR A
        SBC HL,DE
        LD (CRLEFT),HL
        LD HL,STAGE+128
CR9READ:
        PUSH HL
        LD HL,(CRLEFT)
        LD A,H
        OR L
        POP HL
        JR Z,CR9CHECK
        CALL CRNEXT128
        RET NZ
        PUSH HL
        LD HL,(CRLEFT)
        LD DE,128
        OR A
        SBC HL,DE
        LD (CRLEFT),HL
        POP HL
        JR CR9READ
CR9CHECK:
        LD HL,(CR9LENGTH)
        DEC HL
        DEC HL
        LD B,H
        LD C,L
        LD DE,STAGE
        CALL LY_CCRC
        PUSH HL
        LD HL,(CR9LENGTH)
        LD DE,STAGE-2
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        POP HL
        OR A
        SBC HL,DE
        JP NZ,CRBAD
        LD HL,(CR9BIND)
        LD DE,STAGE
        ADD HL,DE
        LD A,(HL)
        CP 'B'
        JP NZ,CRBAD
        INC HL
        LD A,(HL)
        CP 'P'
        JP NZ,CRBAD
        INC HL
        LD A,(HL)
        CP 2
        JP NZ,CRBAD
        INC HL
        LD A,(CRFILE)
        OR A
        JR NZ,CR9CLASS
        LD A,(HL)
        CP 1
        JP NZ,CRBAD
CR9CLASS:
        LD A,(HL)
        INC HL
        OR A
        JR Z,CR9PUBLIC
        DEC A
        JP NZ,CRBAD
        LD DE,LY_CID
        CALL LY_CCMP
        JP NZ,CRBAD
        JR CR9SUM
CR9PUBLIC:
        LD B,16
CR9ZERO:
        OR (HL)
        INC HL
        DJNZ CR9ZERO
        JP NZ,CRBAD
CR9SUM:
        LD A,(CRFILE)
        OR A
        JR Z,CR9RELCHECK
        LD HL,(CRMPAYLOAD)
        LD DE,STAGE
        ADD HL,DE
        LD BC,(CRMSIZE)
        LD DE,0
CR9SUMLP:
        LD A,(HL)
        ADD A,E
        LD E,A
        JR NC,CR9NC
        INC D
CR9NC:
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,CR9SUMLP
        LD HL,(STAGE+44)
        OR A
        SBC HL,DE
        JP NZ,CRBAD
CR9RELCHECK:
        LD HL,0
        LD (CR9PREV),HL
        CALL CR9TABLE
CR9RELP:
        LD A,B
        OR C
        JR Z,CR9COPY
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        PUSH HL
        PUSH BC
        LD HL,(CRMSIZE)
        DEC HL
        OR A
        SBC HL,DE
        JP C,CRRLBAD
        JP Z,CRRLBAD
        EX DE,HL
        PUSH HL
        LD DE,(CR9PREV)
        OR A
        SBC HL,DE
        POP HL
        JP C,CRRLBAD
        INC HL
        INC HL
        LD (CR9PREV),HL
        POP BC
        POP HL
        DEC BC
        JR CR9RELP
CR9COPY:
        LD HL,(CRBASE)
        LD (CRBOUND),HL
        LD DE,(CRMLINK)
        OR A
        SBC HL,DE
        LD (CRDELTA),HL
        LD HL,(CRMPAYLOAD)
        LD DE,STAGE
        ADD HL,DE
        LD DE,(CRBASE)
        LD BC,(CRMSIZE)
        LDIR
        CALL CR9TABLE
CR9APPLY:
        LD A,B
        OR C
        JP Z,CRENTRY
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        PUSH HL
        PUSH BC
        LD HL,(CRBASE)
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD BC,(CRDELTA)
        ADD HL,BC
        EX DE,HL
        LD (HL),D
        DEC HL
        LD (HL),E
        POP BC
        POP HL
        DEC BC
        JR CR9APPLY
CR9TABLE:
        LD HL,(CRMRELTABLE)
        LD DE,STAGE
        ADD HL,DE
        LD BC,(CRMRELOCS)
        RET
CR9LIFE:
        LD A,D
        AND E
        INC A
        RET Z
CR9OFFSET:
        LD HL,(CRMSIZE)
        OR A
        SBC HL,DE
        JP C,CRBAD
        JP Z,CRBAD
        XOR A
        RET
CRRLBAD:
        POP BC
        POP HL
CRBAD:
        LD A,1
        OR A
        RET

; One actual 128-byte record is required. Never accept a short FL_NEXT block.
CRNEXT128:
        LD A,(CRFILE)
        OR A
        JR Z,CR9RAW
        PUSH HL
        LD B,H
        LD C,L
        LD DE,LY_FCB
        CALL LY_EXT+9
        POP HL
        OR A
        RET NZ
        LD DE,128
        ADD HL,DE
        XOR A
        RET
CR9RAW:
        LD A,(CRSLOT)
        CP 160
        JP NC,CRBAD
        INC A
        LD (CRSLOT),A
        DEC A
        LD E,A
        LD D,0
        LD B,1
        JP LY_DISK+15

CR9META: DW 0
CR9EXTRA: DW 0
CR9BODYEND: DW 0
CR9BIND: DW 0
CR9LENGTH: DW 0
CR9ROUND: DW 0
CR9PREV: DW 0
