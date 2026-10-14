; Direct DUP entry: parse everything before initialization or media operations.
DCPARSE:
        XOR A
        LD (DCMODE),A
        LD (DCRUN),A
        LD (DCNEXT),A
        LD A,(0080H)
        LD C,A
        LD HL,0081H
        CALL DCSKIP
        JR NC,DCSTART
        OR A                          ; empty is normal interactive invocation
        RET
DCSTART:
        LD A,(HL)
        CP '/'
        JP NZ,DCFAIL
        INC HL
        DEC C
        LD DE,DCFMT
        LD B,6
        CALL DCMATCH
        LD A,1
        JR NC,DCOP
        LD DE,DCCOPY
        LD B,4
        CALL DCMATCH
        LD A,2
        JR NC,DCOP
        LD DE,DCCHECK
        LD B,5
        CALL DCMATCH
        LD A,3
        JP C,DCFAIL
DCOP:
        LD (DCMODE),A
        CALL DCSKIP
        JP C,DCFAIL
        CALL DCDRIVE
        RET C
        LD (DCFIRST),A
        LD A,(DCMODE)
        CP 2
        JR NZ,DCEND
        CALL DCSKIP
        JP C,DCFAIL
        CALL DCDRIVE
        RET C
        OR A
        JP Z,DCFAIL                    ; COPY destination A is forbidden
        LD (DCSECOND),A
DCEND:
        CALL DCSKIP
        JP NC,DCFAIL
        OR A
        RET
DCFAIL:
        SCF
        RET
DCSKIP:
        LD A,C
        OR A
        JR Z,DCEMPTY
        LD A,(HL)
        CP ' '
        RET NZ
        INC HL
        DEC C
        JR DCSKIP
DCEMPTY:
        SCF
        RET
; Match a complete operation token, preserving the cursor on mismatch.
DCMATCH:
        PUSH HL
        PUSH BC
DCMLOOP:
        LD A,C
        OR A
        JR Z,DCMISS
        LD A,(HL)
        AND 05FH
        PUSH BC
        LD B,A
        LD A,(DE)
        CP B
        POP BC
        JR NZ,DCMISS
        INC HL
        INC DE
        DEC C
        DJNZ DCMLOOP
        LD A,C
        OR A
        JR Z,DCMISS
        LD A,(HL)
        CP ' '
        JR NZ,DCMISS
        POP DE                        ; discard saved BC, retain consumed cursor
        POP DE
        OR A
        RET
DCMISS:
        POP BC
        POP HL
        SCF
        RET
DCDRIVE:
        LD A,C
        CP 2
        JR C,DCFAIL
        LD A,(HL)
        AND 05FH
        SUB 'A'
        CP 4
        JR NC,DCFAIL
        LD (DCTEMP),A
        INC HL
        DEC C
        LD A,(HL)
        CP ':'
        JR NZ,DCFAIL
        INC HL
        DEC C
        LD A,C
        OR A
        JR Z,DCDONE
        LD A,(HL)
        CP ' '
        JR NZ,DCFAIL
DCDONE:
        LD A,(DCTEMP)
        OR A
        RET
DCBAD:
        LD HL,DCUSAGE
        CALL PUTS
        JP DONE
DCPAUSE:
        LD A,(DCMODE)
        OR A
        RET NZ
        JP PAUSE
DCFMT: DB 'FORMAT'
DCCOPY: DB 'COPY'
DCCHECK: DB 'CHECK'
DCUSAGE: DB 13,10,'Usage: DUP [/FORMAT A: | /COPY A: B: | /CHECK A: | /VER]',13,10,0
DCMODE: DB 0
DCRUN: DB 0
DCNEXT: DB 0
DCFIRST: DB 0
DCSECOND: DB 0
DCTEMP: DB 0
