SELECTUSER:
        LD E,(IX+FU)
        LD C,32
        JP SERVICE
FCBDE:
        PUSH IX
        POP DE
        RET
OPENFILE:
        CALL SELECTUSER
        CALL FCBDE
        LD C,15
        CALL SERVICE
        CP 255
        JR Z,OPENBAD
        LD (IX+FO),1
        CALL FCBDE
        LD C,35
        CALL SERVICE
        ; Function 35 returns size in the FCB, not a defined accumulator value.
        LD A,(IX+33)
        LD (IX+FL),A
        LD A,(IX+34)
        LD (IX+FL+1),A
        LD A,(IX+35)
        LD (IX+FL+2),A
        PUSH IX
        POP HL
        LD DE,FL
        ADD HL,DE
        LD B,7
FILESHIFT:
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
        DJNZ FILESHIFT
        OR A
        RET
SIZEBAD:
        LD HL,READMSG
        JR FILEERROR
OPENBAD:
        LD HL,OPENMSG
FILEERROR:
        CALL TEXT
        LD L,(IX+FN)
        LD H,(IX+FN+1)
        CALL TEXT
        CALL LINE
        SCF
        RET
CLOSEFILE:
        LD A,(IX+FO)
        OR A
        RET Z
        CALL SELECTUSER
        CALL FCBDE
        LD C,16
        CALL SERVICE
        LD (IX+FO),0
        RET
; Range clamped before address addition. Never loop over absent/absent bytes.
RANGE:
        LD HL,START1
        LD DE,FILE1+FP
        CALL COPY32
        LD HL,START2
        LD DE,FILE2+FP
        CALL COPY32
        LD HL,START1
        CALL NZ32
        LD B,A
        LD HL,START2
        CALL NZ32
        OR B
        LD B,A
        LD A,(LENSET)
        OR B
        LD (RANGED),A
        LD HL,FILE1+FL
        LD DE,LEFT
        CALL COPY32
        LD HL,START1
        CALL SUB32
        JR NC,RANGE2
        EX DE,HL
        CALL ZERO32
RANGE2:
        LD HL,FILE2+FL
        LD DE,TEMP
        CALL COPY32
        LD HL,START2
        CALL SUB32
        JR NC,RANGEMAX
        EX DE,HL
        CALL ZERO32
RANGEMAX:
        LD HL,TEMP
        LD DE,LEFT
        CALL CMP32
        CALL NC,COPY32
        LD A,(LENSET)
        OR A
        JR Z,RANGECHECK
        LD HL,LENGTH
        LD DE,LEFT
        CALL CMP32
        CALL C,COPY32
RANGECHECK:
        LD HL,LEFT
        LD DE,TOTAL
        CALL COPY32
        CALL NZ32
        RET Z
        LD DE,TEMP
        CALL COPY32
        LD HL,TEMP
        CALL DEC32
        LD HL,START1
        LD DE,NVAL
        CALL COPY32
        LD HL,TEMP
        CALL ADD32
        RET C
        LD HL,START2
        CALL COPY32
        LD HL,TEMP
        CALL ADD32
        RET C
        LD A,(START1)
        LD B,A
        LD A,(WIDTH)
        DEC A
        AND B
        LD (SLOT),A
        OR A
        RET
; File access uses absolute 32-bit positions and caches one logical record.
GETBYTE:
        LD (IX+FA),0
        PUSH IX
        POP HL
        LD DE,FP
        ADD HL,DE
        PUSH IX
        POP DE
        PUSH HL
        LD HL,FL
        ADD HL,DE
        EX DE,HL
        POP HL
        CALL CMP32
        JR C,HASBYTE
        OR A
        RET
HASBYTE:
        LD A,(IX+FP)
        RLCA
        AND 1
        LD C,A
        LD L,(IX+FP+1)
        LD H,(IX+FP+2)
        LD A,(IX+FP+3)
        ADD HL,HL
        RLA
        LD (IX+35),A
        LD A,L
        OR C
        LD (IX+33),A
        LD (IX+34),H
        LD A,(IX+FC)
        OR A
        JR Z,READRECORD
        LD A,(IX+33)
        CP (IX+FK)
        JR NZ,READRECORD
        LD A,(IX+34)
        CP (IX+FK+1)
        JR NZ,READRECORD
        LD A,(IX+35)
        CP (IX+FK+2)
        JR Z,CACHEDBYTE
READRECORD:
        CALL SELECTUSER
        PUSH IX
        POP HL
        LD DE,FB
        ADD HL,DE
        EX DE,HL
        LD C,26
        CALL SERVICE
        CALL FCBDE
        LD C,33
        CALL SERVICE
        OR A
        JR NZ,GETERROR
        LD A,(IX+33)
        LD (IX+FK),A
        LD A,(IX+34)
        LD (IX+FK+1),A
        LD A,(IX+35)
        LD (IX+FK+2),A
        LD (IX+FC),1
CACHEDBYTE:
        LD A,(IX+FP)
        AND 127
        LD E,A
        LD D,0
        PUSH IX
        POP HL
        ADD HL,DE
        LD DE,FB
        ADD HL,DE
        LD A,(HL)
        LD (IX+FV),A
        LD (IX+FA),1
        OR A
        RET
GETERROR:
        SCF
        RET
