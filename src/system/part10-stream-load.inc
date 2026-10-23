; Part 10 experimental header-retaining, single-pass command loader.
; Only prospective/unpublished payload memory may be changed before admission.
; Fixed header cache + record buffer; all state is inside the verified stage.
STAGE EQU 01000H
CR10BUFFER EQU 01600H
CR10FLOOR EQU 01680H

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
        LD HL,(CRBOUND)
        LD DE,(CRMALLOC)
        OR A
        SBC HL,DE
        JP C,CRBAD
        LD (CRBASE),HL
        LD DE,CR10FLOOR
        OR A
        SBC HL,DE
        JP C,CRBAD                ; header/buffer must finish below destination
        LD HL,(CRMHEADSZ)
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
        JR Z,CR9RELCHECK
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
CR9RELCHECK:
        LD HL,0
        LD (CR9PREV),HL
        CALL CR9TABLE
CR9RELP:
        LD A,B
        OR C
        JR Z,CR10STREAM
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
; The complete header is retained and its relocation table prevalidated.
; All payload writes below are to unlinked memory. A failed load leaves
; CRBOUND unchanged; its caller can reuse the same destination immediately.
CR10STREAM:
        LD BC,(CRMHEADSZ)
        LD DE,STAGE
        CALL LY_CCRC
        LD (CR10CRC),HL
        XOR A
        LD (CR10AVAIL),A
        LD HL,(CRBASE)
        LD BC,(CRMSIZE)
        LD DE,0
CR10PAY:
        CALL CR10BYTE
        JP C,CRBAD
        LD (HL),A
        INC HL
        ADD A,E
        LD E,A
        JR NC,CR10NC
        INC D
CR10NC:
        DEC BC
        LD A,B
        OR C
        JR NZ,CR10PAY
        LD A,(CRFILE)
        OR A
        JR Z,CR10META
        PUSH HL
        LD HL,(STAGE+44)
        OR A
        SBC HL,DE
        POP HL
        JP NZ,CRBAD
CR10META:
        LD BC,(CR9EXTRA)
C10METLP:
        LD A,B
        OR C
        JR Z,C10BINDG
        CALL CR10BYTE
        JP C,CRBAD
        DEC BC
        JR C10METLP
C10BINDG:
        LD HL,CR10BIND
        LD B,20
C10BINDL:
        CALL CR10BYTE
        JP C,CRBAD
        LD (HL),A
        INC HL
        DJNZ C10BINDL
        CALL CR10GET
        JP C,CRBAD
        LD E,A
        CALL CR10GET
        JP C,CRBAD
        LD D,A
        LD HL,(CR10CRC)
        OR A
        SBC HL,DE
        JP NZ,CRBAD
        LD HL,CR10BIND
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
        JP CR9COPY

; Return one byte with carry clear; preserve BC, DE and HL.
; Read exactly one physical record when the buffer is exhausted.
CR10GET:
        PUSH BC
        PUSH DE
        PUSH HL
        LD A,(CR10AVAIL)
        OR A
        JR NZ,CR10HAVE
        LD HL,CR10BUFFER
        CALL CRNEXT128
        JR NZ,CR10IOBAD
        LD HL,CR10BUFFER
        LD (CR10PTR),HL
        LD A,128
CR10HAVE:
        DEC A
        LD (CR10AVAIL),A
        LD HL,(CR10PTR)
        LD A,(HL)
        INC HL
        LD (CR10PTR),HL
        POP HL
        POP DE
        POP BC
        OR A
        RET
CR10IOBAD:
        POP HL
        POP DE
        POP BC
        SCF
        RET

; Consume one semantic byte and update CRC-16/CCITT-FALSE incrementally.
; The final CRC word uses CR10GET; CP/M record padding is ignored.
CR10BYTE:
        CALL CR10GET
        RET C
        PUSH AF
        PUSH BC
        PUSH HL
        LD HL,(CR10CRC)
        XOR H
        LD H,A
        LD B,8
CR10BIT:
        ADD HL,HL
        JR NC,CR10BITNEXT
        LD A,H
        XOR 010H
        LD H,A
        LD A,L
        XOR 021H
        LD L,A
CR10BITNEXT:
        DJNZ CR10BIT
        LD (CR10CRC),HL
        POP HL
        POP BC
        POP AF
        RET

CR9COPY:
        LD HL,(CRBASE)
        LD (CRBOUND),HL           ; publish only after all admission checks
        LD DE,(CRMLINK)
        OR A
        SBC HL,DE
        LD (CRDELTA),HL
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

CR10CRC: DW 0
CR10PTR: DW 0
CR10AVAIL: DB 0
CR10BIND: DS 20
