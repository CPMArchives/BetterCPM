; Shared standalone /VER recognizer. Exact token only, case insensitive.
; UV_QUERY: HL/B span, DE banner. CF=handled. Registers otherwise preserved.
; UV_CHECK: command-tail wrapper; handled requests warm boot without operations.
; Standalone builds load their banner; RCP-derived transient wrappers pass DE.
UV_CHECK:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
; @version-banner@
        LD HL,0081H
        LD A,(0080H)
        LD B,A
        CALL UV_QUERY
        JR C,UV_EXIT
        POP HL
        POP DE
        POP BC
        POP AF
        RET
UV_EXIT:
        POP HL
        POP DE
        POP BC
        POP AF
        JP 00000H
UV_QUERY:
        PUSH BC
        PUSH DE
        PUSH HL
        LD C,0
        LD A,B
        OR A
        JR Z,UV_NONE
UV_SCAN:
        LD A,(HL)
        CP ' '
        JR Z,UV_SPACE
        INC C
        PUSH BC
        PUSH HL
        LD DE,UV_WORD
        LD C,4
UV_MATCH:
        LD A,B
        OR A
        JR Z,UV_NOM
        LD A,(HL)
        OR 020H
        PUSH HL
        LD H,A
        LD A,(DE)
        CP H
        POP HL
        JR NZ,UV_NOM
        INC HL
        INC DE
        DEC B
        DEC C
        JR NZ,UV_MATCH
        LD A,B
        OR A
        JR Z,UV_FOUND
        LD A,(HL)
        CP ' '
        JR Z,UV_FOUND
UV_NOM:
        POP HL
        POP BC
UV_SKIP:
        LD A,(HL)
        CP ' '
        JR Z,UV_SPACE
        INC HL
        DJNZ UV_SKIP
        JR UV_NONE
UV_SPACE:
        INC HL
        DJNZ UV_SCAN
UV_NONE:
        POP HL
        POP DE
        POP BC
        OR A
        RET
UV_FOUND:
        POP HL
        POP BC
        LD A,C
        CP 1
        JR NZ,UV_BAD
        ; The first token is /VER; its remaining tail must contain only spaces.
        LD A,B
        SUB 4
        LD B,A
        INC HL
        INC HL
        INC HL
        INC HL
        JR Z,UV_PRINT
UV_REST:
        LD A,(HL)
        CP ' '
        JR NZ,UV_BAD
        INC HL
        DJNZ UV_REST
UV_PRINT:
        POP HL
        POP DE
        POP BC
        PUSH BC
        PUSH DE
        PUSH HL
        LD C,9
        CALL 00005H
        POP HL
        POP DE
        POP BC
        SCF
        RET
UV_BAD:
        POP HL
        POP DE
        POP BC
        PUSH BC
        PUSH DE
        PUSH HL
        LD DE,UV_ERROR
        LD C,9
        CALL 00005H
        POP HL
        POP DE
        POP BC
        SCF
        RET
UV_WORD: DB '/ver'
UV_ERROR: DB 'Invalid /VER usage.',13,10,'$'
