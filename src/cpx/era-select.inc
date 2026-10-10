; Resident ERA lexical gate. Shared parsing must finish before selection/delete.
; Compound scopes and predicates need a separate destructive-operation contract.
RE_VALIDATE:
        PUSH HL
        PUSH BC
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
        JR C,RE_RETURN
        ; Do not let the legacy operation silently ignore accepted extensions.
        LD HL,(BC_DARGP)
        LD A,(BC_DARGL)
        LD B,A
        OR A
        JR Z,RE_RETURN
RE_SUBSET:
        LD A,(HL)
        CP '['
        JR Z,RE_EXTENDED
        INC HL
        DJNZ RE_SUBSET
        OR A
RE_RETURN:
        POP BC
        POP HL
        RET
RE_EXTENDED:
        LD DE,RE_MESSAGE
        CALL BC_PRINT
        SCF
        POP BC
        POP HL
        RET
RE_MESSAGE: DB 13,10,'Selection not supported by resident ERA.',13,10,'$'
