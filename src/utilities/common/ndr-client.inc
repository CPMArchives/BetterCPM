; Optional NDR discovery: never retain a service address across manager changes.
CN_LOOK:
        LD DE,CN_REQUEST
        LD C,182
        CALL BDOS
        OR A
        RET NZ
        LD (CN_CALL+1),HL
        RET
CN_CALL:
        JP 0

CN_REQUEST: DB 1,20,0,0,'NDR ',1,0
        DW 0,0,0,0,0

; Resolve a bounded NAME: prefix through the one authoritative NDR service.
; HL/B prefix input. Success consumes NAME:, DE=drive 1..16/user, CF set.
; Failure preserves HL/B and clears CF. All lookup uses the provider's resolver.
CN_PREFIX:
        PUSH HL
        PUSH BC
        LD C,0
CN_SCAN:
        LD A,B
        OR A
        JR Z,CN_NO
        LD A,(HL)
        OR A
        JR Z,CN_NO
        CP ':'
        JR Z,CN_FOUND
        CP ' '
        JR Z,CN_NO
        INC C
        LD A,C
        CP 9
        JR NC,CN_NO
        INC HL
        DJNZ CN_SCAN
CN_NO:
        POP BC
        POP HL
        OR A
        RET
CN_FOUND:
        LD A,C
        OR A
        JR Z,CN_NO
        PUSH BC
        CALL CN_LOOK
        POP BC
        JR NZ,CN_NO
        LD B,C
        POP DE
        POP HL
        PUSH HL
        PUSH DE
        PUSH BC
        XOR A
        CALL CN_CALL
        POP BC
        OR A
        JR NZ,CN_NO
        LD A,C
        POP BC
        POP HL
        INC A
        LD C,A
CN_CONSUME:
        INC HL
        DEC B
        DEC C
        JR NZ,CN_CONSUME
        SCF
        RET
