; Transient per-file errors: retain earlier successes and clean this target.
BC_CFAIL:
        LD (CTE_MSG),DE
        LD HL,CT_FAILS
        INC (HL)
        CALL CTPAIR
        LD DE,(CTE_MSG)
        CALL BC_PRINT
        LD A,(BC_CMADE)
        OR A
        JR Z,CTE_DONE
        CALL BC_CSELD
        LD DE,BC_NEWFCB
        LD C,16
        CALL BDOS
        CALL CVVDEL
        RET C
CTE_DONE:
        LD HL,(CTE_MSG)
        LD DE,BC_NOSPACE
        OR A
        SBC HL,DE
        RET NZ
        LD A,1
        LD (BC_WERROR),A
        RET
CTE_MSG: DW 0
CTE_CLEAN: DB 13,10,'INCOMPLETE DESTINATION CLEANUP FAILED',13,10,'$'
