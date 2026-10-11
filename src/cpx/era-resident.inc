; Resident ERA: shared selection, basic erase, unconditional RO/SYS protection.
; Rescan in lexical order after each mutation; never retain a BDOS search cursor.
BC_ERA:
        CALL RE_VALIDATE
        JP C,BC_DBAD
        LD A,B
        OR A
        JP Z,BC_DNOFILE
        ; Validate the entire selected drive domain before the first deletion.
        CALL RE_DVALID
        JP C,BC_BDERR
        LD HL,FS_FCB+1
        LD B,11
RE_ALL:
        LD A,(HL)
        CP '?'
        JR NZ,RE_BEGIN
        INC HL
        DJNZ RE_ALL
        LD DE,BC_ECONF
        CALL BC_PRINT
        XOR A
        LD (BC_EBUFFER+1),A
        LD DE,BC_EBUFFER
        LD C,10
        CALL BDOS
        LD A,(BC_EBUFFER+1)
        CP 1
        JR NZ,RE_CANCEL
        LD A,(BC_EBUFFER+2)
        AND 05FH
        CP 'Y'
        JR NZ,RE_CANCEL
        JR RE_BEGIN
RE_CANCEL:
        JP BC_DURST
RE_BEGIN:
        XOR A
        LD (RF_ANY),A
        LD BC,0
        LD (RF_INDEX),BC
RE_DU:
        LD BC,(RF_INDEX)
        CALL DU_NEXT
        JP C,RE_END
        LD (RF_INDEX),BC
        LD A,D
        LD (RF_DRIVE),A
        LD A,E
        LD (RF_USER),A
        CALL RF_SELECT
        LD HL,RF_LAST
        LD B,11
        XOR A
RE_ZERO:
        LD (HL),A
        INC HL
        DJNZ RE_ZERO
RE_NEXT:
        CALL RF_FIND
        JR C,RE_DU
        LD A,1
        LD (RF_ANY),A
        LD HL,RF_BEST
        LD DE,RF_LAST
        LD BC,11
        LDIR
        CALL RF_FCB
        LD IX,RF_FILE
        LD HL,RF_LAST
        PUSH IX
        POP DE
        INC DE
        LD BC,11
        LDIR
        ; Inspect every physical extent, even ones excluded by the predicate.
        ; A protected extent protects the entire concrete file.
        LD A,'?'
        LD (IX+12),A
        PUSH IX
        POP DE
        LD C,17
        PUSH IX
        CALL BDOS
        POP IX
RE_CHECK:
        CP 0FFH
        JR Z,RE_DELETE
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,BC_DMA+9
        ADD HL,DE
        LD A,(HL)
        INC HL
        OR (HL)
        AND 80H
        JR NZ,RE_NEXT
        PUSH IX
        POP DE
        LD C,18
        PUSH IX
        CALL BDOS
        POP IX
        JR RE_CHECK
RE_DELETE:
        XOR A
        LD (IX+12),A
        PUSH IX
        POP DE
        LD C,19
        PUSH IX
        CALL BDOS
        POP IX
        CP 0FFH
        JR NZ,RE_NEXT
        LD DE,RE_FAILED
        CALL BC_PRINT
        JR RE_NEXT
RE_END:
        LD A,(RF_ANY)
        OR A
        JP Z,BC_DNOFILE
        JP BC_DURST
; Query and parse without changing caller DU. Preserve the input registers.
RE_VALIDATE:
        CALL RE_CAPTURE
        PUSH HL
        PUSH BC
        CALL FS_PARSE
        POP BC
        POP HL
        RET
RE_CAPTURE:
        PUSH HL
        PUSH BC
        LD C,25
        CALL BDOS
        LD (BC_DSAVE),A
        PUSH AF
        LD E,0FFH
        LD C,32
        CALL BDOS
        LD (BC_USAVE),A
        LD E,A
        POP AF
        LD D,A
        POP BC
        POP HL
        RET
RE_FAILED: DB 13,10,'Erase failed.',13,10,'$'

RE_DVALID:
        LD HL,DU_MAP+16
        LD B,48
RE_DOMAIN:
        LD A,(HL)
        OR A
        SCF
        RET NZ
        INC HL
        DJNZ RE_DOMAIN
        OR A
        RET
