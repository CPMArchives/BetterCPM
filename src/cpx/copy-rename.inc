; Transient collision rename. Candidate names remain separate until validated.
CTRENAME:
        LD DE,CTRASK
        CALL BC_PRINT
        LD A,126
        CALL UA_INIT
CTRREAD:
        LD E,0FFH
        LD C,6
        CALL BDOS
        OR A
        JR Z,CTRREAD
        CP 10
        JR NZ,CTRCASE
        LD A,13                    ; COPY has always submitted on CR or LF
CTRCASE:
        CALL UC_UPPER
        LD (CTRCHAR),A
        CALL CU_EDIT
        CP UI_ABORT
        JP Z,CTABORT
        CP UI_SEND
        JP Z,CTRLINE
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
