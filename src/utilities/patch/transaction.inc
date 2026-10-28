; Search preserves private buffers and reads protection flags from directory DMA.
EXISTS:
        CALL SELECTUSER
        LD DE,DIRBUF
        LD C,26
        CALL SERVICE
        CALL FCBDE
        LD C,17
        CALL SERVICE
        CP 255
        RET
COLLISION:
        LD HL,INFILE
        LD DE,OUTFILE
        CALL SAMEFILE
        JP Z,IDENTERROR
        LD HL,PATFILE
        CALL SAMEFILE
        JP Z,IDENTERROR
        LD IX,OUTFILE
        CALL EXISTS
        JR NZ,COLLFOUND
        XOR A
        LD (OUTEXIST),A
        RET
COLLFOUND:
        PUSH AF
        LD A,1
        LD (OUTEXIST),A
        POP AF
        CALL CHECKPROTECT
        JR COLLPROMPT
CHECKPROTECT:
        ; Function 17 returns an entry slot 0..3 in the 128-byte DMA.
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD E,A
        LD D,0
        LD HL,DIRBUF+9
        ADD HL,DE
        LD A,(HL)
        INC HL
        OR (HL)
        AND 128
        RET Z
        LD HL,PROTMSG
        JP FAIL
COLLPROMPT:
        CALL PRINTFILE
        LD HL,COLLMSG
        CALL TEXT
        CALL KEY
        PUSH AF
        CALL LINE
        POP AF
        CP 'Y'
        RET Z
        CP '?'
        JR Z,COLLHELP
        CP 'R'
        JR Z,COLLRENAME
        CP 'N'
        JP Z,CANCEL
        CP 13
        JP Z,CANCEL
        JR COLLPROMPT
COLLHELP:
        LD HL,PROMHELP
        CALL TEXT
        CALL LINE
        JR COLLPROMPT
COLLRENAME:
        LD HL,RENAMEMSG
        CALL TEXT
        LD HL,LINEBUF
        LD B,0
RENAMEKEY:
        CALL KEY
        CP 13
        JR Z,RENAMEDONE
        CP 8
        JR Z,RENAMEBACK
        CP 127
        JR Z,RENAMEBACK
        CP 32
        JR C,RENAMEKEY
        LD C,A
        LD A,B
        CP 31
        JR NC,RENAMEKEY
        LD A,C
        CALL PUT
        LD (HL),A
        INC HL
        INC B
        JR RENAMEKEY
RENAMEBACK:
        LD A,B
        OR A
        JR Z,RENAMEKEY
        DEC HL
        DEC B
        LD A,8
        CALL PUT
        LD A,' '
        CALL PUT
        LD A,8
        CALL PUT
        JR RENAMEKEY
RENAMEDONE:
        LD (HL),0
        CALL LINE
        LD HL,LINEBUF
        LD IX,OUTFILE
        CALL PARSENAME
        JP COLLISION
; IX destination descriptor, HL requested output. Allocate PATnnnnn.TMP/.BAK.
; Never reuse a real file, or the input/patch/output identities.
ALLOCATE:
        LD (ALLOCPTR),IX
        PUSH IX
        POP DE
        CALL COPYDESC
        LD HL,0
        LD (SLOTNUM),HL
ALLOCNEXT:
        LD IX,(ALLOCPTR)
        PUSH IX
        POP HL
        LD BC,184
        CALL ZERO
        LD A,(OUTFILE)
        LD (IX+0),A
        LD A,(OUTFILE+FU)
        LD (IX+FU),A
        LD (IX+1),'P'
        LD (IX+2),'A'
        LD (IX+3),'T'
        LD (IX+9),'T'
        LD (IX+10),'M'
        LD (IX+11),'P'
        PUSH IX
        POP HL
        LD DE,BACKUP
        OR A
        SBC HL,DE
        JR NZ,ALLOCTMP
        LD (IX+9),'B'
        LD (IX+10),'A'
        LD (IX+11),'K'
ALLOCTMP:
        ; Five hex digits: 00000..0FFFF. No 8-bit quotient truncation.
        LD (IX+4),'0'
        LD HL,(SLOTNUM)
        LD A,H
        RRCA
        RRCA
        RRCA
        RRCA
        CALL ALLOCHEX
        LD (IX+5),A
        LD A,H
        CALL ALLOCHEX
        LD (IX+6),A
        LD A,L
        RRCA
        RRCA
        RRCA
        RRCA
        CALL ALLOCHEX
        LD (IX+7),A
        LD A,L
        CALL ALLOCHEX
        LD (IX+8),A
        PUSH IX
        POP HL
        LD DE,INFILE
        CALL SAMEFILE
        JR Z,ALLOCSKIP
        LD DE,PATFILE
        CALL SAMEFILE
        JR Z,ALLOCSKIP
        LD DE,OUTFILE
        CALL SAMEFILE
        JR Z,ALLOCSKIP
        CALL EXISTS
        RET Z
ALLOCSKIP:
        LD HL,(SLOTNUM)
        INC HL
        LD (SLOTNUM),HL
        LD A,H
        OR L
        JP NZ,ALLOCNEXT
        JP WRITEERROR
ALLOCHEX:
        AND 15
        ADD A,'0'
        CP '9'+1
        RET C
        ADD A,7
        RET
; IX source, DE destination. Both identities must be on the same DU.
RENAMEFILE:
        LD (RENDEST),DE
        CALL SELECTUSER
        LD HL,RENBUF
        LD BC,36
        CALL ZERO
        PUSH IX
        POP HL
        LD DE,RENBUF
        LD BC,12
        LDIR
        LD HL,(RENDEST)
        LD DE,RENBUF+16
        LD BC,12
        LDIR
        LD DE,RENBUF
        LD C,23
        CALL SERVICE
        CP 255
        RET
INSTALL:
        ; Recheck collisions/protection after all I/O, retaining prior approval.
        LD IX,OUTFILE
        CALL EXISTS
        JR Z,INSTALLNEW
        PUSH AF
        LD A,(OUTEXIST)
        OR A
        JP Z,CHANGEDERROR
        POP AF
        CALL CHECKPROTECT
        LD IX,BACKUP
        LD HL,OUTFILE
        CALL ALLOCATE
        LD IX,OUTFILE
        LD DE,BACKUP
        CALL RENAMEFILE
        JR Z,INSTALLFAIL
        LD A,1
        LD (BACKED),A
INSTALLNEW:
        LD IX,STAGE
        LD DE,OUTFILE
        CALL RENAMEFILE
        JR Z,INSTALLRESTORE
        XOR A
        LD (STAGED),A
        LD A,(BACKED)
        OR A
        RET Z
        LD IX,BACKUP
        CALL DELETEFILE
        RET NZ
        LD HL,BAKWARN
        CALL TEXT
        CALL PRINTFILE
        JP LINE
INSTALLRESTORE:
        LD A,(BACKED)
        OR A
        JR Z,INSTALLFAIL
        LD IX,BACKUP
        LD DE,OUTFILE
        CALL RENAMEFILE
        JR NZ,INSTALLFAIL
        ; Retain BOTH known recovery files if rollback failed.
        XOR A
        LD (STAGED),A
        LD HL,RESTOREERR
        CALL TEXT
        LD IX,BACKUP
        CALL PRINTFILE
        CALL LINE
        LD HL,STATEREM
        CALL TEXT
        LD IX,STAGE
        CALL PRINTFILE
        CALL LINE
INSTALLFAIL:
        LD HL,RENAMEERR
        JP FAIL
DIRBUF: DS 128
