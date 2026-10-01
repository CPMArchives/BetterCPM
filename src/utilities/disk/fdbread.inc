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
        XOR A
        LD (FDBINDEX),A
FDBDALP:
        LD A,(FDBINDEX)
        LD B,A
        LD A,(FCOUNT)
        CP B
        RET Z
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
        JR NC,FDBDESCBAD
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
        JR Z,FDBDESCBAD                 ; nonzero offset requires flag
        JR FDBIDS
FDBNOEXT:
        LD A,C
        OR A
        JR NZ,FDBDESCBAD                ; flag requires nonzero offset
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
        LD DE,(FDBLEN)
        OR A
        SBC HL,DE
        JR C,FDBIDSGOOD
        JR NZ,FDBDESCBAD                ; end may equal file length
FDBIDSGOOD:
        LD A,(FDBINDEX)
        INC A
        LD (FDBINDEX),A
        JR FDBDALP

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
