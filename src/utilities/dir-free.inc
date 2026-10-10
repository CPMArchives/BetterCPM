; Once-per-selected-drive footer, independent of selected users and size unit.
DX_FINISH:
        XOR A
        LD (DX_DRIVE),A
DX_LOOP:
        LD A,(DX_DRIVE)
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,DU_MAP
        ADD HL,DE
        LD A,(HL)
        INC HL
        OR (HL)
        INC HL
        OR (HL)
        INC HL
        OR (HL)
        JR Z,DX_NEXT
        LD A,(DX_DRIVE)
        LD E,A
        LD C,14
        CALL BDOS
        LD C,31
        CALL BDOS
        PUSH HL
        LD C,27
        CALL BDOS
        EX DE,HL
        POP HL
        CALL DF_COUNT
        LD A,(DX_DRIVE)
        ADD A,'A'
        CALL BC_PCHAR
        LD DE,DX_COLON
        CALL BC_PRINT
        LD HL,DF_VALUE
        LD DE,DTD_NUM
        LD BC,4
        LDIR
        CALL DTD_DEC
        LD DE,DX_MESSAGE
        CALL BC_PRINT
DX_NEXT:
        LD HL,DX_DRIVE
        INC (HL)
        LD A,(HL)
        CP 16
        JR NZ,DX_LOOP
        JP BC_DURST
DX_DRIVE: DB 0
DX_COLON: DB ': $'
DX_MESSAGE: DB 'K FREE',13,10,'$'
