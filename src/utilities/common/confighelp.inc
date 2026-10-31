; Disposable startup query area. Normal CONFIG's private stack is below 4000h;
; this appendix is used only before INIT, which may reuse its memory for data.
; Keep normal code/data below 3E00h; both builders verify the split layout.
CF_MAIN_END:
        REPT 04000H-$
        DB 0FFH
        ENDM
CF_QUERY:
        LD A,(80H)
        CP 128
        RET NC
        LD B,A
        LD HL,81H
        XOR A
        LD (CQ_QUOTE),A
        INC A
        LD (CQ_BOUND),A
CQ_SCAN:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        CP '"'
        JR Z,CQ_TOGGLE
        LD A,(CQ_QUOTE)
        OR A
        JR NZ,CQ_ADVANCE
        LD A,(HL)
        CP ' '
        JR Z,CQ_SPACE
        CP 9
        JR Z,CQ_SPACE
        LD A,(CQ_BOUND)
        OR A
        JR Z,CQ_WORD
        LD A,(HL)
        CP '/'
        JR NZ,CQ_WORD
        LD DE,CQ_HELP
        CALL CQ_MATCH
        JR C,CQ_SHOW
        LD DE,CQ_H
        CALL CQ_MATCH
        JR C,CQ_SHOW
CQ_WORD:
        XOR A
        LD (CQ_BOUND),A
CQ_ADVANCE:
        INC HL
        DEC B
        JR CQ_SCAN
CQ_SPACE:
        LD A,1
        LD (CQ_BOUND),A
        JR CQ_ADVANCE
CQ_TOGGLE:
        LD A,(CQ_QUOTE)
        XOR 1
        LD (CQ_QUOTE),A
        XOR A
        LD (CQ_BOUND),A
        JR CQ_ADVANCE
; Exact unquoted query word, case insensitive, ending at whitespace or EOF.
; Preserve the scanner's bounded cursor on both match and fall-through.
CQ_MATCH:
        PUSH HL
        PUSH BC
CQ_COMPARE:
        LD A,(DE)
        OR A
        JR Z,CQ_END
        LD C,A
        LD A,B
        OR A
        JR Z,CQ_NO
        LD A,(HL)
        XOR C
        AND 0DFH
        JR NZ,CQ_NO
        INC HL
        INC DE
        DEC B
        JR CQ_COMPARE
CQ_END:
        LD A,B
        OR A
        JR Z,CQ_YES
        LD A,(HL)
        CP ' '
        JR Z,CQ_YES
        CP 9
        JR Z,CQ_YES
CQ_NO:
        POP BC
        POP HL
        OR A
        RET
CQ_YES:
        POP BC
        POP HL
        SCF
        RET
CQ_SHOW:
        LD DE,CQ_TEXT
        LD C,9
        CALL BDOS
        JP 0
CQ_QUOTE: DB 0
CQ_BOUND: DB 0
CQ_HELP: DB '/HELP',0
CQ_H: DB '/H',0
; @config-help-text@
