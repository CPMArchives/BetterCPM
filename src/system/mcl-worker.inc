; Private MCL template: copied and fixed up inside the reconstructed CCP.
; IX owns the fixed 128-byte object; all cache fields are write-before-read.
; Entry points are in pds-worker.mac; no public API or persistent pointers.
        JP MC_NEXT
        JP MC_CANCEL
        JP MC_NEW
MC_LOCATE:
        LD HL,LY_PD2
        LD DE,MC_HEAD
        LD B,12
MC_CHECK:
        LD A,(DE)
        CP (HL)
        JR NZ,MC_FATAL
        INC DE
        INC HL
        DJNZ MC_CHECK
        LD HL,(MC_OWNER)
        LD A,(MC_HEAD+6)
        OR A
        RET
MC_FATAL:
        LD DE,MC_PDSMSG
        LD C,9
        CALL LY_BDOS
MC_STOP:
        JR MC_STOP
MC_INPUT:
        LD HL,(MC_COUNT)
        RET
MC_CANCEL:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        CALL MC_LOCATE
        CP 128
        JR NZ,MC_CRET
        PUSH HL
        POP IX
        CALL MC_ZERO
MC_CRET:
        POP IX
        POP HL
        POP DE
        POP BC
        POP AF
        RET
MC_ZERO:
        LD (IX+1),0                    ; withdraw publication before any update
        PUSH IX
        POP HL
        LD B,128
        XOR A
MC_ZLOOP:
        LD (HL),A
        INC HL
        DJNZ MC_ZLOOP
        RET
MC_NEXT:
        CALL MC_LOCATE
        CP 128
        JR NZ,MC_NONE
        PUSH HL
        POP IX
        LD A,(IX+1)
        OR A
        JR NZ,MC_PENDING
        LD B,128
        CALL MC_ZCHECK
        JR NZ,MC_BAD
MC_NONE:
        OR A
        RET
MC_PENDING:
        DEC A
        JR NZ,MC_BAD
        LD B,(IX+0)
        LD A,B
        DEC A
        CP 125
        JR NC,MC_BAD
        INC HL
        INC HL
        CALL MC_TEXT
        JR C,MC_BAD
        LD C,B
        LD B,0
        ADD HL,BC
        LD A,126
        SUB C
        LD B,A
        CALL MC_ZCHECK
        JR NZ,MC_BAD
        LD A,(IX+0)
        CALL MC_INPUT
        LD (HL),A
        INC HL
        EX DE,HL
        PUSH IX
        POP HL
        INC HL
        INC HL
        LD C,A
        LD B,0
        LDIR
        JP MC_NEW
MC_ZCHECK:
        LD A,(HL)
        OR A
        RET NZ
        INC HL
        DJNZ MC_ZCHECK
        RET
MC_BAD:
        CALL MC_ZERO
        LD DE,MC_BADMSG
        JP MC_MESSAGE
MC_NEW:
        CALL MC_LOCATE
        CP 128
        RET NZ                         ; disabled preserves the legacy whole line
        PUSH HL
        POP IX
        CALL MC_INPUT
        LD B,(HL)
        INC HL
        LD A,B
        CP 128
        JR NC,MC_SYNTAX
        CALL MC_TEXT                   ; validate the complete line before dispatch
        JR C,MC_SYNTAX
MC_START:
        LD (MC_FIRST),HL
        LD DE,0                        ; D=nonspace, E=selected segment length
        LD C,D                         ; quote state
MC_SCAN:
        LD A,B
        OR A
        JR Z,MC_BOUNDARY
        LD A,(HL)
        CP ';'
        JR NZ,MC_CHARACTER
        LD A,C
        OR A
        JR Z,MC_BOUNDARY
        LD A,';'
MC_CHARACTER:
        CP '"'
        JR NZ,MC_WORD
        LD A,C
        XOR 1
        LD C,A
        LD A,'"'
MC_WORD:
        CP ' '
        JR Z,MC_ADVANCE
        LD D,1
MC_ADVANCE:
        INC HL
        INC E
        DEC B
        JR MC_SCAN
MC_BOUNDARY:
        LD A,D
        OR A
        JR NZ,MC_PICK
        LD A,B
        OR A
        JR Z,MC_EMPTY
        INC HL
        DEC B
        JR MC_START
MC_PICK:
        LD A,E
        LD (MC_LENGTH),A
        LD A,B
        OR A
        JR Z,MC_REMAINDER
        INC HL                         ; discard exactly this separator
        DEC B
MC_REMAINDER:
        PUSH HL
        PUSH BC
        CALL MC_ZERO
        POP BC
        POP HL
        LD A,B
        OR A
        JR Z,MC_COPY
        LD (IX+0),A
        PUSH IX
        POP DE
        INC DE
        INC DE
        LD C,B
        LD B,0
        LDIR
        LD (IX+1),1                    ; publish only after the remainder is complete
MC_COPY:
        CALL MC_INPUT
        LD A,(MC_LENGTH)
        LD (HL),A
        INC HL
        EX DE,HL
        LD HL,(MC_FIRST)
        LD C,A
        LD B,0
        LDIR
        SCF
        RET
MC_SYNTAX:
        CALL MC_ZERO
        CALL MC_INPUT
        LD (HL),0
        LD DE,MC_SYMSG
        JP MC_MESSAGE
MC_EMPTY:
        CALL MC_ZERO
        CALL MC_INPUT
        LD (HL),0
        OR A
        RET
MC_MESSAGE:
        LD C,9
        CALL LY_BDOS
        OR A
        RET
; HL/B text. Preserve both; carry means invalid printable text or quotes.
MC_TEXT:
        PUSH HL
        PUSH BC
        LD C,0
        LD A,B
        OR A
        JR Z,MC_TEXTEND
MC_TEXTLOOP:
        LD A,(HL)
        CP 32
        JR C,MC_TEXTBAD
        CP 127
        JR NC,MC_TEXTBAD
        CP '"'
        JR NZ,MC_TEXTNEXT
        LD A,C
        XOR 1
        LD C,A
MC_TEXTNEXT:
        INC HL
        DJNZ MC_TEXTLOOP
MC_TEXTEND:
        LD A,C
        RRA
        JR MC_TEXTRETURN
MC_TEXTBAD:
        SCF
MC_TEXTRETURN:
        POP BC
        POP HL
        RET
MC_BADMSG:
MC_SYMSG: DB 'MCL invalid.',13,10,'$'
MC_PDSMSG: DB 'PDS invalid; cold boot required.',13,10,'$'
MC_COUNT: DW 0
MC_OWNER: DW 0
MC_HEAD: DB 0,0,0,0,0,0,0,0,0,0,0,0
MC_FIRST: DW 0
MC_LENGTH: DB 0
