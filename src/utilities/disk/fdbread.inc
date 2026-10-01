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
        OR A
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
