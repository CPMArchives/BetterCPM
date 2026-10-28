; Rewind and fully fingerprint every scan, including stored text padding.
; No consumer writes a planned record until SCANPATCH authenticates this pass.
SCANPATCH:
        LD IX,PATFILE
        CALL FILESIZE
        CALL REWIND
        CALL CINIT
        XOR A
        LD (EOFCHAR),A
        LD (CRSEEN),A
        LD (SEENIN),A
        LD (SEENOUT),A
        LD HL,LINENO
        CALL ZERO32
        LD A,1
        LD (INSIDE),A
SCANNEXT:
        CALL POLL
        LD HL,LINENO
        CALL CHECKINC
        CALL READLINE
        JR C,SCANEND
        CALL PARSELINE
        JR SCANNEXT
SCANEND:
        CALL CFINISH
        LD A,(PHASE)
        OR A
        JR Z,SCANDONE
        LD HL,CVALUES
        LD DE,PATSIG
        LD B,16
SIGLOOP:
        LD A,(DE)
        CP (HL)
        JP NZ,CHANGEDERROR
        INC DE
        INC HL
        DJNZ SIGLOOP
SCANDONE:
        XOR A
        LD (INSIDE),A
        RET
PATGET:
        LD IX,PATFILE
        CALL GETBYTE
        JP C,READERROR
        LD A,(IX+FA)
        OR A
        JR Z,PATEOF
        LD A,(IX+FV)
        PUSH AF
        CALL CUPDATE
        LD HL,PATFILE+FP
        CALL CHECKINC
        POP AF
        OR A
        RET
PATEOF:
        SCF
        RET
READLINE:
        XOR A
        LD (LINELEN),A
RLNEXT:
        CALL PATGET
        JR C,RLEOF
        LD B,A
        LD A,(EOFCHAR)
        OR A
        JR Z,RLNORMAL
        LD A,B
        OR A
        JR Z,RLNEXT
        CP 26
        JP NZ,SYNTAXERROR
        JR RLNEXT
RLNORMAL:
        LD A,B
        CP 26
        JR NZ,RLTERM
        LD A,1
        LD (EOFCHAR),A
        JR RLNEXT
RLTERM:
        CP 10
        JR NZ,RLCR
        LD A,(CRSEEN)
        OR A
        JR Z,RLDONE
        XOR A
        LD (CRSEEN),A
        JR RLNEXT
RLCR:
        XOR A
        LD (CRSEEN),A
        LD A,B
        CP 13
        JR NZ,RLSTORE
        LD A,1
        LD (CRSEEN),A
        JR RLDONE
RLSTORE:
        LD A,B
        CP 9
        JR Z,RLCHAR
        CP 32
        JP C,SYNTAXERROR
        CP 127
        JP NC,SYNTAXERROR
RLCHAR:
        LD A,(LINELEN)
        CP 255
        JP Z,SYNTAXERROR
        LD E,A
        LD D,0
        LD HL,LINEBUF
        ADD HL,DE
        LD A,B
        CALL UPPER
        LD (HL),A
        LD A,(LINELEN)
        INC A
        LD (LINELEN),A
        JR RLNEXT
RLEOF:
        LD A,(LINELEN)
        OR A
        JR NZ,RLDONE
        SCF
        RET
RLDONE:
        LD A,(LINELEN)
        LD E,A
        LD D,0
        LD HL,LINEBUF
        ADD HL,DE
        LD (HL),0
        OR A
        RET
; Strip comments and trailing spaces, then distinguish exact directive words.
PARSELINE:
        LD HL,LINEBUF
PLCOMMENT:
        LD A,(HL)
        OR A
        JR Z,PLTRIM
        CP ';'
        JR Z,PLTRIM
        INC HL
        JR PLCOMMENT
PLTRIM:
        LD (HL),0
        LD DE,LINEBUF
PLBACK:
        OR A
        SBC HL,DE
        ADD HL,DE
        JR Z,PLSTART
        DEC HL
        LD A,(HL)
        CP ' '
        JR Z,PLZERO
        CP 9
        JR NZ,PLSTART
PLZERO:
        LD (HL),0
        JR PLBACK
PLSTART:
        LD HL,LINEBUF
        CALL SKIPWHITE
        LD A,(HL)
        OR A
        RET Z
        LD (TOKEN),HL
        LD DE,DIRINPUT
        CALL WORDMATCH
        JR NZ,PLOUT
        LD A,(SEENIN)
        OR A
        JP NZ,SYNTAXERROR
        INC A
        LD (SEENIN),A
        LD IX,SCRATCH
        CALL PARSENAME
        LD A,(PHASE)
        OR A
        RET NZ
        LD A,(INOPT)
        OR A
        RET NZ
        LD HL,SCRATCH
        LD DE,INFILE
        CALL COPYDESC
        LD A,1
        LD (INSET),A
        RET
PLOUT:
        LD HL,(TOKEN)
        LD DE,DIROUTPUT
        CALL WORDMATCH
        JR NZ,PLPATCH
        LD A,(SEENOUT)
        OR A
        JP NZ,SYNTAXERROR
        INC A
        LD (SEENOUT),A
        LD IX,SCRATCH
        CALL PARSENAME
        LD A,(PHASE)
        OR A
        RET NZ
        LD A,(OUTOPT)
        OR A
        RET NZ
        LD HL,SCRATCH
        LD DE,OUTFILE
        CALL COPYDESC
        LD A,1
        LD (OUTSET),A
        RET
PLPATCH:
        LD HL,(TOKEN)
        CALL HEXOFFSET
        CALL SKIPWHITE
        LD A,(HL)
        CP ':'
        JP NZ,SYNTAXERROR
        INC HL
        LD DE,OLDBYTES
        XOR A
        LD (WHICH),A
        CALL SEQUENCE
        LD A,(SEQLEN)
        LD (OLDLEN),A
        LD A,(HL)
        CP '-'
        JP NZ,SYNTAXERROR
        INC HL
        LD A,(HL)
        CP '>'
        JP NZ,SYNTAXERROR
        INC HL
        LD DE,NEWBYTES
        LD A,1
        LD (WHICH),A
        CALL SEQUENCE
        LD A,(SEQLEN)
        LD (NEWLEN),A
        LD B,A
        LD A,(OLDLEN)
        CP B
        JP C,SYNTAXERROR
        LD A,(HL)
        OR A
        JP NZ,SYNTAXERROR
        LD A,(PHASE)
        OR A
        JR NZ,PLAPPLY
        LD HL,NINST
        JP CHECKINC
PLAPPLY:
        LD HL,OFFSET
        LD DE,ENDOFF
        CALL COPY32
        LD A,(OLDLEN)
        LD HL,ENDOFF
PLEND:
        CALL CHECKINC
        DEC A
        JR NZ,PLEND
        LD HL,ENDOFF
        LD DE,INFILE+FL
        CALL CMP32
        JP C,APPLY
        JP Z,APPLY
        JP RANGEERROR
SKIPWHITE:
        LD A,(HL)
        CP ' '
        JR Z,SWNEXT
        CP 9
        RET NZ
SWNEXT:
        INC HL
        JR SKIPWHITE
WORDMATCH:
        CALL PREFIX
        RET NZ
        LD A,(HL)
        CP ' '
        JR Z,WMYES
        CP 9
        JR Z,WMYES
        LD A,1
        OR A
        RET
WMYES:
        CALL SKIPWHITE
        XOR A
        RET
HEXOFFSET:
        PUSH HL
        LD HL,OFFSET
        CALL ZERO32
        POP HL
        LD B,0
HONEXT:
        LD A,(HL)
        CALL NIBBLE
        JR C,HOEND
        LD C,A
        INC B
        LD A,B
        CP 9
        JP NC,RANGEERROR
        PUSH HL
        PUSH BC
        LD HL,OFFSET
        LD B,4
HOSHIFT:
        SLA (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        INC HL
        RL (HL)
        LD HL,OFFSET
        DJNZ HOSHIFT
        POP BC
        LD A,(OFFSET)
        OR C
        LD (OFFSET),A
        POP HL
        INC HL
        JR HONEXT
HOEND:
        LD A,B
        OR A
        JP Z,SYNTAXERROR
        LD A,(HL)
        CP 'H'
        RET NZ
        INC HL
        RET
NIBBLE:
        SUB '0'
        RET C
        CP 10
        JR C,NIBOK
        SUB 7
        CP 10
        JR C,NIBBAD
        CP 16
        JR NC,NIBBAD
NIBOK:
        OR A
        RET
NIBBAD:
        SCF
        RET
SEQUENCE:
        LD (SEQDEST),DE
        XOR A
        LD (SEQLEN),A
SQNEXT:
        CALL SKIPWHITE
        LD A,(HL)
        OR A
        JR Z,SQEND
        CP '-'
        JR Z,SQEND
        CALL NIBBLE
        JP C,SYNTAXERROR
        RLCA
        RLCA
        RLCA
        RLCA
        LD C,A
        INC HL
        LD A,(HL)
        CALL NIBBLE
        JP C,SYNTAXERROR
        OR C
        LD DE,(SEQDEST)
        LD (DE),A
        INC DE
        LD (SEQDEST),DE
        LD A,(SEQLEN)
        INC A
        CP 85
        JP NC,SYNTAXERROR
        LD (SEQLEN),A
        INC HL
        LD A,(HL)
        OR A
        JR Z,SQEND
        CP '-'
        JR Z,SQEND
        CP ' '
        JR Z,SQNEXT
        CP 9
        JP NZ,SYNTAXERROR
        JR SQNEXT
SQEND:
        LD A,(SEQLEN)
        OR A
        JP Z,SYNTAXERROR
        RET
; Increment a 32-bit count without silent wrap. Preserve A and pointers.
CHECKINC:
        PUSH AF
        CALL INC32
        CALL NZ32
        JP Z,RANGEERROR
        POP AF
        RET
