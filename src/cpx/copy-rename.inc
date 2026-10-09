; Transient collision rename. Candidate names remain separate until validated.
CTRENAME:
        LD DE,CTRASK
        CALL BC_PRINT
        XOR A
        LD (CTRLEN),A
        LD (CTROVER),A
CTRREAD:
        LD E,0FFH
        LD C,6
        CALL BDOS
        OR A
        JR Z,CTRREAD
        CP 3
        JP Z,CTABORT
        CP 13
        JP Z,CTRLINE
        CP 10
        JP Z,CTRLINE
        CP 8
        JR Z,CTRBACK
        CP 127
        JR Z,CTRBACK
        CP 'a'
        JR C,CTRSTORE
        CP 'z'+1
        JR NC,CTRSTORE
        SUB 32
CTRSTORE:
        LD (CTRCHAR),A
        LD A,(CTRLEN)
        CP 126
        JR NC,CTRFULL
        LD E,A
        LD D,0
        LD HL,CTRBUF
        ADD HL,DE
        LD A,(CTRCHAR)
        LD (HL),A
        LD HL,CTRLEN
        INC (HL)
        CALL BC_PCHAR
        JR CTRREAD
CTRFULL:
        LD A,1
        LD (CTROVER),A
        JR CTRREAD
CTRBACK:
        LD A,(CTRLEN)
        OR A
        JR Z,CTRREAD
        DEC A
        LD (CTRLEN),A
        LD DE,CTRERASE
        CALL BC_PRINT
        JR CTRREAD
CTRLINE:
        LD DE,BC_NL
        CALL BC_PRINT
        LD A,(CTROVER)
        OR A
        JP NZ,CTRINVALID
        LD A,(CTRLEN)
        OR A
        JP Z,CTPROMPT
        LD B,A
        LD HL,CTRFCB
        LD (BC_COFCP),HL
        LD HL,CTRBUF
        CALL BC_CVALID
        JP C,CTRINVALID
        LD A,(CTRLEN)
        LD B,A
        LD HL,CTRBUF
        LD DE,CTRFCB
        CALL BC_PFCB
        LD HL,CTRFCB+1
        LD B,8
        CALL CTVFIELD
        JP C,CTRINVALID
        LD A,C
        OR A
        JP Z,CTRINVALID
        LD B,3
        CALL CTVFIELD
        JP C,CTRINVALID
        LD HL,(CT_DCUR)
        LD DE,CTROLD
        LD BC,11
        LDIR
        LD HL,CTRFCB+1
        LD DE,(CT_DCUR)
        LD BC,11
        LDIR
        LD A,(CT_COUNT)
        LD (CTRLEFT),A
        LD HL,CT_TARGETS
        LD (CTRPTR),HL
CTRSCAN:
        LD HL,(CTRPTR)
        LD DE,(CT_DCUR)
        OR A
        SBC HL,DE
        JR Z,CTRNEXT
        LD HL,(CTRPTR)
        CALL BC_WCMP
        JR Z,CTRCONFL
CTRNEXT:
        LD HL,(CTRPTR)
        LD DE,11
        ADD HL,DE
        LD (CTRPTR),HL
        LD HL,CTRLEFT
        DEC (HL)
        JR NZ,CTRSCAN
        CALL CTSRCTST
        JR Z,CTRCONFL
        LD HL,CTRFCB
        LD DE,BC_NEWFCB
        LD BC,36
        LDIR
        CALL BC_CSELD
        LD DE,BC_NEWFCB
        LD C,15
        CALL BDOS
        CP 0FFH
        JP Z,BC_CMAKE
        JP CTEXIST
CTRCONFL:
        LD HL,CTROLD
        LD DE,(CT_DCUR)
        LD BC,11
        LDIR
        LD DE,CT_MAPMSG
        CALL BC_PRINT
        JP CTRENAME
CTRINVALID:
        LD DE,CTRERROR
        CALL BC_PRINT
        JP CTRENAME
CTRASK: DB 'New Name: $'
CTRERROR: DB 'Invalid filename.',13,10,'$'
CTRERASE: DB 8,' ',8,'$'
CTRLEN: DB 0
CTROVER: DB 0
CTRCHAR: DB 0
CTRLEFT: DB 0
CTRPTR: DW 0
CTRBUF: DS 126
CTRFCB: DS 36
CTROLD: DS 11
