; Each pass reconstructs the complete result, one stored record at a time.
PROCESS:
        LD IX,INFILE
        CALL REWIND
        LD HL,RECORD
        CALL ZERO32
        LD A,(PHASE)
        CP 1
        JR NZ,PRNEXT
        LD HL,NWRITE
        CALL ZERO32
        LD HL,NCHANGE
        CALL ZERO32
PRNEXT:
        CALL POLL
        LD HL,RECORD
        LD DE,INFILE+FL
        CALL CMP32
        JP NC,PRDONE
        LD DE,INFILE+FP
        CALL COPY32
        LD IX,INFILE
        CALL GETBYTE
        JP C,READERROR
        LD A,(INFILE+FA)
        OR A
        JP Z,READERROR
        LD HL,INFILE+FB
        LD DE,EXPECTED
        LD BC,128
        LDIR
        LD HL,WRITEMAP
        LD BC,128
        CALL ZERO
        LD HL,RECORD
        LD DE,RECLIMIT
        CALL COPY32
        LD A,128
PRLIMIT:
        LD HL,RECLIMIT
        CALL CHECKINC
        DEC A
        JR NZ,PRLIMIT
        CALL SCANPATCH
        LD A,(PHASE)
        CP 1
        JR Z,PRADVANCE
        CP 3
        JR Z,PRVERIFY
        LD IX,STAGE
        CALL SELECTUSER
        LD DE,EXPECTED
        LD C,26
        CALL SERVICE
        CALL FCBDE
        LD C,21
        CALL SERVICE
        OR A
        JP NZ,WRITEERROR
        JR PRADVANCE
PRVERIFY:
        LD HL,RECORD
        LD DE,STAGE+FP
        CALL COPY32
        LD IX,STAGE
        CALL GETBYTE
        JP C,READERROR
        LD A,(STAGE+FA)
        OR A
        JP Z,VERIFYERROR
        LD HL,EXPECTED
        LD DE,STAGE+FB
        LD B,128
PRCOMPARE:
        LD A,(DE)
        CP (HL)
        JP NZ,VERIFYERROR
        INC DE
        INC HL
        DJNZ PRCOMPARE
PRADVANCE:
        LD HL,RECLIMIT
        LD DE,RECORD
        CALL COPY32
        JP PRNEXT
PRDONE:
        CALL CHECKINPUT
        ; An empty input still needs range checking and patch consistency.
        LD HL,INFILE+FL
        CALL NZ32
        CALL Z,SCANPATCH
        LD A,(PHASE)
        CP 3
        RET NZ
        LD HL,INFILE+FL
        LD DE,STAGE+FL
        CALL CMP32
        JP NZ,VERIFYERROR
        RET
; Range validation is global. Byte checks use original INFILE+FB, never EXPECTED.
APPLY:
        LD HL,OFFSET
        LD DE,BYTEPOS
        CALL COPY32
        XOR A
        LD (INDEX),A
        LD (BADLINE),A
APNEXT:
        LD HL,BYTEPOS
        LD DE,RECORD
        CALL CMP32
        JR C,APADVANCE
        LD DE,RECLIMIT
        CALL CMP32
        JR NC,APADVANCE
        LD HL,BYTEPOS
        LD DE,WORKPOS
        CALL COPY32
        LD HL,RECORD
        CALL SUB32
        LD A,(WORKPOS)
        LD E,A
        LD D,0
        LD HL,INFILE+FB
        ADD HL,DE
        LD A,(HL)
        LD (FOUND),A
        LD A,(INDEX)
        LD E,A
        LD HL,OLDBYTES
        ADD HL,DE
        LD A,(FOUND)
        CP (HL)
        CALL NZ,MISMATCH
        LD A,(INDEX)
        LD B,A
        LD A,(NEWLEN)
        CP B
        JR Z,APADVANCE
        JR C,APADVANCE
        LD A,(WORKPOS)
        LD E,A
        LD HL,WRITEMAP
        ADD HL,DE
        LD A,(HL)
        OR A
        JP NZ,OVERLAP
        LD (HL),1
        LD HL,EXPECTED
        ADD HL,DE
        PUSH HL
        LD A,(INDEX)
        LD E,A
        LD HL,NEWBYTES
        ADD HL,DE
        LD A,(HL)
        POP HL
        LD (HL),A
        LD B,A
        LD A,(PHASE)
        CP 1
        JR NZ,APADVANCE
        LD HL,NWRITE
        CALL CHECKINC
        LD A,(FOUND)
        CP B
        JR Z,APADVANCE
        LD HL,NCHANGE
        CALL CHECKINC
APADVANCE:
        LD HL,BYTEPOS
        CALL CHECKINC
        LD A,(INDEX)
        INC A
        LD (INDEX),A
        LD B,A
        LD A,(OLDLEN)
        CP B
        JP NZ,APNEXT
        LD A,(PHASE)
        CP 1
        RET NZ
        LD A,(VERBOSE)
        OR A
        RET Z
        ; Print a record's validation result only if its verification range
        ; intersects this record. Long contexts may produce several checks.
        LD HL,OFFSET
        LD DE,RECLIMIT
        CALL CMP32
        RET NC
        LD HL,RECORD
        LD DE,ENDOFF
        CALL CMP32
        RET NC
        CALL LOCATION
        LD HL,LINEBUF
        CALL TEXT
        LD A,(BADLINE)
        OR A
        JR NZ,APBADPRINT
        LD HL,OKMSG
        CALL TEXT
APBADPRINT:
        CALL LINE
        RET
MISMATCH:
        LD A,(HL)
        LD (WANTED),A
        LD A,1
        LD (BADVALID),A
        LD (BADLINE),A
        LD HL,MISMSG
        CALL TEXT
        LD HL,BYTEPOS
        CALL HEX32
        LD HL,ACTMSG
        CALL TEXT
        LD A,(WANTED)
        CALL HEX8
        LD HL,FOUNDM
        CALL TEXT
        LD A,(FOUND)
        CALL HEX8
        CALL LINE
        CALL LOCATION
        LD A,(PHASE)
        CP 1
        JP NZ,VALIDERROR
        LD A,(VERBOSE)
        OR A
        JP Z,VALIDERROR
        RET
OVERLAP:
        LD HL,OVERMSG
        JP FAIL
VERIFYERROR:
        LD HL,CHUNKMSG
        JP FAIL
WRITEERROR:
        LD HL,WRITEMSG
        JP FAIL
READERROR:
        LD HL,READMSG
        CALL TEXT
        CALL PRINTFILE
        CALL LINE
        LD HL,VALIDMSG
        JP FAIL
SELECTUSER:
        LD E,(IX+FU)
        LD C,32
        JP SERVICE
FCBDE:
        PUSH IX
        POP DE
        RET
REWIND:
        PUSH IX
        POP HL
        LD DE,FP
        ADD HL,DE
        CALL ZERO32
        LD (IX+FC),0
        RET
OPENFILE:
        CALL SELECTUSER
        CALL FCBDE
        LD C,15
        CALL SERVICE
        CP 255
        JR NZ,OPENOK
        LD HL,OPENMSG
        CALL TEXT
        CALL PRINTFILE
        CALL LINE
        JP VALIDERROR
OPENOK:
        LD (IX+FO),1
        CALL FILESIZE
        JP REWIND
FILESIZE:
        CALL SELECTUSER
        CALL FCBDE
        LD C,35
        CALL SERVICE
        LD A,(IX+33)
        LD (IX+FL),A
        LD A,(IX+34)
        LD (IX+FL+1),A
        LD A,(IX+35)
        LD (IX+FL+2),A
        LD (IX+FL+3),0
        PUSH IX
        POP HL
        LD DE,FL
        ADD HL,DE
        LD B,7
FSSHIFT:
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
        DJNZ FSSHIFT
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
CLOSECHECK:
        CALL CLOSEFILE
        CP 255
        JP Z,WRITEERROR
        RET
MAKEFILE:
        CALL SELECTUSER
        CALL FCBDE
        LD C,22
        CALL SERVICE
        CP 255
        JP Z,WRITEERROR
        LD (IX+FO),1
        RET
DELETEFILE:
        CALL SELECTUSER
        CALL FCBDE
        LD C,19
        CALL SERVICE
        CP 255
        RET

; A fresh random-record fingerprint pass detects input size/content changes.
; Input and patch files must stay mounted and unmodified during the command.
INPUTSIGN:
        LD IX,INFILE
        CALL FILESIZE
        CALL REWIND
        CALL CINIT
ISNEXT:
        CALL POLL
        LD IX,INFILE
        CALL GETBYTE
        JP C,READERROR
        LD A,(IX+FA)
        OR A
        JR Z,ISDONE
        LD A,(IX+FV)
        CALL CUPDATE
        LD HL,INFILE+FP
        CALL CHECKINC
        JR ISNEXT
ISDONE:
        JP CFINISH
CHECKINPUT:
        CALL INPUTSIGN
        LD HL,CVALUES
        LD DE,INSIG
        LD B,16
CILOOP:
        LD A,(DE)
        CP (HL)
        JP NZ,CHANGEDERROR
        INC DE
        INC HL
        DJNZ CILOOP
        RET
