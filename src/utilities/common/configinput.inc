; CONFIG's inline input binding. No resident or loaded-monitor dependency.
CI_READ:
        LD C,6
        LD E,255
        CALL BDOS
        OR A
        JR Z,CI_READ
        LD (CI_LAST),A
        CP 3
        JR Z,CI_ESCAPE
        CP 127
        RET NZ
        LD A,8
        RET
CI_ESCAPE:
        LD A,27
        RET
CI_PUT:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD C,6
        CALL BDOS
        POP HL
        POP DE
        POP BC
        POP AF
        RET
CI_CRLF:
        LD A,13
        CALL CI_PUT
        LD A,10
        JP CI_PUT
CI_MESSAGE:
        PUSH HL
        CALL CI_CRLF
        POP HL
CI_TEXT:
        LD A,(HL)
        INC HL
        OR A
        JP Z,CI_CRLF
        CALL CI_PUT
        JR CI_TEXT
CI_LIMIT:DB 'Input limit reached.',0
CI_MARKER:
        PUSH BC
        LD B,A
        LD A,(HASREV)
        OR A
        LD A,B
        JR Z,CI_FALLBACK
        POP BC
        JP INVERSE
CI_FALLBACK:
        POP BC
        LD A,'_'
        JP CI_PUT
; @ui-input@
; @ui-inline@
