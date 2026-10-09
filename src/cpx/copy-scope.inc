; Transient COPY source scope. All DU selection is frozen before destination I/O.
CTSCOPE:
        LD A,0FFH
        LD (CT_FILTER),A
        LD (BC_COFCP),DE
        LD A,(BC_CDSAV)
        LD D,A
        LD A,(BC_CUSAV)
        LD E,A
        CALL DU_PARSE
        JR C,CTS_BAD
        CALL OQ_SPLIT
        JR C,CTS_BAD
        LD (BC_COPTR),HL
        LD A,B
        LD (BC_COLEN),A
        OR A
        JR Z,CTS_BAD
        LD A,(OQ_LEN)
        OR A
        JR Z,CTSFILES
        LD B,A
        LD HL,(OQ_PTR)
        CALL AT_PARSE
        JR C,CTS_BAD
        LD (CT_FILTER),A
CTSFILES:
        LD HL,(BC_COPTR)
        LD A,(BC_COLEN)
        LD B,A
        CALL BC_CVALID
        JR C,CTS_BAD
        LD HL,(BC_COPTR)
        LD A,(BC_COLEN)
        LD B,A
        LD DE,BC_FCB
        CALL BC_PFCB
        LD A,(BC_CDSAV)
        LD (BC_CODRV),A
        LD A,(BC_CUSAV)
        LD (BC_COUSE),A
        SCF
        RET
CTS_BAD:
        XOR A
        RET

; Iterate source locations; failure aborts the whole preflight, never writes.
CTDUNEXT:
        LD BC,(CTDUIDX)
        CALL DU_NEXT
        JR C,CTDUEND
        LD (CTDUIDX),BC
        LD A,D
        LD (BC_CSDRV),A
        LD A,E
        LD (BC_CSUSR),A
        LD E,D
        LD C,14
        CALL BDOS
        CP 0FFH
        JR Z,CTDUBAD
        JP BC_WRESET
CTDUEND:
        LD A,(CT_COUNT)
        OR A
        JP NZ,CTPREF
        LD DE,BC_NOFILE
        CALL BC_PRINT
        JP BC_WEND
CTDUBAD:
        LD DE,CTDUMSG
        CALL BC_PRINT
        JP BC_WEND

; Does this generated target overlap any selected source in its actual DU?
CTSRCTST:
        LD HL,CT_DUS
        LD (CTDUSCAN),HL
        LD HL,CT_NAMES
        LD (CTCKPTR),HL
        LD A,(CT_COUNT)
        LD (CTSCAN),A
CTSRCLP:
        LD HL,(CTDUSCAN)
        LD A,(BC_CDDRV)
        CP (HL)
        JR NZ,CTSRCADV
        INC HL
        LD A,(BC_CDUSR)
        CP (HL)
        JR NZ,CTSRCADV
        LD HL,(CTCKPTR)
        LD DE,(CT_DCUR)
        CALL BC_WCMP
        RET Z
CTSRCADV:
        LD HL,(CTDUSCAN)
        INC HL
        INC HL
        LD (CTDUSCAN),HL
        LD HL,(CTCKPTR)
        LD DE,11
        ADD HL,DE
        LD (CTCKPTR),HL
        LD HL,CTSCAN
        DEC (HL)
        JR NZ,CTSRCLP
        LD A,1
        OR A
        RET

DU_MAP: DS 64
DU_WORK: DS 12
CTDUIDX: DW 0
CT_DUS: DS 64*2
CTDUENDP: DW 0
CTDUCUR: DW 0
CTDUSCAN: DW 0
CTDUMSG: DB 13,10,'COPY SOURCE DRIVE UNAVAILABLE',13,10,'$'

; Evaluate the predicate against directory metadata before masking name bits.
; Input HL points at the directory name; preserve it for filename collection.
CTMATCH:
        PUSH HL
        PUSH BC
        LD DE,8
        ADD HL,DE
        LD C,0
        LD A,(HL)
        AND 80H
        JR Z,CTMSYS
        INC C
CTMSYS:
        INC HL
        LD A,(HL)
        AND 80H
        JR Z,CTMARC
        LD A,C
        OR 2
        LD C,A
CTMARC:
        INC HL
        LD A,(HL)
        AND 80H
        JR Z,CTMTEST
        LD A,C
        OR 4
        LD C,A
CTMTEST:
        LD A,C
        OR A
        LD A,(CT_FILTER)
        JR Z,CTMRESULT
        LD B,C
CTMSHIFT:
        SRL A
        DJNZ CTMSHIFT
CTMRESULT:
        AND 1
        POP BC
        POP HL
        RET
CT_FILTER: DB 0FFH
