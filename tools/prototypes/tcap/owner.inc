; Private XTCP 0.1 feasibility slice, NOT the proposed public request ABI.
; A=2 begin,3 takeover,4 end,7 describe. DE points to a 16-byte token.
; Recovery is internal and completed only by the safe-stack coordinator.
TX_ENTRY:
        PUSH DE
        LD (TX_PTR),DE
        CALL TX_DISP
        PUSH AF
        LD HL,0
        LD (TX_PTR),HL
        POP AF
        POP DE
        RET
TX_DISP:
        CP 2
        JP Z,TX_BEGIN
        CP 3
        JP Z,TX_TAKE
        CP 4
        JP Z,TX_END
        CP 7
        JR Z,TX_DESC
        LD A,4
        RET
TX_DESC:
        LD A,(TX_STATE)
        RET
TX_TAKE:
        LD A,(AN_STATE)
        OR A
        JP NZ,TX_PARSER
        LD A,(TX_STATE)
        OR A
        JP NZ,TX_BUSY
        CALL TZ_INPUT
        RET NZ
        LD HL,TX_SESS
        CALL TX_INC
        RET NZ
        LD HL,0
        LD (TX_SCOPE),HL
        LD (TX_SCOPE+2),HL
        LD A,1
        LD (TX_KIND),A
        LD A,2
        LD (TX_STATE),A
        JP TX_WRITE
TX_BEGIN:
        LD A,(AN_STATE)
        OR A
        JP NZ,TX_PARSER
        LD A,(TX_STATE)
        CP 5
        JP Z,TX_REQ
        CP 1
        JP Z,TX_BAD
        CP 3
        JP Z,TX_BAD
        CP 2
        JR Z,TB_TAKE
        OR A
        JP NZ,TX_BUSY
        CALL TZ_INPUT
        RET NZ
        JR TB_MAP
TB_TAKE:
        CALL TX_MATCH
        RET NZ
TB_MAP:
        LD A,(TX_MAP)
        OR A
        JR NZ,TB_ALLOC
        LD A,1
        RET
TB_ALLOC:
        ; Check scope exhaustion before consuming a session identity.
        LD HL,TX_SSEQ
        CALL TX_NMAX
        RET NZ
        LD A,(TX_STATE)
        CP 2
        JR Z,TB_SCOPE
        LD HL,TX_SESS
        CALL TX_INC
        RET NZ
TB_SCOPE:
        LD HL,TX_SSEQ
        CALL TX_INC
        RET NZ
        LD HL,TX_SSEQ
        LD DE,TX_SCOPE
        LD BC,4
        LDIR
        LD A,2
        LD (TX_KIND),A
        LD A,(TX_STATE)
        INC A
        LD (TX_STATE),A             ; arm ownership BEFORE backend mutation
        LD HL,AP_VALUE
        LD DE,TX_CAP
        LD BC,9
        LDIR
        LD HL,AP_VALUE
        LD DE,TX_WORK
        LD BC,9
        LDIR
        LD A,(TX_MAP)
        LD HL,TX_WORK
        OR (HL)
        LD (HL),A
        LD A,20
        CALL AN_RAW
        OR A
        JR NZ,TB_FAIL
        LD HL,TX_WORK
        LD DE,AP_VALUE
        LD BC,9
        LDIR
        JP TX_WRITE
TB_FAIL:
        CALL TX_WRITE
        LD A,5
        LD (TX_STATE),A
TX_REQ:
        LD A,18
        RET
TX_END:
        LD A,(TX_STATE)
        CP 5
        JP Z,TX_REQ
        CP 1
        JR Z,TE_MATCH
        CP 3
        JP NZ,TX_BAD
TE_MATCH:
        CALL TX_MATCH
        RET NZ
        LD A,(AN_STATE)
        OR A
        JP NZ,TX_PARSER
        LD HL,TX_CAP
        LD A,20
        CALL AN_RAW
        OR A
        JR NZ,TE_FAIL
        LD HL,TX_CAP
        LD DE,AP_VALUE
        LD BC,9
        LDIR
        LD A,(TX_STATE)
        DEC A
        LD (TX_STATE),A             ; 1 -> Idle; 3 -> Takeover
        XOR A
        LD HL,TX_SCOPE
        LD B,4
TE_ZERO:
        LD (HL),A
        INC HL
        DJNZ TE_ZERO
        LD A,1
        LD (TX_KIND),A
        XOR A
        RET
TE_FAIL:
        LD A,5
        LD (TX_STATE),A
        LD A,18
        RET
TX_MATCH:
        LD HL,(TX_PTR)
        LD DE,TX_TOKEN
        LD B,16
TM_LOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,TX_INVALID
        INC DE
        INC HL
        DJNZ TM_LOOP
        XOR A
        RET
TZ_INPUT:
        LD HL,(TX_PTR)
        LD B,16
        XOR A
TZ_LOOP:
        OR (HL)
        INC HL
        DJNZ TZ_LOOP
        JR NZ,TX_INVALID
        RET
TX_INVALID:
        LD A,13
        OR A
        RET
TX_WRITE:
        LD HL,TX_TOKEN
        LD DE,(TX_PTR)
        LD BC,16
        LDIR
        XOR A
        RET
TX_NMAX:
        PUSH HL
        LD B,4
        LD A,255
TN_LOOP:
        AND (HL)
        INC HL
        DJNZ TN_LOOP
        POP HL
        CP 255
        JR Z,TX_EXH
        XOR A
        RET
TX_INC:
        CALL TX_NMAX
        RET NZ
        LD B,4
TI_LOOP:
        INC (HL)
        JR NZ,TI_DONE
        INC HL
        DJNZ TI_LOOP
TI_DONE:
        XOR A
        RET
TX_EXH:
        LD A,20
        OR A
        RET
TX_BUSY:
        LD A,16
        OR A
        RET
TX_PARSER:
        LD A,11
        OR A
        RET
TX_BAD:
        LD A,12
        OR A
        RET
; Internal rendering phase. Leaves RecoveryRequired until coordinator finishes.
TX_FIX:
        LD A,(TX_STATE)
        OR A
        JR NZ,TF_GO
        LD A,2
        RET
TF_GO:
        LD A,5
        LD (TX_STATE),A
        CALL AN_RESET
        LD HL,TX_NORM
        LD A,20
        CALL AN_RAW
        OR A
        JP NZ,TF_FAIL
        LD HL,TX_NORM
        LD DE,AP_VALUE
        LD BC,9
        LDIR
        LD HL,0
        LD DE,0
        LD A,22
        CALL AN_RAW
        OR A
        JR NZ,TF_FAIL
        LD A,1
        LD (AN_VISIBLE),A
        LD C,1
        LD A,15
        CALL AN_RAW
        CP 255
        JR Z,TF_FAIL
        XOR A
        RET
TF_FAIL:
        LD A,19
        OR A
        RET
TX_STATE: DB 0
TX_MAP: DB 32                  ; explicit configured reverse for this trial
TX_ROUTE: DB 1                     ; CRT console, non-CRT LIST (no alias)
TX_PTR: DW 0                       ; cleared before public dispatcher returns
TX_TOKEN:
TX_VALID: DB 1,0,0,0            ; fixture-issued, NOT a production allocator
TX_SESS: DB 0,0,0,0
TX_SCOPE: DB 0,0,0,0
TX_KIND: DB 1
        DB 0,0,0
TX_SSEQ: DB 0,0,0,0
TX_CAP: DB 0,0,0,0,0,0,0,0,0
TX_WORK: DB 0,0,0,0,0,0,0,0,0
TX_NORM: DB 0,0,0,0,0,0,0,0,0
TX_IMAGE:
