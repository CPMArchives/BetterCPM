SPACES:
        PUSH BC
        LD A,B
        OR A
        JR Z,SPACESEND
SPACESLOOP:
        LD A,' '
        CALL PUT
        DJNZ SPACESLOOP
SPACESEND:
        POP BC
        RET
LISTBYTE:
        LD A,(ALLSET)
        OR A
        JR NZ,LISTSHOW
        LD HL,(SHOWN)
        LD DE,(LIMIT)
        OR A
        SBC HL,DE
        RET NC
LISTSHOW:
        LD HL,FILE1+FP
        CALL HEX32
        LD B,2
        CALL SPACES
        LD HL,FILE2+FP
        CALL HEX32
        CALL SPACES
        LD IX,FILE1
        CALL LISTVALUE
        LD B,2
        CALL SPACES
        LD IX,FILE2
        CALL LISTVALUE
        LD HL,(SHOWN)
        INC HL
        LD (SHOWN),HL
        LD HL,DISPLAYED
        CALL INC32
        JP LINE
LISTVALUE:
        LD A,(IX+FA)
        OR A
        JR Z,LISTEOF
        LD A,(IX+FV)
        CALL HEX8
        LD B,11
        JP SPACES
LISTEOF:
        LD HL,EOFMSG
        JP TEXT
STAGEBYTE:
        LD A,(ROWACTIVE)
        OR A
        JR NZ,STAGECELL
        LD HL,ROW1
        LD DE,ROW1+1
        LD BC,31
        LD (HL),0
        LDIR
        LD HL,NVAL
        CALL ZERO32
        LD A,(SLOT)
        LD (NVAL),A
        LD HL,FILE1+FP
        LD DE,BASE1
        CALL COPY32
        LD HL,NVAL
        CALL SUB32
        LD HL,FILE2+FP
        LD DE,BASE2
        CALL COPY32
        LD HL,NVAL
        CALL SUB32
        LD A,0
        ADC A,0
        LD (NEGBASE),A
        LD A,1
        LD (ROWACTIVE),A
        XOR A
        LD (ROWDIFF),A
STAGECELL:
        LD A,(SLOT)
        LD E,A
        LD D,0
        LD HL,ROW1
        ADD HL,DE
        LD A,(FILE1+FV)
        LD (HL),A
        LD HL,VALID1
        ADD HL,DE
        LD A,(FILE1+FA)
        LD (HL),A
        LD HL,ROW2
        ADD HL,DE
        LD A,(FILE2+FV)
        LD (HL),A
        LD HL,VALID2
        ADD HL,DE
        LD A,(FILE2+FA)
        LD (HL),A
        LD A,(DIFF)
        LD B,A
        LD A,(ROWDIFF)
        OR B
        LD (ROWDIFF),A
        LD A,(SLOT)
        INC A
        LD (SLOT),A
        LD B,A
        LD A,(WIDTH)
        CP B
        RET NZ
        CALL RENDER
        XOR A
        LD (SLOT),A
        RET
RENDER:
        LD HL,BASE1
        CALL HEX32
        LD B,2
        CALL SPACES
        LD IX,FILE1
        LD HL,ROW1
        LD DE,VALID1
        CALL ROWFIELD
        LD A,(COMPACT)
        OR A
        JR NZ,MARKER
        LD B,1
        CALL SPACES
MARKER:
        LD A,(ROWDIFF)
        OR A
        JR Z,NOMARKER
        LD A,'<'
        CALL PUT
        LD A,'>'
        CALL PUT
        JR AFTERMARKER
NOMARKER:
        LD B,2
        CALL SPACES
AFTERMARKER:
        LD A,(COMPACT)
        OR A
        JR NZ,SECONDADDRESS
        LD B,1
        CALL SPACES
SECONDADDRESS:
        LD A,(NEGBASE)
        OR A
        JR Z,POSITIVEBASE
        LD HL,MINUSEIGHT
        CALL TEXT
        JR SECONDFIELD
POSITIVEBASE:
        LD HL,BASE2
        CALL HEX32
SECONDFIELD:
        LD B,2
        CALL SPACES
        LD IX,FILE2
        LD HL,ROW2
        LD DE,VALID2
        CALL ROWFIELD
        XOR A
        LD (ROWACTIVE),A
        JP LINE
; HL=bytes, DE=availability. Never overwrite a partially populated EOF row.
ROWFIELD:
        PUSH HL
        PUSH DE
        LD A,(WIDTH)
        LD B,A
        XOR A
FIELDANY:
        LD C,A
        LD A,(DE)
        OR C
        INC DE
        DJNZ FIELDANY
        POP DE
        POP HL
        OR A
        JR NZ,FIELDBYTES
        LD A,(IX+FE)
        OR A
        JR NZ,FIELDBYTES
        LD (IX+FE),1
        LD A,(COMPACT)
        OR A
        JR Z,FIELDEOFNORMAL
        LD A,'E'
        CALL PUT
        LD A,'O'
        CALL PUT
        LD A,'F'
        CALL PUT
        LD B,5
        JP SPACES
FIELDEOFNORMAL:
        LD HL,EOFMSG
        CALL TEXT
        LD B,10
        JP SPACES
FIELDBYTES:
        LD A,(WIDTH)
        LD B,A
FIELDLOOP:
        LD A,(DE)
        OR A
        JR Z,FIELDBLANK
        LD A,(HL)
        CALL HEX8
        JR FIELDNEXT
FIELDBLANK:
        PUSH BC
        LD B,2
        CALL SPACES
        POP BC
FIELDNEXT:
        INC HL
        INC DE
        DEC B
        RET Z
        LD A,(COMPACT)
        OR A
        JR NZ,FIELDLOOP
        LD A,' '
        CALL PUT
        JR FIELDLOOP
