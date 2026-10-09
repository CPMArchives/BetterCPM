; Shared internal DU selection library, initial conventional-scope increment.
; Include once. Caller defines DU_MAP (64 bytes) and DU_WORK (12 bytes).
; DU_PARSE: HL=input, B=count, D=original drive 0..15, E=user 0..31.
; Success: CF clear, HL/B=remaining filespec; DU_MAP selects one DU.
; Failure: CF set, A=1 syntax/2 domain/3 extended form not yet implemented,
;          HL=offending byte, DU_MAP cleared. BC/DE/AF are scratch.
; DU_NEXT: BC=next logical index (initially 0). Success CF clear, D/E=DU,
;          BC=following index. Exhausted CF set and BC=512. HL/AF scratch.
; Neither routine calls BDOS. Input is never modified.
DU_PTR  EQU DU_WORK
DU_LEN  EQU DU_WORK+2
DU_DRV  EQU DU_WORK+3
DU_USR  EQU DU_WORK+4
DU_QLEN EQU DU_WORK+5
DU_NUM  EQU DU_WORK+6
DU_DIG  EQU DU_WORK+7

DU_CLEAR:
        PUSH HL
        PUSH BC
        LD HL,DU_MAP
        LD B,64
        XOR A
DU_ZERO:
        LD (HL),A
        INC HL
        DJNZ DU_ZERO
        POP BC
        POP HL
        RET

DU_PARSE:
        LD (DU_PTR),HL
        LD A,B
        LD (DU_LEN),A
        LD A,D
        LD (DU_DRV),A
        LD A,E
        LD (DU_USR),A
        CALL DU_CLEAR
        LD A,D
        CP 16
        JP NC,DU_RANGE
        LD A,E
        CP 32
        JP NC,DU_RANGE
        LD C,0
DU_SCAN:
        LD A,B
        OR A
        JR Z,DU_PLAIN
        LD A,(HL)
        CP '['
        JP Z,DU_EXT
        CP ']'
        JP Z,DU_EXT
        CP ' '
        JR Z,DU_PLAIN
        CP ':'
        JR Z,DU_QUAL
        INC HL
        INC C
        DJNZ DU_SCAN
DU_PLAIN:
        LD HL,(DU_PTR)
        LD A,(DU_LEN)
        LD B,A
        JR DU_SELECT
DU_QUAL:
        LD A,C
        LD (DU_QLEN),A
        OR A
        JP Z,DU_SYNT
        LD HL,(DU_PTR)
        LD A,(HL)
        AND 05FH
        CP 'A'
        JR C,DU_NUMBER
        CP 'P'+1
        JP NC,DU_SYNT
        SUB 'A'
        LD (DU_DRV),A
        INC HL
        DEC C
        JR Z,DU_FINQ
DU_NUMBER:
        XOR A
        LD (DU_NUM),A
        LD (DU_DIG),A
DU_DIGIT:
        LD A,(HL)
        CP '0'
        JP C,DU_SYNT
        CP '9'+1
        JP NC,DU_SYNT
        SUB '0'
        LD E,A
        LD A,(DU_DIG)
        INC A
        CP 3
        JP NC,DU_SYNT
        LD (DU_DIG),A
        LD A,(DU_NUM)
        ADD A,A
        LD D,A
        ADD A,A
        ADD A,A
        ADD A,D
        ADD A,E
        CP 32
        JP NC,DU_RANGE
        LD (DU_NUM),A
        INC HL
        DEC C
        JR NZ,DU_DIGIT
        LD (DU_USR),A
DU_FINQ:
        INC HL
        LD A,(DU_QLEN)
        INC A
        LD C,A
        LD A,(DU_LEN)
        SUB C
        LD B,A
DU_SELECT:
        PUSH HL
        PUSH BC
        LD A,(DU_DRV)
        LD D,A
        LD A,(DU_USR)
        LD E,A
        ; Byte = drive*4 + user/8; mask = 1 << (user & 7).
        LD A,D
        ADD A,A
        ADD A,A
        LD C,A
        LD A,E
        SRL A
        SRL A
        SRL A
        ADD A,C
        LD C,A
        LD B,0
        LD HL,DU_MAP
        ADD HL,BC
        LD A,E
        AND 7
        LD B,A
        LD A,1
        JR Z,DU_BIT
DU_SHIFT:
        ADD A,A
        DJNZ DU_SHIFT
DU_BIT:
        OR (HL)
        LD (HL),A
        POP BC
        POP HL
        OR A
        RET
DU_EXT:
        LD A,3
        JR DU_FAIL
DU_RANGE:
        LD A,2
        JR DU_FAIL
DU_SYNT:
        LD A,1
DU_FAIL:
        PUSH AF
        CALL DU_CLEAR
        POP AF
        SCF
        RET

DU_NEXT:
        LD A,B
        CP 2
        JR NC,DU_END
        PUSH BC
        LD H,B
        LD L,C
        SRL H
        RR L
        SRL H
        RR L
        SRL H
        RR L
        LD DE,DU_MAP
        ADD HL,DE
        LD A,C
        AND 7
        LD E,A
        LD A,1
        JR Z,DU_TEST
DU_NSH:
        ADD A,A
        DEC E
        JR NZ,DU_NSH
DU_TEST:
        AND (HL)
        POP BC
        JR NZ,DU_FOUND
        INC BC
        JR DU_NEXT
DU_FOUND:
        LD A,C
        AND 31
        LD E,A
        LD A,C
        RLCA
        RLCA
        RLCA
        AND 7
        LD D,A
        LD A,B
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,D                      ; disjoint high/low drive bits
        LD D,A
        INC BC
        OR A
        RET
DU_END:
        LD BC,512
        SCF
        RET
