; Transient DIR command transaction. HL/B=tail, D/E=captured caller DU.
; One operand and command-wide options, in either order. Original tail is
; unchanged. All tokens validate before FS_PARSE publishes a selection map.
DP_PARSE:
        LD (DP_DU),DE
        XOR A
        LD (DP_ERROR),A
        LD (DP_HAS),A
        LD (DP_ALEN),A
        LD (DN_REV),A
        LD (DT_SHOWATTR),A
        LD (DG_PAGE),A
        LD (DG_LINES),A
        LD (DG_MEASURE),A
        LD (DC_REQUEST),A
        LD A,'N'
        LD (DN_MODE),A
        LD A,'K'
        LD (DT_UNIT),A
        CALL FS_CLEAR
DP_TOKEN:
        LD A,B
        OR A
        JR Z,DP_DONE
        LD A,(HL)
        CP ' '
        JR NZ,DP_START
        INC HL
        DEC B
        JR DP_TOKEN
DP_START:
        LD (DP_TOK),HL
        LD C,0
DP_SCAN:
        LD A,B
        OR A
        JR Z,DP_STOP
        LD A,(HL)
        CP ' '
        JR Z,DP_STOP
        INC HL
        INC C
        DEC B
        JR DP_SCAN
DP_STOP:
        LD (DP_NEXT),HL
        LD A,B
        LD (DP_REM),A
        LD A,C
        LD (DP_LEN),A
        LD HL,(DP_TOK)
        LD A,(HL)
        CP '/'
        JR Z,DP_SWITCH
        LD A,(DP_HAS)
        OR A
        JR NZ,DP_BAD
        INC A
        LD (DP_HAS),A
        LD A,C
        LD (DP_ALEN),A
        LD B,0
        LD DE,DP_ARG
        LDIR
        JR DP_RESUME
DP_SWITCH:
        CALL DP_OPTION
        JR C,DP_BAD
DP_RESUME:
        LD HL,(DP_NEXT)
        LD A,(DP_REM)
        LD B,A
        JR DP_TOKEN
DP_DONE:
        LD HL,DP_ARG
        LD A,(DP_ALEN)
        LD B,A
        LD DE,(DP_DU)
        JP FS_PARSE
DP_BAD:
        CALL FS_CLEAR
        SCF
        RET
DP_OPTION:
        LD A,1
        LD (DP_ERROR),A
        LD A,(DP_LEN)
        CP 2
        JP Z,DP_ATTR
        CP 4
        JR Z,DP_FORM
        CP 5
        JP NZ,DP_OPBAD
DP_FORM:
        INC HL
        LD A,(HL)
        AND 0DFH
        CP 'Z'
        JP Z,DP_UNIT
        CP 'C'
        JP Z,DP_COLUMNS
        CP 'S'
        JP NZ,DP_OPBAD
        INC HL
        LD A,(HL)
        CP '='
        JP NZ,DP_OPBAD
        INC HL
        LD A,(HL)
        AND 0DFH
        LD C,A
        CP 'N'
        JR Z,DP_KEY
        CP 'T'
        JR Z,DP_KEY
        CP 'Z'
        JR Z,DP_KEY
        CP 'U'
        JP NZ,DP_OPBAD
DP_KEY:
        LD E,0
        LD A,(DP_LEN)
        CP 4
        JR Z,DP_SET
        LD A,C
        CP 'U'
        JP Z,DP_OPBAD
        INC HL
        LD A,(HL)
        CP '+'
        JR Z,DP_SET
        CP '-'
        JP NZ,DP_OPBAD
        INC E
DP_SET:
        LD A,C
        LD (DN_MODE),A
        LD A,E
        LD (DN_REV),A
DP_OK:
        XOR A
        LD (DP_ERROR),A
        RET
DP_ATTR:
        INC HL
        LD A,(HL)
        AND 0DFH
        CP 'Z'
        JR Z,DP_KUNIT
        CP 'P'
        JR Z,DP_PAGING
        CP 'A'
        JP NZ,DP_OPBAD
        LD A,1
        LD (DT_SHOWATTR),A
        JR DP_OK
DP_PAGING:
        LD A,1
        LD (DG_PAGE),A
        JR DP_OK
DP_KUNIT:
        LD A,'K'
        JR DP_USET
DP_UNIT:
        LD A,(DP_LEN)
        CP 4
        JP NZ,DP_OPBAD
        INC HL
        LD A,(HL)
        CP '='
        JP NZ,DP_OPBAD
        INC HL
        LD A,(HL)
        AND 0DFH
        CP 'K'
        JR Z,DP_USET
        CP 'S'
        JR Z,DP_USET
        CP 'E'
        JP NZ,DP_OPBAD
DP_USET:
        LD (DT_UNIT),A
        JR DP_OK
DP_COLUMNS:
        LD A,(DP_LEN)
        CP 4
        JP NZ,DP_OPBAD
        INC HL
        LD A,(HL)
        CP '='
        JP NZ,DP_OPBAD
        INC HL
        LD A,(HL)
        CP '1'
        JR Z,DP_CSET
        CP '2'
        JR Z,DP_CSET
        CP '4'
        JP NZ,DP_OPBAD
DP_CSET:
        SUB '0'
        LD (DC_REQUEST),A
        JP DP_OK
DP_OPBAD:
        SCF
        RET
DP_REJECT:
        LD A,(DP_ERROR)
        OR A
        JP Z,BC_DBAD
        LD DE,DP_MSG
        CALL BC_PRINT
        JP BC_DURST
DP_DU: DW 0
DP_TOK: DW 0
DP_NEXT: DW 0
DP_LEN: DB 0
DP_REM: DB 0
DP_HAS: DB 0
DP_ALEN: DB 0
DP_ERROR: DB 0
DP_ARG: DS 128
DP_MSG: DB 13,10,'Invalid option.',13,10,'$'
