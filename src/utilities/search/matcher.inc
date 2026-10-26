; SEARCH 1.0 streaming core, no BDOS or console dependencies.
; Include once with state.inc in the same linked consumer.
;
; SCONFIG: HL literal pattern, B byte length (1..127), C flags:
;   bit 0 /NOHEX, bit 1 /NOTEXT, bit 2 /NOCASE. Other bits invalid.
;   Preserves source bytes. Carry/A error: 1 flags/no mode, 2 empty,
;   3 enabled TEXT too long, 4 invalid HEX-only pattern. Success A=0.
;   Every failure disables both matchers. Calls SRESET on success.
; SRESET: clear per-file history, position, line state and error latch;
;   retain configured patterns. Call between files, never between records.
; SFEED: A next byte; carry clear on success, A=result bitmask
;   (1 TEXT, 2 HEX). Both may be set. SPOS = bytes consumed.
;   STSTART/SHSTART = zero-based start offsets for set result bits;
;   STLINE = one-based line containing TEXT match's first byte.
;   Results for unset bits are unspecified. Every overlapping start counts.
;   Carry set/A=5 if position or line exceeds 32 bits. Error remains latched
;   until reset. Caller must mark coverage incomplete, never wrap totals.
; All entries may clobber AF/BC/DE/HL; IX/IY unchanged. Non-reentrant.
; No byte-value sentinel: NUL, 1Ah and all high-bit bytes are ordinary data.
SCONFIG:
        XOR A
        LD (STLEN),A
        LD (SHLEN),A
        LD A,C
        LD (SFLAGS),A
        AND 248
        JP NZ,SBADFLAG
        LD A,C
        AND 3
        CP 3
        JP Z,SBADFLAG
        LD A,B
        OR A
        JP Z,SEMPTY
        CP 128
        JP NC,SBADFLAG
        LD (SRAWLEN),A
        LD (SRAWPTR),HL
        LD A,C
        AND 2
        JR NZ,SCFGHEX
        LD A,(SRAWLEN)
        CP 65
        JP NC,STOOLONG
        LD (STLEN),A
        LD DE,STPAT
SCOPYTXT:
        LD A,(HL)
        CALL SFOLD
        LD (DE),A
        INC HL
        INC DE
        DJNZ SCOPYTXT
SCFGHEX:
        LD A,(SFLAGS)
        AND 1
        JR NZ,SCFGOK
        LD HL,(SRAWPTR)
        LD A,(SRAWLEN)
        LD B,A
        LD DE,SHPAT
        LD C,0
        XOR A
        LD (SFORMAT),A
SPAIR:
        LD A,(HL)
        CALL SNIBBLE
        JR C,SBADHEX
        RLCA
        RLCA
        RLCA
        RLCA
        LD (SHIGH),A
        INC HL
        DEC B
        JR Z,SBADHEX
        LD A,(HL)
        CALL SNIBBLE
        JR C,SBADHEX
        PUSH HL
        LD HL,SHIGH
        OR (HL)
        POP HL
        LD (DE),A
        INC DE
        INC C
        INC HL
        DEC B
        JR Z,SHDONE
        LD A,(HL)
        CP ' '
        JR Z,SSPACED
        LD A,(SFORMAT)
        CP 1
        JR Z,SBADHEX
        LD A,2
        LD (SFORMAT),A
        JR SPAIR
SSPACED:
        LD A,(SFORMAT)
        CP 2
        JR Z,SBADHEX
        LD A,1
        LD (SFORMAT),A
SHSPACE:
        INC HL
        DEC B
        JR Z,SBADHEX
        LD A,(HL)
        CP ' '
        JR Z,SHSPACE
        JR SPAIR
SHDONE:
        LD A,C
        LD (SHLEN),A
SCFGOK:
        CALL SRESET
        XOR A
        RET
SBADHEX:
        LD A,(STLEN)
        OR A
        JR NZ,SCFGOK
        LD A,4
        JR SCFGFAIL
SBADFLAG:
        LD A,1
        JR SCFGFAIL
SEMPTY:
        LD A,2
        JR SCFGFAIL
STOOLONG:
        LD A,3
SCFGFAIL:
        PUSH AF
        XOR A
        LD (STLEN),A
        LD (SHLEN),A
        POP AF
        SCF
        RET
SNIBBLE:
        CP '0'
        JR C,SNOTHEX
        CP '9'+1
        JR C,SDIGIT
        AND 223
        CP 'A'
        JR C,SNOTHEX
        CP 'F'+1
        JR NC,SNOTHEX
        SUB 'A'-10
        OR A
        RET
SDIGIT:
        SUB '0'
        RET
SNOTHEX:
        SCF
        RET
SFOLD:
        PUSH BC
        LD B,A
        LD A,(SFLAGS)
        AND 4
        LD A,B
        JR Z,SFOLDDON
        CP 'a'
        JR C,SFOLDDON
        CP 'z'+1
        JR NC,SFOLDDON
        SUB 32
SFOLDDON:
        POP BC
        RET
SRESET:
        LD HL,SFSTATE
        LD DE,SFSTATE+1
        LD BC,SFEND-SFSTATE-1
        LD (HL),0
        LDIR
        LD A,1
        LD (SLINE),A
        RET
SFEED:
        LD (SBYTE),A
        LD A,(SERROR)
        OR A
        JP NZ,SOVFLOW
        ; Refuse an unrepresentable next position before accepting the byte.
        LD HL,SPOS
        LD B,4
SCHKPOS:
        LD A,(HL)
        CP 255
        JR NZ,SPOSOK
        INC HL
        DJNZ SCHKPOS
        JP SOVFLOW
SPOSOK:
        XOR A
        LD (SRESULT),A
        LD A,(SCR)
        OR A
        JR Z,SSTORE
        LD A,(SBYTE)
        CP 10
        JR Z,SSTORE
        LD HL,SLINE
        CALL SINC32
        JP C,SOVFLOW
SSTORE:
        ; Ring history stores source bytes and their starting-line attribution.
        LD A,(SNEXT)
        LD E,A
        LD D,0
        LD HL,SRING
        ADD HL,DE
        LD A,(SBYTE)
        LD (HL),A
        LD L,E
        LD H,0
        ADD HL,HL
        ADD HL,HL
        LD DE,SLRING
        ADD HL,DE
        EX DE,HL
        LD HL,SLINE
        LD BC,4
        LDIR
        LD A,(SNEXT)
        INC A
        AND 63
        LD (SNEXT),A
        LD A,(SSEEN)
        CP 64
        JR Z,SSEENOK
        INC A
        LD (SSEEN),A
SSEENOK:
        LD HL,SPOS
        CALL SINC32
        ; Track CR lazily so CR/LF bytes both belong to the preceding line.
        LD A,(SBYTE)
        CP 13
        LD A,1
        JR Z,SSETCR
        XOR A
SSETCR:
        LD (SCR),A
        LD A,(SBYTE)
        CP 10
        JR NZ,SMTEXT
        LD HL,SLINE
        CALL SINC32
        JP C,SOVFLOW
SMTEXT:
        LD A,(STLEN)
        OR A
        JR Z,SMHEX
        LD DE,STPAT
        LD C,1
        CALL SCOMPARE
        JR NZ,SMHEX
        LD A,1
        LD (SRESULT),A
        LD A,(STLEN)
        LD DE,STSTART
        CALL SSTART
        LD A,(SMINDEX)
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        LD DE,SLRING
        ADD HL,DE
        LD DE,STLINE
        LD BC,4
        LDIR
SMHEX:
        LD A,(SHLEN)
        OR A
        JR Z,SFDONE
        LD DE,SHPAT
        LD C,0
        CALL SCOMPARE
        JR NZ,SFDONE
        LD A,(SRESULT)
        OR 2
        LD (SRESULT),A
        LD A,(SHLEN)
        LD DE,SHSTART
        CALL SSTART
SFDONE:
        LD A,(SRESULT)
        OR A
        RET
SOVFLOW:
        LD A,5
        LD (SERROR),A
        SCF
        RET
; A length, DE pattern, C=1 folds ring bytes; Z iff full suffix matches.
SCOMPARE:
        LD B,A
        LD A,(SSEEN)
        CP B
        JR C,SNOMATCH
        LD A,(SNEXT)
        SUB B
        AND 63
        LD (SMINDEX),A
        LD HL,SRING
        ADD A,L
        LD L,A
        JR NC,SRADDR
        INC H
SRADDR:
        LD A,C
        OR A
        LD A,(HL)
        CALL NZ,SFOLD
        PUSH HL
        LD H,A
        LD A,(DE)
        CP H
        POP HL
        RET NZ
        INC DE
        LD A,L
        SUB SRING % 256
        INC A
        AND 63
        PUSH DE
        LD DE,SRING
        LD L,A
        LD H,0
        ADD HL,DE
        POP DE
        DJNZ SRADDR
        XOR A
        RET
SNOMATCH:
        LD A,1
        OR A
        RET
; DE = position - A, all four bytes. Position has already advanced.
SSTART:
        LD B,A
        LD HL,SPOS
        LD C,4
        OR A
SSUBST:
        LD A,(HL)
        SBC A,B
        LD (DE),A
        INC HL
        INC DE
        LD B,0
        DEC C
        JR NZ,SSUBST
        RET
; Increment little-endian uint32; carry iff overflow.
SINC32:
        LD B,4
SINCLOOP:
        INC (HL)
        JR NZ,SINCOK
        INC HL
        DJNZ SINCLOOP
        SCF
        RET
SINCOK:
        OR A
        RET
