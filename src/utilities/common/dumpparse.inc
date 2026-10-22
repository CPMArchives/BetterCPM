; Parse bounded raw tail into tokens; no file service before full validation.
DPARSE:
        LD A,16
        LD (ROWBYTES),A
        LD HL,TAIL
DTOKEN:
        LD A,(HL)
        OR A
        JP Z,DPDONE
        CP ' '
        JP Z,DTSKIP
        CP 9
        JP Z,DTSKIP
        LD (TOKEN),HL
        LD B,0
DTSCAN:
        LD A,(HL)
        OR A
        JR Z,DTEND
        CP ' '
        JR Z,DTEND
        CP 9
        JR Z,DTEND
        CALL UPPER
        LD (HL),A
        INC HL
        INC B
        JR DTSCAN
DTEND:
        LD A,B
        LD (TOKLEN),A
        PUSH HL
        LD HL,(TOKEN)
        LD A,(HL)
        CP '/'
        JR Z,DOPTION
        LD A,(FILESET)
        OR A
        JP NZ,DPBADPOP
        INC A
        LD (FILESET),A
        LD (FNPTR),HL
        LD A,B
        LD (FNLEN),A
        JR DTPASS
DOPTION:
        LD DE,OPBARE
        CALL TOKENEQ
        JR Z,DPBARE
        LD DE,OPPAGE
        CALL TOKENEQ
        JR Z,DPPAGE
        LD DE,OP40
        CALL TOKENEQ
        JR Z,DP40
        LD HL,(TOKEN)
        LD DE,OPFROM
        LD B,6
DPFROMCHECK:
        LD A,(DE)
        CP (HL)
        JP NZ,DPBADPOP
        INC HL
        INC DE
        DJNZ DPFROMCHECK
        LD A,(TOKLEN)
        SUB 6
        JP C,DPBADPOP
        LD B,A
        LD DE,FROM
        CALL PARSEHEX
        JP C,DPBADPOP
        LD HL,FROM
        LD DE,MAXFROM
        CALL CMP32
        CALL NC,COPY32
        LD A,1
        LD (FROMSET),A
        JR DTPASS
DPBARE:
        LD A,1
        LD (BARE),A
        JR DTPASS
DPPAGE:
        LD A,1
        LD (PAGED),A
        JR DTPASS
DP40:
        LD A,1
        LD (COMPACT),A
        LD A,8
        LD (ROWBYTES),A
DTPASS:
        POP HL
        LD A,(HL)
        OR A
        JR Z,DPDONE
DTSKIP:
        INC HL
        JP DTOKEN
DPBADPOP:
        POP HL
        JP DPBAD
DPDONE:
        LD A,(FILESET)
        OR A
        JP Z,DPBAD
        LD A,(BARE)
        OR A
        JR Z,DPFILE
        LD A,(PAGED)
        LD B,A
        LD A,(COMPACT)
        OR B
        LD B,A
        LD A,(FROMSET)
        OR B
        JP NZ,DPBAD
DPFILE:
        LD HL,(FNPTR)
        LD (TOKEN),HL
        LD A,(FNLEN)
        LD (TOKLEN),A
        LD HL,(FNPTR)
        LD A,(FNLEN)
        LD B,A
        ; Reject compound/attribute syntax before invoking the shared DU lexer.
        PUSH HL
DPCHECK:
        LD A,(HL)
        CP '['
        JP Z,DPBADPOP
        CP ']'
        JP Z,DPBADPOP
        INC HL
        DJNZ DPCHECK
        POP HL
        LD A,(FNLEN)
        LD B,A
        LD A,(ODRIVE)
        LD D,A
        LD A,(OUSER)
        LD E,A
        CALL DU_PARSE
        JP C,DPBAD
        PUSH HL
        PUSH BC
        LD BC,0
        CALL DU_NEXT
        JP C,DPFILEBAD
        LD A,E
        LD (USER),A
        LD A,D
        INC A
        LD (DFCB),A
        CALL DU_NEXT
        JP NC,DPFILEBAD
        POP BC
        POP HL
        LD A,(BARE)
        OR A
        JR Z,DPNAME
        ; /BARE accepts only one optional drive letter, never a user suffix.
        PUSH HL
        LD HL,(FNPTR)
        LD A,(FNLEN)
        CP B
        JR Z,DPBAREOK
        SUB B
        CP 2
        JR NZ,DPBAREBAD
        INC HL
        LD A,(HL)
        CP ':'
        JR NZ,DPBAREBAD
DPBAREOK:
        POP HL
DPNAME:
        PUSH HL
        PUSH BC
        XOR A
        CALL FP_VALIDATE
        JP C,DPFILEBAD
        POP BC
        POP HL
        ; Initialize full FCB, preserving drive selected above.
        PUSH HL
        LD HL,DFCB+1
        LD DE,DFCB+2
        LD BC,34
        LD (HL),0
        LDIR
        LD HL,DFCB+1
        LD B,11
        LD A,' '
DPFILL:
        LD (HL),A
        INC HL
        DJNZ DPFILL
        POP HL
        LD DE,DFCB+1
        LD A,(HL)
DPFNLOOP:
        LD A,(HL)
        OR A
        JR Z,DPGOOD
        CP ' '
        JR Z,DPGOOD
        CP 9
        JR Z,DPGOOD
        CP '.'
        JR Z,DPDOT
        LD (DE),A
        INC DE
        INC HL
        JR DPFNLOOP
DPDOT:
        LD DE,DFCB+9
        INC HL
        JR DPFNLOOP
DPGOOD:
        OR A
        RET
DPBAREBAD:
        POP HL
        JP DPBAD
DPFILEBAD:
        POP BC
        POP HL
DPBAD:
        LD DE,BADOPT
        CALL MESSAGE
        LD HL,(TOKEN)
        LD A,(TOKLEN)
        LD B,A
        OR A
        JR Z,DPBADEND
DPBADPRINT:
        LD A,(HL)
        CALL CHARACTER
        INC HL
        DJNZ DPBADPRINT
DPBADEND:
        CALL NEWLINE
        SCF
        RET
TOKENEQ:
        LD HL,(TOKEN)
        LD A,(TOKLEN)
        LD B,A
TELOOP:
        LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DJNZ TELOOP
        LD A,(DE)
        OR A
        RET
; HL/B hex input, DE output32. Validate entire input; CF=invalid.
PARSEHEX:
        LD A,B
        OR A
        JR Z,PHBAD
        PUSH HL
        LD A,B
        DEC A
        LD C,A
        LD B,0
        ADD HL,BC
        LD A,(HL)
        CALL UPPER
        POP HL
        LD B,C
        INC B
        CP 'H'
        JR NZ,PHNOSUFF
        DEC B
PHNOSUFF:
        LD A,B
        OR A
        JR Z,PHBAD
        CP 9
        JR NC,PHBAD
        PUSH DE
        XOR A
        LD (DE),A
        INC DE
        LD (DE),A
        INC DE
        LD (DE),A
        INC DE
        LD (DE),A
        POP DE
PHLOOP:
        LD A,(HL)
        CALL HEXDIGIT
        RET C
        PUSH HL
        PUSH BC
        PUSH DE
        PUSH AF
        EX DE,HL
        LD B,4
PHSHIFT:
        SLA (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        DEC HL
        DEC HL
        DEC HL
        DJNZ PHSHIFT
        POP AF
        OR (HL)
        LD (HL),A
        POP DE
        POP BC
        POP HL
        INC HL
        DJNZ PHLOOP
        OR A
        RET
PHBAD:
        SCF
        RET
HEXDIGIT:
        CALL UPPER
        SUB '0'
        JR C,PHBAD
        CP 10
        JR C,HDGOOD
        SUB 7
        CP 10
        JR C,PHBAD
        CP 16
        JR NC,PHBAD
        OR A
        RET
HDGOOD:
        OR A
        RET
OPBARE: DB '/BARE',0
OPPAGE: DB '/P',0
OP40: DB '/40',0
OPFROM: DB '/FROM='
