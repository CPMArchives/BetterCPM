; @ndr-lookup@

; Resolve NAME: at shell token boundaries before dispatch/FCB preparation.
; Work in DATA; RAW is temporary suffix storage until CCP_UPPER captures it.
; Every rewrite is bounded to 127 bytes. Fixed Duu: spelling keeps this small;
; normal numeric parsers still own DU semantics. Quoted text is literal.
CN_NORMAL:
        CALL CN_LOOK
        RET NZ
        LD HL,CCP_DATA
        LD A,(CCP_COUNT)
        LD B,A
        LD A,(HL)
        CP ':'
        JR Z,CN_SKIP
        CP '.'
        JR NZ,CN_WORD
CN_SKIP:
        INC HL
        DEC B
CN_WORD:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        CP '"'
        JP Z,CN_QUOTED
        PUSH HL
        PUSH BC
        LD C,0
CN_CSCAN:
        LD A,(HL)
        CP ':'
        JR Z,CN_CFOUND
        INC C
        LD A,C
        CP 9
        JR NC,CN_UNCHANGED
        INC HL
        DJNZ CN_CSCAN
        JR CN_UNCHANGED
CN_CFOUND:
        INC HL
        DEC B
        PUSH HL
        PUSH BC
        LD E,C
        INC E
        LD D,0
        OR A
        SBC HL,DE
        LD B,C
        XOR A
        CALL CN_CALL
        POP BC
        POP HL
        OR A
        JR NZ,CN_UNCHANGED
        ; Stack contains original remaining count and the prefix start.
        POP AF
        SUB B
        LD C,A                      ; old qualifier length
        LD A,(CCP_COUNT)
        SUB C
        ADD A,4
        CP 128
        JR NC,CN_LONG
        LD (CCP_COUNT),A
        PUSH BC                     ; suffix count
        PUSH HL                     ; suffix pointer
        LD HL,CCP_FCB
        LD A,D
        ADD A,'A'-1
        LD (HL),A
        INC HL
        LD A,E
        LD D,'0'-1
CN_NUM:
        INC D
        SUB 10
        JR NC,CN_NUM
CN_NUMEND:
        LD (HL),D
        INC HL
        ADD A,'0'+10
        LD (HL),A
        INC HL
        LD (HL),':'
        POP HL
        POP BC
        PUSH BC
        LD A,B
        OR A
        JR Z,CN_NOTAIL
        LD C,B
        LD B,0
        LD DE,CCP_RAW
        LDIR
CN_NOTAIL:
        POP AF                      ; original suffix count in A
        POP DE                      ; old prefix start
        LD HL,CCP_FCB
        LD BC,4
        LDIR
        PUSH DE                     ; resume immediately after qualifier
        OR A
        JR Z,CN_NEWEND
        LD C,A
        LD B,0
        LD HL,CCP_RAW
        LDIR
CN_NEWEND:
        POP HL
        LD B,A
        JR CN_TEXT
CN_UNCHANGED:
        POP BC
        POP HL
CN_TEXT:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        INC HL
        DEC B
        CP ' '
        JR Z,CN_BOUND
        CP '='
        JR NZ,CN_TEXT
CN_BOUND:
        JP CN_WORD
CN_QUOTED:
        LD C,A
        INC HL
        DEC B
CN_QLOOP:
        LD A,B
        OR A
        RET Z
        LD A,(HL)
        INC HL
        DEC B
        CP C
        JR NZ,CN_QLOOP
        JR CN_TEXT
CN_LONG:
        POP HL
        LD DE,CCP_UNKNOWN
        LD C,9
        CALL BDOS
        SCF
        RET

; Display annotation only at the main prompt, not numeric DU reports.
CN_PROMPT:
        CALL CN_LOOK
        RET NZ
        LD C,25
        CALL BDOS
        INC A
        PUSH AF
        LD E,255
        LD C,32
        CALL BDOS
        LD E,A
        POP AF
        LD D,A
        LD A,1
        CALL CN_CALL
        OR A
        RET NZ
        LD A,' '
        CALL CN_CHAR
        LD A,'['
        CALL CN_CHAR
        LD B,8
CN_PNAME:
        LD A,(HL)
        CP ' '
        JR Z,CN_PCLOSE
        CALL CN_CHAR
        INC HL
        DJNZ CN_PNAME
CN_PCLOSE:
        LD A,']'
        CALL CN_CHAR
        LD A,' '
CN_CHAR:
        PUSH HL
        PUSH BC
        LD E,A
        LD C,2
        CALL BDOS
        POP BC
        POP HL
        RET
