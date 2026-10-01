; FDB VERSION-1 NATIVE READER FOUNDATION -- 01-Oct-2026
; Load DISK.FDB into FDFRAM, then validate its framing and whole-file CRC.
; FDBVALID remains separately callable for focused host-side qualification.

; Open DISK.FDB on the current drive, falling back to A:, and validate its
; framing before the transitional text-catalogue path reuses FDFRAM.
FDBLOAD:
        LD HL,FDBFCB+12
        LD DE,FDBFCB+13
        LD BC,23
        LD (HL),0
        LDIR
        LD DE,FDBFCB
        LD C,15
        CALL BDOS
        CP 0FFH
        JR NZ,FDBOPEN
        LD A,1
        LD (FDBFCB),A
        LD DE,FDBFCB
        LD C,15
        CALL BDOS
        CP 0FFH
        JP Z,FDBMISSING
FDBOPEN:
        LD HL,FDFRAM
FDBREAD:
        LD (FDBPOS),HL
        EX DE,HL
        LD C,26
        CALL BDOS
        LD DE,FDBFCB
        LD C,20
        CALL BDOS
        CP 1
        JR Z,FDBEOF
        OR A
        JP NZ,FDBFILEBAD
        LD HL,(FDBPOS)
        LD DE,128
        ADD HL,DE
        LD DE,FDFLIM
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JR C,FDBREAD
        JP FDBFILEBAD
FDBEOF: LD HL,(FDBPOS)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD (FDBLEN),HL
        LD DE,FDBFCB
        LD C,16
        CALL BDOS
        LD DE,80H
        LD C,26
        CALL BDOS
        CALL FDBVALID
        RET NC
FDBFILEBAD:
        LD DE,FDBFCB
        LD C,16
        CALL BDOS
        LD DE,80H
        LD C,26
        CALL BDOS
        LD HL,FDBBADMSG
        JP FATAL
FDBMISSING:
        LD HL,FDBNOMSG
        JP FATAL

FDBVALID:
        LD HL,(FDBLEN)
        LD A,H
        OR L
        JP Z,FDBBAD
        LD A,L
        AND 07FH
        JP NZ,FDBBAD                 ; complete CP/M records only
        LD HL,FDFRAM
        LD DE,FDBMAG
        LD B,4
FDBMAGLP:
        LD A,(DE)
        CP (HL)
        JP NZ,FDBBAD
        INC DE
        INC HL
        DJNZ FDBMAGLP
        LD A,(FDFRAM+4)
        CP 1
        JP NZ,FDBBAD                 ; unknown major version
        LD A,(FDFRAM+6)
        CP 16
        JP C,FDBBAD
        CP 129
        JP NC,FDBBAD
        LD (FDBHSIZE),A
        LD A,(FDFRAM+7)
        CP 64
        JP C,FDBBAD
        LD (FDBSTRIDE),A
        LD A,(FDFRAM+9)
        OR A
        JP NZ,FDBBAD                 ; CONFIG index is one byte
        LD A,(FDFRAM+8)
        LD (FCOUNT),A
        LD HL,(FDFRAM+10)
        LD DE,128
        OR A
        SBC HL,DE
        JP NZ,FDBBAD                 ; v1 descriptors begin at record one

; Reproduce pool = 128 + descriptor_count * descriptor_stride, rejecting wrap.
        LD A,(FDBSTRIDE)
        LD E,A
        LD D,0
        LD HL,128
        LD A,(FCOUNT)
        LD B,A
        OR A
        JR Z,FDBPOOLDONE
FDBPOOLLP:
        ADD HL,DE
        JP C,FDBBAD
        DJNZ FDBPOOLLP
FDBPOOLDONE:
        LD (FDBPOOL),HL
        LD DE,(FDFRAM+12)
        OR A
        SBC HL,DE
        JP NZ,FDBBAD
        LD HL,(FDBLEN)
        OR A
        SBC HL,DE
        JP C,FDBBAD                  ; pool must fall within the file

; Same-major header tails may carry optional data. Bytes after header_size up
; to the fixed first descriptor record remain reserved and therefore zero.
        LD A,(FDBHSIZE)
        LD L,A
        LD H,0
        LD DE,FDFRAM
        ADD HL,DE
        LD DE,FDFRAM+128
FDBRESLP:
        LD A,H
        CP D
        JR NZ,FDBRESBYTE
        LD A,L
        CP E
        JR Z,FDBCRC
FDBRESBYTE:
        LD A,(HL)
        OR A
        JP NZ,FDBBAD
        INC HL
        JR FDBRESLP

; CRC-16/CCITT-FALSE over the complete file, with stored CRC bytes zeroed.
FDBCRC: LD HL,(FDFRAM+14)
        LD (FDBEXPECT),HL
        XOR A
        LD (FDFRAM+14),A
        LD (FDFRAM+15),A
        LD HL,0FFFFH
        LD DE,FDFRAM
        LD BC,(FDBLEN)
FDBCRCBYTE:
        LD A,(DE)
        XOR H
        LD H,A
        PUSH BC
        LD B,8
FDBCRCBIT:
        ADD HL,HL
        JR NC,FDBCRCNEXT
        LD A,H
        XOR 010H
        LD H,A
        LD A,L
        XOR 021H
        LD L,A
FDBCRCNEXT:
        DJNZ FDBCRCBIT
        POP BC
        INC DE
        DEC BC
        LD A,B
        OR C
        JR NZ,FDBCRCBYTE
        PUSH HL
        LD HL,(FDBEXPECT)
        LD (FDFRAM+14),HL
        POP DE
        OR A
        SBC HL,DE
        JP NZ,FDBBAD
        CALL FDBDALL
        RET C
        OR A
        RET

; Validate the fixed prefix of every descriptor.  Required-extension semantics
; and binding construction are deliberately left to the next reader layer.
FDBDALL:
; Place the byte-ownership bitmap above the loaded catalogue. Its size is one
; bit per possible FDB byte; reject a catalogue that leaves no validation room.
        LD HL,(FDBLEN)
        LD DE,7
        ADD HL,DE
        RET C
        SRL H
        RR L
        SRL H
        RR L
        SRL H
        RR L
        LD (FDBOWNSIZE),HL
        EX DE,HL
        LD HL,FDFLIM
        OR A
        SBC HL,DE
        LD (FDBOWNBASE),HL
        LD HL,FDFRAM
        LD DE,(FDBLEN)
        ADD HL,DE
        LD DE,(FDBOWNBASE)
        OR A
        SBC HL,DE
        JR C,FDBOWNFIT
        JR Z,FDBOWNFIT
        SCF
        RET
FDBOWNFIT:
        LD HL,(FDBOWNBASE)
        LD DE,(FDBOWNBASE)
        INC DE
        LD BC,(FDBOWNSIZE)
        DEC BC
        LD (HL),0
        LDIR
        LD HL,FDBSUPPORT
        LD DE,FDBSUPPORT+1
        LD BC,31
        LD (HL),0FFH
        LDIR
        LD HL,(FDBPOOL)
        LD DE,FDFRAM
        ADD HL,DE
        LD (FDBHIGH),HL
        XOR A
        LD (FDBINDEX),A
FDBDALP:
        LD A,(FDBINDEX)
        LD B,A
        LD A,(FCOUNT)
        CP B
        JP Z,FDBDEND
        LD A,B
        CALL FDBDESC
        RET C
        PUSH HL
        CALL FDBID
        POP HL
        RET C
        PUSH HL
        LD DE,8
        ADD HL,DE
        CALL FDBDESCRIPTION
        POP HL
        RET C
        PUSH HL
        POP IX
        LD A,(IX+55)
        OR A
        SCF
        RET Z                           ; physical sector count
        CP (IX+59)
        SCF
        RET NZ                          ; duplicated count must agree
        LD A,(IX+56)
        CP 4
        JP NC,FDBDESCBAD
        LD A,(IX+57)
        OR A
        SCF
        RET Z                           ; cylinders must be nonzero
        LD A,(IX+58)
        AND 080H
        LD C,A
        LD A,(IX+62)
        OR (IX+63)
        JR Z,FDBNOEXT
        LD A,C
        OR A
        JP Z,FDBDESCBAD                 ; nonzero offset requires flag
        JR FDBIDS
FDBNOEXT:
        LD A,C
        OR A
        JP NZ,FDBDESCBAD                ; flag requires nonzero offset
FDBIDS: LD E,(IX+60)
        LD D,(IX+61)
        PUSH DE
        LD HL,(FDBPOOL)
        OR A
        EX DE,HL
        SBC HL,DE
        POP DE
        RET C                           ; list points before pool
        LD A,(IX+55)
        LD L,A
        LD H,0
        ADD HL,DE
        RET C
        PUSH HL                          ; end offset
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        POP HL
        JR C,FDBIDSGOOD
        JR Z,FDBIDSGOOD                 ; end may equal file length
        JP FDBDESCBAD
FDBIDSGOOD:
        PUSH HL                          ; end offset
        LD DE,FDFRAM
        ADD HL,DE
        EX DE,HL                         ; DE = end address
        POP HL                           ; discard numeric end
        LD L,(IX+60)
        LD H,(IX+61)
        PUSH DE
        LD DE,FDFRAM
        ADD HL,DE                        ; HL = sector-ID address
        POP DE
        PUSH HL
        PUSH DE
        LD B,(IX+55)
        CALL FDBIDUNIQUE
        POP DE
        POP HL
        RET C
        CALL FDBOBJADD
        RET C
        LD A,(IX+62)
        OR (IX+63)
        JR Z,FDBDESCOK
        LD L,(IX+62)
        LD H,(IX+63)
        LD DE,FDFRAM
        ADD HL,DE
        CALL FDBEXTENSIONS
        RET C
FDBDESCOK:
        LD A,(FDBINDEX)
        INC A
        LD (FDBINDEX),A
        JP FDBDALP

FDBDEND:
; The final referenced byte determines the sole permitted record-aligned size.
        LD HL,(FDBHIGH)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD DE,127
        ADD HL,DE
        RET C
        LD A,L
        AND 080H
        LD L,A
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        JP NZ,FDBDESCBAD
; Every nonzero pool byte must belong to one claimed object.
        LD HL,(FDBPOOL)
        LD DE,FDFRAM
        ADD HL,DE
        LD (FDBOBJPTR),HL
FDBOWNCHECK:
        LD HL,(FDBOBJPTR)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        JR Z,FDBOWNDONE
        LD HL,(FDBOBJPTR)
        LD A,(HL)
        OR A
        JR Z,FDBOWNNEXT
        CALL FDBOWNPTR
        AND (HL)
        SCF
        RET Z
FDBOWNNEXT:
        LD HL,(FDBOBJPTR)
        INC HL
        LD (FDBOBJPTR),HL
        JR FDBOWNCHECK
FDBOWNDONE:
        OR A
        RET

; Require every sector ID in [HL,HL+B) to be distinct.
FDBIDUNIQUE:
        LD A,B
        OR A
        RET Z
FIUOUT:
        LD A,(HL)
        PUSH HL
        PUSH BC
        INC HL
        DEC B
FIUIN:
        JR Z,FIUNXT
        CP (HL)
        JR Z,FIUBAD
        INC HL
        DJNZ FIUIN
FIUNXT:
        POP BC
        POP HL
        INC HL
        DJNZ FIUOUT
        OR A
        RET
FIUBAD:
        POP BC
        POP HL
        SCF
        RET

; Parse and validate one extension list beginning at HL, then own its complete
; byte interval. Unknown required kinds mark only this descriptor unsupported.
FDBEXTENSIONS:
        LD (FDBEXSTART),HL
        LD HL,FDBTYPES
        LD DE,FDBTYPES+1
        LD BC,15
        LD (HL),0
        LDIR
        LD HL,(FDBEXSTART)
FDBEXTLOOP:
        LD DE,2
        CALL FDBROOM
        RET C
        LD A,(HL)
        LD (FDBEXTYPE),A
        INC HL
        LD A,(HL)
        LD (FDBEXLEN),A
        INC HL
        LD A,(FDBEXTYPE)
        OR A
        JR NZ,FDBEXTNONZERO
        LD A,(FDBEXLEN)
        OR A
        SCF
        RET NZ
        EX DE,HL
        LD HL,(FDBEXSTART)
        CALL FDBOBJADD
        RET
FDBEXTNONZERO:
        CP 080H
        SCF
        RET Z
        AND 07FH
        PUSH HL
        LD DE,FDBTYPES
        CALL FDBBITPTR
        LD B,A
        AND (HL)
        JR NZ,FDBEXTDUP
        LD A,B
        OR (HL)
        LD (HL),A
        POP HL
        LD A,(FDBEXLEN)
        LD E,A
        LD D,0
        CALL FDBROOM
        RET C
        LD A,(FDBEXTYPE)
        AND 07FH
        CP 1
        JR Z,FDBEXTSIZE
        CP 2
        JR Z,FDBEXTTRACK
        LD A,(FDBEXTYPE)
        AND 080H
        CALL NZ,FDBMARKUNSUPPORTED
        JR FDBEXTADVANCE
FDBEXTDUP:
        POP HL
        SCF
        RET
FDBEXTSIZE:
        LD A,(FDBEXTYPE)
        CP 081H
        SCF
        RET NZ
        LD A,(FDBEXLEN)
        CP (IX+55)
        SCF
        RET NZ
        LD B,A
        LD C,0                           ; maximum size code
        PUSH HL
FESLP:
        LD A,(HL)
        CP 4
        JR NC,FESBAD
        CP C
        JR C,FESNXT
        LD C,A
FESNXT:
        INC HL
        DJNZ FESLP
        POP HL
        LD A,C
        CP (IX+56)
        SCF
        RET NZ
        JR FDBEXTADVANCE
FESBAD:
        POP HL
        SCF
        RET
FDBEXTTRACK:
        LD A,(FDBEXTYPE)
        CP 082H
        SCF
        RET NZ
        LD A,(FDBEXLEN)
        CP 1
        SCF
        RET NZ
        LD A,(HL)
        CP 1
        SCF
        RET NZ
FDBEXTADVANCE:
        LD A,(FDBEXLEN)
        LD E,A
        LD D,0
        ADD HL,DE
        JP FDBEXTLOOP

FDBMARKUNSUPPORTED:
        PUSH HL
        LD A,(FDBINDEX)
        LD DE,FDBSUPPORT
        CALL FDBBITPTR
        CPL
        AND (HL)
        LD (HL),A
        POP HL
        RET

; Carry if [HL,HL+DE) extends beyond the loaded file.
FDBROOM:
        PUSH HL
        ADD HL,DE
        JR C,FDBROOMBAD
        PUSH HL
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        POP HL
        JR C,FDBROOMGOOD
        JR Z,FDBROOMGOOD
FDBROOMBAD:
        POP HL
        SCF
        RET
FDBROOMGOOD:
        POP HL
        OR A
        RET

; Claim [HL,DE) in a bit-per-byte ownership map; carry on bounds or overlap.
FDBOBJADD:
        LD (FDBOBJPOS),HL
        LD (FDBOBJEND),DE
        OR A
        SBC HL,DE
        JR NC,FDBOBJBAD                  ; empty or reversed
        LD HL,(FDBOBJPOS)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD DE,(FDBPOOL)
        OR A
        SBC HL,DE
        RET C
        LD HL,(FDBOBJEND)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        JR C,FDBOBJBOUNDSOK
        JR NZ,FDBOBJBAD
FDBOBJBOUNDSOK:
        LD HL,(FDBOBJEND)
        LD DE,(FDBHIGH)
        OR A
        SBC HL,DE
        JR C,FDBOBJMARK
        JR Z,FDBOBJMARK
        LD HL,(FDBOBJEND)
        LD (FDBHIGH),HL
FDBOBJMARK:
        LD HL,(FDBOBJPOS)
        LD (FDBOBJPTR),HL
FOMLP:
        CALL FDBOWNPTR
        LD B,A
        AND (HL)
        SCF
        RET NZ
        LD A,B
        OR (HL)
        LD (HL),A
        LD HL,(FDBOBJPTR)
        INC HL
        LD (FDBOBJPTR),HL
        LD DE,(FDBOBJEND)
        OR A
        SBC HL,DE
        JR NZ,FOMLP
        OR A
        RET
FDBOBJBAD:
        SCF
        RET

; Address in FDBOBJPTR -> HL ownership byte, A bit mask.
FDBOWNPTR:
        LD HL,(FDBOBJPTR)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD A,L
        AND 7
        LD E,A
        LD D,0
        PUSH DE
        SRL H
        RR L
        SRL H
        RR L
        SRL H
        RR L
        LD DE,(FDBOWNBASE)
        ADD HL,DE
        POP DE
        PUSH HL
        LD HL,FDBBITS
        ADD HL,DE
        LD A,(HL)
        POP HL
        RET

; A = descriptor index -> HL = descriptor address, carry if outside catalogue.
FDBDESC:
        LD B,A
        LD A,(FCOUNT)
        CP B
        JR Z,FDBDESCBAD
        JR C,FDBDESCBAD
        LD HL,FDFRAM+128
        LD A,B
        OR A
        RET Z
        LD A,(FDBSTRIDE)
        LD E,A
        LD D,0
FDBADLP:
        ADD HL,DE
        DJNZ FDBADLP
        OR A
        RET
FDBDESCBAD:
        SCF
        RET

; A = descriptor index -> HL = 32-byte space-padded display description.
FDBNAME:
        CALL FDBDESC
        RET C
        LD DE,8
        ADD HL,DE
        RET

; A = descriptor index. Print its fixed 32-byte display description.
FDBPNAME:
        CALL FDBNAME
        RET C
        LD B,32
FPNLP:
        LD A,(HL)
        CALL PUTC
        INC HL
        DJNZ FPNLP
        OR A
        RET

; Print the FDB name matching CURB's normalized binding, or Custom/Undefined.
FDBCURNAME:
        LD A,(CURB)
        CP 0FFH
        JR Z,FDBCURUNDEFINED
        XOR A
        LD (FINDIDX),A
FDBCURLOOP:
        LD A,(FINDIDX)
        CALL FDBBIND
        JR C,FDBCURNEXT
        LD HL,CURB+1
        LD DE,BIND+1
        LD B,63
FDBCURCOMPARE:
        LD A,(DE)
        CP (HL)
        JR NZ,FDBCURNEXT
        INC HL
        INC DE
        DJNZ FDBCURCOMPARE
        LD A,(FINDIDX)
        JP FDBPNAME
FDBCURNEXT:
        LD A,(FINDIDX)
        INC A
        LD (FINDIDX),A
        LD B,A
        LD A,(FCOUNT)
        CP B
        JR NZ,FDBCURLOOP
        LD HL,CUSTOM
        JP PUTS
FDBCURUNDEFINED:
        LD HL,UNDEF
        JP PUTS

; A = descriptor index -> zero when an unknown required extension prevents use.
FDBISSUPPORTED:
        LD B,A
        LD A,(FCOUNT)
        CP B
        JR Z,FDBDESCBAD
        JR C,FDBDESCBAD
        LD A,B
        LD DE,FDBSUPPORT
        CALL FDBBITPTR
        AND (HL)
        OR A
        RET

; A = supported descriptor index -> the established 64-byte normalized BIND.
; Carry means the descriptor cannot be represented by the current BIOS record.
FDBBIND:
        LD (FDBBINDINDEX),A
        CALL FDBISSUPPORTED
        RET C
        SCF
        RET Z
        LD A,(FDBBINDINDEX)
        CALL FDBDESC
        RET C
        PUSH HL
        POP IX
        LD A,(IX+55)
        CP 33
        CCF
        RET C                           ; binding has 32 sector-ID slots
        LD HL,BIND
        LD DE,BIND+1
        LD BC,63
        LD (HL),0
        LDIR
        PUSH IX
        POP HL
        LD DE,40
        ADD HL,DE
        LD DE,BIND+1
        LD BC,15
        LDIR                            ; standard CP/M DPB
        LD A,(IX+57)
        LD (BIND+16),A                  ; cylinders
        LD A,(IX+55)
        LD (BIND+17),A                  ; physical sectors
        LD A,(IX+56)
        LD (BIND+18),A                  ; maximum sector-size code
        LD A,(IX+58)
        CALL FDBFLAGS
        LD (BIND+19),A
        LD L,(IX+60)
        LD H,(IX+61)
        LD DE,FDFRAM
        ADD HL,DE
        LD DE,BIND+20
        LD C,(IX+55)
        LD B,0
        LDIR                            ; ordered sector IDs
        LD A,(IX+62)
        OR (IX+63)
        RET Z
        LD L,(IX+62)
        LD H,(IX+63)
        LD DE,FDFRAM
        ADD HL,DE
FDBBINDEXT:
        LD A,(HL)
        OR A
        RET Z
        LD C,A
        INC HL
        LD A,(HL)
        LD (FDBEXLEN),A
        INC HL
        LD A,C
        CP 081H
        JR Z,FDBBINDMIXED
        CP 082H
        JR Z,FDBBINDCYLINDER
FDBBINDSKIP:
        LD A,(FDBEXLEN)
        LD E,A
        LD D,0
        ADD HL,DE
        JR FDBBINDEXT
FDBBINDCYLINDER:
        LD A,(BIND+19)
        OR 020H
        LD (BIND+19),A
        JR FDBBINDSKIP
FDBBINDMIXED:
        PUSH HL
        LD DE,BIND+53
        LD A,1
        LD (BIND+52),A
        XOR A
        LD (FDBPACKACC),A
        LD (FDBPACKPOS),A
        LD B,(IX+55)
FDBPACKLP:
        LD A,(HL)
        LD C,A
        LD A,(FDBPACKPOS)
        OR A
        JR Z,FDBPACKREADY
        PUSH BC
        LD B,A
FDBPACKSHIFT:
        LD A,C
        ADD A,A
        ADD A,A
        LD C,A
        DJNZ FDBPACKSHIFT
        LD A,C
        POP BC
        LD C,A
FDBPACKREADY:
        LD A,(FDBPACKACC)
        OR C
        LD (FDBPACKACC),A
        LD A,(FDBPACKPOS)
        INC A
        AND 3
        LD (FDBPACKPOS),A
        JR NZ,FDBPACKNEXT
        LD A,(FDBPACKACC)
        LD (DE),A
        INC DE
        XOR A
        LD (FDBPACKACC),A
FDBPACKNEXT:
        INC HL
        DJNZ FDBPACKLP
        LD A,(FDBPACKPOS)
        OR A
        JR Z,FDBPACKDONE
        LD A,(FDBPACKACC)
        LD (DE),A
FDBPACKDONE:
        POP HL
        JR FDBBINDSKIP

; Translate normalized FDB flags to the established MM-compatible binding bits.
FDBFLAGS:
        LD C,A
        LD B,0
        AND 1
        JR Z,FDBFLAG1
        LD A,B
        OR 040H
        LD B,A
FDBFLAG1:
        LD A,C
        AND 2
        JR Z,FDBFLAG2
        LD A,B
        OR 080H
        LD B,A
FDBFLAG2:
        LD A,C
        AND 4
        JR Z,FDBFLAG3
        LD A,B
        OR 010H
        LD B,A
FDBFLAG3:
        LD A,C
        AND 8
        JR Z,FDBFLAG4
        LD A,B
        OR 2
        LD B,A
FDBFLAG4:
        LD A,C
        AND 010H
        JR Z,FDBFLAG5
        LD A,B
        OR 1
        LD B,A
FDBFLAG5:
        LD A,C
        AND 020H
        JR Z,FDBFLAG6
        LD A,B
        OR 4
        LD B,A
FDBFLAG6:
        LD A,C
        AND 040H
        JR Z,FDBFLAGDONE
        LD A,B
        OR 8
        LD B,A
FDBFLAGDONE:
        LD A,B
        RET

; A index, DE bitmap base -> HL byte address, A bit mask.
FDBBITPTR:
        LD C,A
        AND 7
        LD L,A
        LD H,0
        PUSH DE
        LD DE,FDBBITS
        ADD HL,DE
        LD B,(HL)
        LD A,C
        RRCA
        RRCA
        RRCA
        AND 01FH
        LD L,A
        LD H,0
        POP DE
        ADD HL,DE
        LD A,B
        RET

; Require one to eight uppercase letters/digits followed only by spaces.
FDBID:  LD B,8
        LD C,0                           ; bit 0 seen char, bit 1 seen padding
FDBIDLP:
        LD A,(HL)
        INC HL
        CP ' '
        JR Z,FDBIDSPACE
        LD D,A
        LD A,C
        AND 2
        SCF
        RET NZ
        LD A,D
        CP '0'
        JR C,FDBIDBAD
        CP '9'+1
        JR C,FDBIDCHAR
        CP 'A'
        JR C,FDBIDBAD
        CP 'Z'+1
        JR NC,FDBIDBAD
FDBIDCHAR:
        LD A,C
        OR 1
        LD C,A
        DJNZ FDBIDLP
        LD A,C
        AND 1
        JR Z,FDBIDBAD
        OR A
        RET
FDBIDBAD:
        SCF
        RET
FDBIDSPACE:
        LD A,C
        OR 2
        LD C,A
        DJNZ FDBIDLP
        LD A,C
        AND 1
        JR Z,FDBIDBAD
        OR A
        RET

; Description is 1..32 printable ASCII characters with space padding.
FDBDESCRIPTION:
        LD B,32
        LD C,0
FDBTXLP:
        LD A,(HL)
        INC HL
        CP 32
        JR C,FDBDESCTBAD
        CP 127
        JR NC,FDBDESCTBAD
        CP ' '
        JR Z,FDBDESCNEXT
        LD C,1
FDBDESCNEXT:
        DJNZ FDBTXLP
        LD A,C
        OR A
        JR Z,FDBDESCTBAD
        OR A
        RET
FDBDESCTBAD:
        SCF
        RET

FDBBAD: SCF
        RET

FDBMAG: DB 'BFDB'
FDBNOMSG:DB 'Cannot open DISK.FDB on current drive or A:.',13,10,0
FDBBADMSG:DB 'DISK.FDB has invalid framing or CRC.',13,10,0
FDBFCB: DB 0,'DISK    FDB'
        DS 24
FDBPOS: DW 0
FDBLEN: DW 0
FDBPOOL:DW 0
FDBEXPECT:DW 0
FDBHSIZE:DB 0
FDBSTRIDE:DB 0
FDBINDEX:DB 0
FDBEXSTART:DW 0
FDBEXTYPE:DB 0
FDBEXLEN:DB 0
FDBOBJPOS:DW 0
FDBOBJEND:DW 0
FDBOBJPTR:DW 0
FDBHIGH:DW 0
FDBOWNBASE:DW 0
FDBOWNSIZE:DW 0
FDBBINDINDEX:DB 0
FDBPACKACC:DB 0
FDBPACKPOS:DB 0
FDBBITS:DB 1,2,4,8,16,32,64,128
FDBTYPES:DS 16
FDBSUPPORT:DS 32
