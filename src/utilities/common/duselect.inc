; Shared internal DU selection library, bounded single and compound scopes.
; Include once. Caller defines DU_MAP (64 bytes) and DU_WORK (12 bytes).
; DU_PARSE: HL=input, B=count, D=original drive 0..15, E=user 0..31.
; Success: CF clear, HL/B=remaining filespec; DU_MAP contains the selected set.
; Failure: CF set, A=1 syntax/2 domain,
;          HL=offending byte, DU_MAP cleared. BC/DE/AF are scratch.
; DU_NEXT: BC=next logical index (initially 0). Success CF clear, D/E=DU,
;          BC=following index. Exhausted CF set and BC=512. HL/AF scratch.
; Neither routine calls BDOS. Input is never modified.
DU_PTR  EQU DU_WORK
DU_LEN  EQU DU_WORK+2
DU_DRV  EQU DU_WORK+3
DU_USR  EQU DU_WORK+4
DU_QLEN EQU DU_WORK+5
DU_VAL  EQU DU_WORK+6
DU_ODRV EQU DU_WORK+8
DU_OUSR EQU DU_WORK+9
DU_LOW  EQU DU_WORK+10
DU_HIGH EQU DU_WORK+11

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
        LD (DU_ODRV),A
        LD (DU_DRV),A
        LD A,E
        LD (DU_OUSR),A
        LD (DU_USR),A
        CALL DU_CLEAR
        LD A,D
        CP 16
        JP NC,DU_PDOM
        LD A,E
        CP 32
        JP NC,DU_PDOM
        ; Only a colon or selector bracket introduces a qualified scope.
DU_SCAN:
        LD A,B
        OR A
        JR Z,DU_PLAIN
        LD A,(HL)
        CP ':'
        JR Z,DU_SCOPE
        CP '['
        JR Z,DU_SCOPE
        CP ']'
        JR Z,DU_SCOPE
        CP ' '
        JR Z,DU_PLAIN
        INC HL
        DJNZ DU_SCAN
DU_PLAIN:
        LD HL,(DU_PTR)
        LD A,(DU_LEN)
        LD B,A
        CALL DU_SELECT
        RET
DU_SCOPE:
        LD HL,(DU_PTR)
        LD A,(DU_LEN)
        LD B,A
        LD A,(HL)
        CP '['
        JR Z,DU_OUTER
        CALL DU_TERM
        JP C,DU_FAIL
        JR DU_COLON
DU_OUTER:
        CALL DU_ADV
DU_OTERM:
        CALL DU_TERM
        JP C,DU_FAIL
        CALL DU_PEEK
        JP C,DU_FAIL
        CP ','
        JR Z,DU_OCOM
        CP ']'
        JP NZ,DU_PSYNT
        CALL DU_ADV
        JR DU_COLON
DU_OCOM:
        CALL DU_ADV
        JR DU_OTERM
DU_COLON:
        CALL DU_PEEK
        JP C,DU_FAIL
        CP ':'
        JP NZ,DU_PSYNT
        CALL DU_ADV
        OR A
        RET
DU_PDOM:
        LD A,2
        JP DU_FAIL
DU_PSYNT:
        LD A,1
        JP DU_FAIL

; Subroutines return errors through carry, allowing every stack frame to unwind.
DU_TERM:
        LD A,(DU_ODRV)
        LD (DU_DRV),A
        LD A,(DU_OUSR)
        LD (DU_USR),A
        CALL DU_PEEK
        RET C
        AND 05FH
        CP 'A'
        JR C,DU_TNUM
        CP 'P'+1
        JP NC,DU_SYNT
        SUB 'A'
        LD (DU_DRV),A
        CALL DU_ADV
        LD A,B
        OR A
        JR Z,DU_TONE
        LD A,(HL)
        CP '['
        JR Z,DU_ULIST
        CP '0'
        JR C,DU_TONE
        CP '9'+1
        JR NC,DU_TONE
DU_TNUM:
        CALL DU_NUMBER
        RET C
        LD (DU_USR),A
DU_TONE:
        CALL DU_SELECT
        OR A
        RET
DU_ULIST:
        CALL DU_ADV
DU_UITEM:
        CALL DU_PEEK
        RET C
        CP '-'
        JR Z,DU_LOPEN
        CALL DU_NUMBER
        RET C
        LD (DU_LOW),A
        CALL DU_PEEK
        RET C
        CP '-'
        JR Z,DU_HYPH
        LD A,(DU_LOW)
        LD (DU_HIGH),A
        JR DU_UFILL
DU_LOPEN:
        XOR A
        LD (DU_LOW),A
DU_HYPH:
        CALL DU_ADV
        CALL DU_PEEK
        RET C
        CP ','
        JR Z,DU_HOPEN
        CP ']'
        JR Z,DU_HOPEN
        CALL DU_NUMBER
        RET C
        LD (DU_HIGH),A
        JR DU_ORDER
DU_HOPEN:
        LD A,31
        LD (DU_HIGH),A
DU_ORDER:
        LD A,(DU_LOW)
        LD C,A
        LD A,(DU_HIGH)
        CP C
        JR NC,DU_UFILL
        LD (DU_LOW),A
        LD A,C
        LD (DU_HIGH),A
DU_UFILL:
        LD A,(DU_LOW)
        LD (DU_USR),A
DU_ULOOP:
        CALL DU_SELECT
        LD A,(DU_HIGH)
        LD C,A
        LD A,(DU_USR)
        CP C
        JR Z,DU_UEND
        INC A
        LD (DU_USR),A
        JR DU_ULOOP
DU_UEND:
        CALL DU_PEEK
        RET C
        CP ','
        JR Z,DU_UCOM
        CP ']'
        JP NZ,DU_SYNT
        CALL DU_ADV
        OR A
        RET
DU_UCOM:
        CALL DU_ADV
        JP DU_UITEM

; One or two decimal digits, with no sign or whitespace. Result A=0..31.
DU_NUMBER:
        XOR A
        LD (DU_VAL),A
        LD C,0
DU_DIGIT:
        CALL DU_PEEK
        RET C
        CP '0'
        JP C,DU_SYNT
        CP '9'+1
        JP NC,DU_SYNT
        SUB '0'
        LD E,A
        INC C
        LD A,C
        CP 3
        JP NC,DU_SYNT
        LD A,(DU_VAL)
        ADD A,A
        LD D,A
        ADD A,A
        ADD A,A
        ADD A,D
        ADD A,E
        CP 32
        JP NC,DU_RANGE
        LD (DU_VAL),A
        CALL DU_ADV
        LD A,B
        OR A
        JR Z,DU_NDONE
        LD A,(HL)
        CP '0'
        JR C,DU_NDONE
        CP '9'+1
        JR C,DU_DIGIT
DU_NDONE:
        LD A,(DU_VAL)
        OR A
        RET
DU_PEEK:
        LD A,B
        OR A
        JP Z,DU_SYNT
        LD A,(HL)
        OR A
        RET
DU_ADV:
        INC HL
        DEC B
        RET
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
DU_RANGE:
        LD A,2
        SCF
        RET
DU_SYNT:
        LD A,1
        SCF
        RET
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
