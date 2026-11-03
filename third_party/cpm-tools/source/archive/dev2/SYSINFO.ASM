; SYSINFO Version 1.0.0-dev2 - add read-only system-state report
; Intel 8080 instruction subset, using z80asm/M80-compatible Z80 mnemonics.
;
; All system facts come from documented page-zero fields or BDOS function 12.
; In particular, the CCP base and physical system top are not exposed by the
; standard interface, so they are deliberately reported as Unknown.

        ORG     0100H

BDOS    EQU     0005H
WBOOTOP EQU     0000H
WBOOTAD EQU     0001H
IOBYTE  EQU     0003H
BDOSOP  EQU     0005H
BDOSAD  EQU     0006H
DMADEF  EQU     0080H

START:  LD      SP,STACKTOP
        LD      HL,0
        PUSH    HL              ; RET returns through CP/M warm boot
        CALL    PARSE
        CP      0
        JP      Z,SUMMARY
        CP      1
        JP      Z,MEMORY
        CP      2
        JP      Z,IOINFO
        CP      3
        JP      Z,VECTORS
        CP      4
        JP      Z,ALLINFO
        CP      5
        JP      Z,HELP
        CP      6
        JP      Z,DISKINFO
        CP      7
        JP      Z,DPBINFO
        CP      8
        JP      Z,STATEINFO
        LD      DE,BADOPT
        CALL    PUTS
        RET

; Return A=0 default, 1 /MEM, 2 /IO, 3 /VECTORS, 4 /ALL, 5 /H,
; 6 /DISK, 7 /DPB, 8 /STATE, or FF invalid.
PARSE:  LD      A,(0080H)
        OR      A
        RET     Z
        LD      B,A
        LD      HL,0081H
PSPACE:LD      A,(HL)
        CP      ' '
        JP      NZ,PSLASH
        INC     HL
        DEC     B
        JP      NZ,PSPACE
        XOR     A
        RET
PSLASH:CP      '/'
        JP      NZ,PBAD
        INC     HL
        DEC     B
        JP      Z,PBAD
        LD      DE,OPBUF
        LD      C,9              ; longest accepted token is VECTORS
PCOPY: LD      A,(HL)
        CP      ' '
        JP      Z,PCDONE
        LD      A,C
        OR      A
        JP      Z,PBAD
        DEC     C
        LD      A,(HL)
        AND     5FH             ; ASCII lower case to upper case
        LD      (DE),A
        INC     DE
        INC     HL
        DEC     B
        JP      NZ,PCOPY
PCDONE:XOR     A
        LD      (DE),A
        LD      (PTAILP),HL
        LD      A,B
        LD      (PTAILN),A
PTEST: LD      HL,OPBUF
        LD      DE,TXTH
        CALL    STREQ
        OR      A
        JP      NZ,PH
        LD      HL,OPBUF
        LD      DE,TXTMEM
        CALL    STREQ
        OR      A
        JP      NZ,PMEM
        LD      HL,OPBUF
        LD      DE,TXTIO
        CALL    STREQ
        OR      A
        JP      NZ,PIO
        LD      HL,OPBUF
        LD      DE,TXTVEC
        CALL    STREQ
        OR      A
        JP      NZ,PVEC
        LD      HL,OPBUF
        LD      DE,TXTALL
        CALL    STREQ
        OR      A
        JP      NZ,PALL
        LD      HL,OPBUF
        LD      DE,TXTDISK
        CALL    STREQ
        OR      A
        JP      NZ,PDISK
        LD      HL,OPBUF
        LD      DE,TXTDPB
        CALL    STREQ
        OR      A
        JP      NZ,PDPB
        LD      HL,OPBUF
        LD      DE,TXTSTATE
        CALL    STREQ
        OR      A
        JP      NZ,PSTATE
PBAD:  LD      A,0FFH
        RET
PH:    LD      C,5
        JP      PCHECK
PMEM:  LD      C,1
        JP      PCHECK
PIO:   LD      C,2
        JP      PCHECK
PVEC:  LD      C,3
        JP      PCHECK
PALL:  LD      C,4
        JP      PCHECK
PSTATE:LD      C,8
        JP      PCHECK

; Simple options allow trailing spaces but no additional operands.
PCHECK:LD      HL,(PTAILP)
        LD      A,(PTAILN)
        LD      B,A
PCHKLP:LD      A,B
        OR      A
        JP      Z,PCHKOK
        LD      A,(HL)
        CP      ' '
        JP      NZ,PBAD
        INC     HL
        DEC     B
        JP      PCHKLP
PCHKOK:LD      A,C
        RET

PDISK: LD      A,6
        JP      PARGINIT
PDPB:  LD      A,7
PARGINIT:
        LD      (SELMODE),A
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        LD      (LOGFLAG),A
        LD      HL,(PTAILP)
        LD      A,(PTAILN)
        LD      B,A
PARGSP:LD      A,B
        OR      A
        JP      Z,PARGEND
        LD      A,(HL)
        CP      ' '
        JP      NZ,PARGTOK
        INC     HL
        DEC     B
        JP      PARGSP
PARGTOK:
        CP      '/'
        JP      Z,PARGOPT
        LD      A,(LOGFLAG)
        OR      A
        JP      NZ,PBAD
        LD      A,(HL)
        AND     5FH
        CP      'A'
        JP      C,PBAD
        CP      'P'+1
        JP      NC,PBAD
        LD      C,A
        LD      A,B
        CP      2
        JP      C,PBAD
        INC     HL
        LD      A,(HL)
        CP      ':'
        JP      NZ,PBAD
        INC     HL
        DEC     B
        DEC     B
        LD      A,B
        OR      A
        JP      Z,PSETDRV
        LD      A,(HL)
        CP      ' '
        JP      NZ,PBAD
PSETDRV:
        LD      A,C
        SUB     'A'
        ADD     A,A
        LD      E,A
        LD      D,0
        PUSH    HL
        LD      HL,BITTAB
        ADD     HL,DE
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      HL,(DRVMASK)
        LD      A,L
        OR      E
        LD      L,A
        LD      A,H
        OR      D
        LD      H,A
        LD      (DRVMASK),HL
        POP     HL
        JP      PARGSP

; /LOGGED is accepted only as the sole /DISK operand.
PARGOPT:
        LD      A,(SELMODE)
        CP      6
        JP      NZ,PBAD
        LD      A,(DRVMASK)
        LD      C,A
        LD      A,(DRVMASK+1)
        OR      C
        JP      NZ,PBAD
        LD      A,(LOGFLAG)
        OR      A
        JP      NZ,PBAD
        INC     HL
        DEC     B
        LD      DE,TXTLOG
PLOGCP:LD      A,(DE)
        OR      A
        JP      Z,PLOGDONE
        LD      C,A
        LD      A,B
        OR      A
        JP      Z,PBAD
        LD      A,(HL)
        AND     5FH
        CP      C
        JP      NZ,PBAD
        INC     HL
        INC     DE
        DEC     B
        JP      PLOGCP
PLOGDONE:
        LD      A,B
        OR      A
        JP      Z,PLOGOK
        LD      A,(HL)
        CP      ' '
        JP      NZ,PBAD
PLOGOK:LD      A,1
        LD      (LOGFLAG),A
        JP      PARGSP
PARGEND:
        LD      A,(SELMODE)
        RET

; Compare zero-terminated strings HL and DE; A=1 equal, A=0 unequal.
STREQ: LD      A,(DE)
        CP      (HL)
        JP      NZ,SNOTEQ
        OR      A
        JP      Z,SEQUAL
        INC     HL
        INC     DE
        JP      STREQ
SNOTEQ:XOR     A
        RET
SEQUAL:LD      A,1
        RET

SUMMARY:
        LD      DE,TITLE
        CALL    PUTS
        LD      DE,VERLAB
        CALL    PUTS
        CALL    VERSION
        LD      DE,SUMMEM
        CALL    PUTS
        LD      HL,0100H
        CALL    HEX16
        CALL    PUTH
        LD      DE,SUMTPA
        CALL    PUTS
        CALL    GETBDOS
        CALL    PADDR
        LD      DE,SUMSYS
        CALL    PUTS
        LD      DE,UNKNOWN
        CALL    PUTS
        LD      DE,SUMBDOS
        CALL    PUTS
        CALL    GETBDOS
        CALL    PADDR
        LD      DE,SUMBIOS
        CALL    PUTS
        CALL    GETBIOS
        CALL    PADDR
        RET

MEMORY:
        LD      DE,MEMHEAD
        CALL    PUTS
        LD      DE,MTPA
        CALL    PUTS
        LD      HL,0100H
        CALL    HEX16
        CALL    PUTH
        LD      DE,MBDOS
        CALL    PUTS
        CALL    GETBDOS
        CALL    PADDR
        LD      DE,MBIOS
        CALL    PUTS
        CALL    GETBIOS
        CALL    PADDR
        LD      DE,MTOP
        CALL    PUTS
        LD      DE,UNKNOWN
        CALL    PUTS
        LD      DE,MSIZE
        CALL    PUTS
        CALL    GETBDOS
        OR      A
        JP      Z,MUNKNOWN
        DEC     H               ; documented boundary minus COM base 0100h
        CALL    DEC16
        LD      DE,BYTES
        CALL    PUTS
        RET
MUNKNOWN:
        LD      DE,UNKNOWN
        CALL    PUTS
        RET

VECTORS:
        LD      DE,VECHEAD
        CALL    PUTS
        LD      DE,VWARM
        CALL    PUTS
        CALL    GETWARM
        CALL    PADDR
        LD      DE,VBDOSV
        CALL    PUTS
        CALL    GETBDOS
        CALL    PADDR
        LD      DE,VBDOSE
        CALL    PUTS
        LD      HL,BDOS
        CALL    HEX16
        CALL    PUTH
        LD      DE,VDMA
        CALL    PUTS
        LD      HL,DMADEF
        CALL    HEX16
        CALL    PUTH
        RET

IOINFO:
        LD      DE,IOHEAD
        CALL    PUTS
        LD      A,(IOBYTE)
        LD      (IOVAL),A
        CALL    HEX8
        CALL    PUTH
        LD      DE,CONLAB
        CALL    PUTS
        LD      A,(IOVAL)
        AND     03H
        LD      HL,CONTAB
        CALL    PTABLE
        LD      DE,RDRLAB
        CALL    PUTS
        LD      A,(IOVAL)
        RRCA
        RRCA
        AND     03H
        LD      HL,RDRTAB
        CALL    PTABLE
        LD      DE,PUNLAB
        CALL    PUTS
        LD      A,(IOVAL)
        RRCA
        RRCA
        RRCA
        RRCA
        AND     03H
        LD      HL,PUNTAB
        CALL    PTABLE
        LD      DE,LSTLAB
        CALL    PUTS
        LD      A,(IOVAL)
        RLCA
        RLCA
        AND     03H
        LD      HL,LSTTAB
        CALL    PTABLE
        RET

; Function 25 and Function 32 query current state without changing it.
; Functions 24 and 29 return public bit vectors; decoding them here saves the
; operator from counting bits on the back of an envelope.
STATEINFO:
        LD      C,25
        CALL    BDOS
        LD      (STATECUR),A
        LD      E,0FFH
        LD      C,32
        CALL    BDOS
        LD      (STATEUSER),A
        LD      C,24
        CALL    BDOS
        LD      (STLOGV),HL
        LD      C,29
        CALL    BDOS
        LD      (STROV),HL
        LD      DE,STATEHEAD
        CALL    PUTS
        LD      DE,STATECD
        CALL    PUTS
        LD      A,(STATECUR)
        ADD     A,'A'
        CALL    PUTCH
        LD      DE,COLON
        CALL    PUTS
        LD      DE,STATEUSR
        CALL    PUTS
        LD      A,(STATEUSER)
        LD      L,A
        LD      H,0
        CALL    PDECEND
        LD      DE,STATELOGIN
        CALL    PUTS
        LD      HL,(STLOGV)
        CALL    HEX16
        LD      DE,OPENPAR
        CALL    PUTS
        LD      HL,(STLOGV)
        CALL    PDRVLIST
        LD      DE,CLOSEPAR
        CALL    PUTS
        LD      DE,STATEROONLY
        CALL    PUTS
        LD      HL,(STROV)
        CALL    HEX16
        LD      DE,OPENPAR
        CALL    PUTS
        LD      HL,(STROV)
        CALL    PDRVLIST
        LD      DE,CLOSEPAR
        JP      PUTS

; Print a public drive mask as A: through P:, or "none" for zero.
PDRVLIST:
        LD      A,H
        OR      L
        JP      NZ,PDLSTART
        LD      DE,NONE
        JP      PUTS
PDLSTART:
        LD      (STATEWORK),HL
        XOR     A
        LD      (STATEIDX),A
        LD      (STATEFIRST),A
PDLLOOP:
        LD      HL,(STATEWORK)
        LD      A,L
        AND     1
        JP      Z,PDLSHIFT
        LD      A,(STATEFIRST)
        OR      A
        JP      Z,PDLLETTER
        LD      A,' '
        CALL    PUTCH
PDLLETTER:
        LD      A,(STATEIDX)
        ADD     A,'A'
        CALL    PUTCH
        LD      A,':'
        CALL    PUTCH
        LD      A,1
        LD      (STATEFIRST),A
PDLSHIFT:
        LD      HL,(STATEWORK)
        CALL    SHRHL
        LD      (STATEWORK),HL
        LD      A,(STATEIDX)
        INC     A
        LD      (STATEIDX),A
        CP      16
        JP      NZ,PDLLOOP
        RET

; /DISK and /DPB share drive selection and DPB acquisition.  BDOS functions
; 14 and 31 are used for maximum BIOS portability, and the original current
; drive is restored before any report is printed.  Selecting an explicitly
; named, previously unused drive can add it to BDOS's login vector, but no
; directory or data sector is read or written by SYSINFO.
DISKINFO:
        LD      A,0
        LD      (REPORTDPB),A
        JP      DISKSETUP
DPBINFO:
        LD      A,1
        LD      (REPORTDPB),A
DISKSETUP:
        LD      C,25
        CALL    BDOS
        LD      (ORIGDRV),A
        LD      C,24
        CALL    BDOS
        LD      (LOGINMASK),HL
        LD      C,29
        CALL    BDOS
        LD      (ROMASK),HL
DSMASK:LD      A,(LOGFLAG)
        OR      A
        JP      Z,DSGIVEN
        LD      HL,(LOGINMASK)
        LD      (DRVMASK),HL
        JP      DSREADY
DSGIVEN:
        LD      HL,(DRVMASK)
        LD      A,H
        OR      L
        JP      NZ,DSREADY
        LD      A,(ORIGDRV)
        CALL    MAKEMASK
        LD      (DRVMASK),HL
DSREADY:
        LD      HL,(DRVMASK)
        LD      (WORKMASK),HL
        LD      HL,(LOGINMASK)
        LD      (LOGINWORK),HL
        LD      HL,(ROMASK)
        LD      (ROWORK),HL
        XOR     A
        LD      (CURINDEX),A
        LD      B,16
DSLOOP:PUSH    BC
        LD      HL,(WORKMASK)
        LD      A,L
        AND     1
        CALL    NZ,SHOWDRIVE
        CALL    SHIFTMASKS
        LD      A,(CURINDEX)
        INC     A
        LD      (CURINDEX),A
        POP     BC
        DEC     B
        JP      NZ,DSLOOP
        RET

; Build a one-bit drive mask in HL from drive number A (0=A ... 15=P).
MAKEMASK:
        ADD     A,A
        LD      E,A
        LD      D,0
        LD      HL,BITTAB
        ADD     HL,DE
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        EX      DE,HL
        RET

SHOWDRIVE:
        CALL    FETCHDPB
        PUSH    AF
        LD      DE,DISKHEAD
        CALL    PUTS
        LD      A,(CURINDEX)
        ADD     A,'A'
        CALL    PUTCH
        LD      DE,COLON
        CALL    PUTS
        POP     AF
        OR      A
        JP      Z,DRIVEUNK
        LD      A,(REPORTDPB)
        OR      A
        JP      NZ,SHOWDPB
        JP      SHOWDISK
DRIVEUNK:
        LD      DE,UNAVAIL
        JP      PUTS

; Select through BDOS and copy the standard 15-byte DPB to private storage.
FETCHDPB:
        LD      A,(CURINDEX)
        LD      E,A
        LD      C,14
        CALL    BDOS
        LD      C,31
        CALL    BDOS
        LD      A,H
        OR      L
        JP      Z,FDPFAIL
        LD      (DPBPTR),HL
        LD      DE,DPBBUF
        LD      B,15
FDPCPY:LD      A,(HL)
        LD      (DE),A
        INC     HL
        INC     DE
        DEC     B
        JP      NZ,FDPCPY
        LD      A,(ORIGDRV)
        LD      E,A
        LD      C,14
        CALL    BDOS
        LD      A,1
        RET
FDPFAIL:
        LD      A,(ORIGDRV)
        LD      E,A
        LD      C,14
        CALL    BDOS
        XOR     A
        RET

SHOWDISK:
        LD      DE,DSTATUS
        CALL    PUTS
        LD      DE,DLOGGED
        CALL    PUTS
        LD      HL,(LOGINWORK)
        LD      A,L
        AND     1
        CALL    YESNO
        LD      DE,DREADONLY
        CALL    PUTS
        LD      HL,(ROWORK)
        LD      A,L
        AND     1
        CALL    YESNO
        LD      DE,DCURRENT
        CALL    PUTS
        LD      A,(CURINDEX)
        LD      C,A
        LD      A,(ORIGDRV)
        CP      C
        LD      A,0
        JP      NZ,DSCURR
        INC     A
DSCURR:CALL    YESNO
        LD      DE,DGEOM
        CALL    PUTS
        LD      DE,DSECSIZE
        CALL    PUTS
        LD      HL,128
        CALL    PDECEND
        LD      DE,DSPT
        CALL    PUTS
        LD      HL,(DPBBUF)
        CALL    PDECEND
        LD      DE,DBLOCK
        CALL    PUTS
        LD      HL,128
        LD      A,(DPBBUF+2)
        LD      B,A
DBLSH: LD      A,B
        OR      A
        JP      Z,DBLDONE
        ADD     HL,HL
        DEC     B
        JP      DBLSH
DBLDONE:
        CALL    PDECEND
        LD      DE,DALLOCS
        CALL    PUTS
        LD      HL,(DPBBUF+5)
        INC     HL
        CALL    PDECEND
        LD      DE,DDIRENTS
        CALL    PUTS
        LD      HL,(DPBBUF+7)
        INC     HL
        CALL    PDECEND
        LD      DE,DRESERVED
        CALL    PUTS
        LD      HL,(DPBBUF+13)
        CALL    PDECEND
        RET

SHOWDPB:
        LD      DE,DPBADDR
        CALL    PUTS
        LD      HL,(DPBPTR)
        CALL    HEX16
        CALL    PUTH
        LD      DE,FSPT
        CALL    PUTS
        LD      HL,(DPBBUF)
        CALL    PHEXDEC
        LD      DE,FBSH
        CALL    PUTS
        LD      A,(DPBBUF+2)
        CALL    PBYTEDEC
        LD      DE,FBLM
        CALL    PUTS
        LD      A,(DPBBUF+3)
        CALL    PBYTEDEC
        LD      DE,FEXM
        CALL    PUTS
        LD      A,(DPBBUF+4)
        CALL    PBYTEDEC
        LD      DE,FDSM
        CALL    PUTS
        LD      HL,(DPBBUF+5)
        CALL    PHEXDEC
        LD      DE,FDRM
        CALL    PUTS
        LD      HL,(DPBBUF+7)
        CALL    PHEXDEC
        LD      DE,FAL0
        CALL    PUTS
        LD      A,(DPBBUF+9)
        CALL    PBYTEHEX
        LD      DE,FAL1
        CALL    PUTS
        LD      A,(DPBBUF+10)
        CALL    PBYTEHEX
        LD      DE,FCKS
        CALL    PUTS
        LD      HL,(DPBBUF+11)
        CALL    PHEXDEC
        LD      DE,FOFF
        CALL    PUTS
        LD      HL,(DPBBUF+13)
        CALL    PHEXDEC
        RET

YESNO: OR      A
        LD      DE,NO
        JP      Z,YNPRINT
        LD      DE,YES
YNPRINT:JP     PUTS
PDECEND:
        CALL    DEC16
        LD      DE,CRLF
        JP      PUTS
PHEXDEC:
        PUSH    HL
        CALL    HEX16
        LD      DE,OPENPAR
        CALL    PUTS
        POP     HL
        CALL    DEC16
        LD      DE,CLOSEPAR
        JP      PUTS
PBYTEDEC:
        PUSH    AF
        CALL    HEX8
        LD      DE,OPENPAR
        CALL    PUTS
        POP     AF
        LD      L,A
        LD      H,0
        CALL    DEC16
        LD      DE,CLOSEPAR
        JP      PUTS
PBYTEHEX:
        CALL    HEX8
        JP      PUTH

SHIFTMASKS:
        LD      HL,(WORKMASK)
        CALL    SHRHL
        LD      (WORKMASK),HL
        LD      HL,(LOGINWORK)
        CALL    SHRHL
        LD      (LOGINWORK),HL
        LD      HL,(ROWORK)
        CALL    SHRHL
        LD      (ROWORK),HL
        RET
SHRHL: XOR     A
        LD      A,H
        RRA
        LD      H,A
        LD      A,L
        RRA
        LD      L,A
        RET

ALLINFO:
        CALL    SUMMARY
        CALL    STATEINFO
        CALL    MEMORY
        CALL    IOINFO
        CALL    VECTORS
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        LD      (LOGFLAG),A
        CALL    DISKINFO
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        JP      DPBINFO

HELP:  LD      DE,HELPMSG
        CALL    PUTS
        RET

; Validate documented JMP vectors before trusting their address fields.
GETBDOS:
        LD      A,(BDOSOP)
        CP      0C3H
        JP      NZ,GFAIL
        LD      HL,(BDOSAD)
        LD      A,H
        OR      L
        JP      Z,GFAIL
        LD      A,1
        RET
GETWARM:
        LD      A,(WBOOTOP)
        CP      0C3H
        JP      NZ,GFAIL
        LD      HL,(WBOOTAD)
        LD      A,H
        OR      L
        JP      Z,GFAIL
        LD      A,1
        RET
GETBIOS:
        CALL    GETWARM
        OR      A
        RET     Z
        DEC     HL              ; WBOOT is BIOS jump-table entry BIOS+3
        DEC     HL
        DEC     HL
        LD      A,1
        RET
GFAIL: XOR     A
        RET

; Print address in HL when A nonzero, otherwise Unknown.
PADDR: OR      A
        JP      Z,PAUNK
        CALL    HEX16
        JP      PUTH
PAUNK: LD      DE,UNKNOWN
        JP      PUTS

; BDOS function 12: H=system type, L=BCD-like major/minor version byte.
VERSION:
        LD      C,12
        CALL    BDOS
        LD      A,H
        OR      A
        JP      NZ,VUNKNOWN
        LD      A,L
        PUSH    AF
        RRCA
        RRCA
        RRCA
        RRCA
        AND     0FH
        ADD     A,'0'
        CALL    PUTCH
        LD      A,'.'
        CALL    PUTCH
        POP     AF
        AND     0FH
        ADD     A,'0'
        CALL    PUTCH
        LD      DE,CRLF
        JP      PUTS
VUNKNOWN:
        LD      DE,UNKNOWN
        JP      PUTS

; A indexes four zero-terminated string pointers at HL.
PTABLE:ADD     A,A
        LD      E,A
        LD      D,0
        ADD     HL,DE
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        CALL    PUTZ
        LD      DE,CRLF
        JP      PUTS

PUTH:  LD      A,'h'
        CALL    PUTCH
        LD      DE,CRLF
        JP      PUTS
HEX16: LD      A,H
        CALL    HEX8
        LD      A,L
HEX8:  PUSH    AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL    HEXNIB
        POP     AF
HEXNIB:AND     0FH
        ADD     A,'0'
        CP      '9'+1
        JP      C,PUTCH
        ADD     A,7
        JP      PUTCH

; Unsigned 16-bit decimal output, including zero.
DEC16: LD      DE,10000
        XOR     A
        LD      (DSTART),A
        CALL    DECDIG
        LD      DE,1000
        CALL    DECDIG
        LD      DE,100
        CALL    DECDIG
        LD      DE,10
        CALL    DECDIG
        LD      A,L
        ADD     A,'0'
        JP      PUTCH
DECDIG:LD      B,'0'
DDLOOP:OR      A
        CALL    SUBHLDE
        JP      C,DDDONE
        INC     B
        JP      DDLOOP
DDDONE:ADD     HL,DE
        LD      A,(DSTART)
        OR      A
        JP      NZ,DDPRINT
        LD      A,B
        CP      '0'
        RET     Z
        LD      A,1
        LD      (DSTART),A
DDPRINT:LD     A,B
        JP      PUTCH

; Intel 8080-compatible unsigned HL := HL-DE, returning the borrow in carry.
SUBHLDE:
        LD      A,L
        SUB     E
        LD      L,A
        LD      A,H
        SBC     A,D
        LD      H,A
        RET

PUTS:  LD      C,9
        JP      BDOS
PUTZ:  LD      A,(DE)
        OR      A
        RET     Z
        PUSH    DE
        CALL    PUTCH
        POP     DE
        INC     DE
        JP      PUTZ
PUTCH: PUSH    BC
        PUSH    DE
        PUSH    HL              ; CP/M only guarantees A as function result
        LD      E,A
        LD      C,2
        CALL    BDOS
        POP     HL
        POP     DE
        POP     BC
        RET

TXTH:   DB 'H',0
TXTMEM: DB 'MEM',0
TXTIO:  DB 'IO',0
TXTVEC: DB 'VECTORS',0
TXTALL: DB 'ALL',0
TXTDISK:DB 'DISK',0
TXTDPB: DB 'DPB',0
TXTSTATE:DB 'STATE',0
TXTLOG: DB 'LOGGED',0

TITLE:  DB 13,10,'CP/M System Information',13,10,'$'
VERLAB: DB 13,10,'Version:',13,10,'  CP/M ','$'
SUMMEM: DB 13,10,'Memory:',13,10,'  TPA start:       ','$'
SUMTPA: DB '  Top of TPA:      ','$'
SUMSYS: DB 13,10,'System:',13,10,'  CCP address:     ','$'
SUMBDOS:DB '  BDOS address:    ','$'
SUMBIOS:DB '  BIOS address:    ','$'

MEMHEAD:DB 13,10,'CP/M Memory Layout',13,10,'$'
MTPA:   DB '  TPA start:       ','$'
MBDOS:  DB '  BDOS address:    ','$'
MBIOS:  DB '  BIOS address:    ','$'
MTOP:   DB '  System top:      ','$'
MSIZE:  DB '  TPA size:        ','$'
BYTES:  DB ' bytes',13,10,'$'

VECHEAD:DB 13,10,'Standard Low-Memory Vectors',13,10,'$'
VWARM:  DB '  Warm boot vector (0001h): ','$'
VBDOSV: DB '  BDOS vector (0006h):      ','$'
VBDOSE: DB '  BDOS entry (0005h):       ','$'
VDMA:   DB '  Default DMA address:       ','$'

IOHEAD: DB 13,10,'CP/M I/O Assignments',13,10,'  IOBYTE:   ','$'
CONLAB: DB '  Console:  ','$'
RDRLAB: DB '  Reader:   ','$'
PUNLAB: DB '  Punch:    ','$'
LSTLAB: DB '  List:     ','$'

STATEHEAD:DB 13,10,'CP/M System State',13,10,'$'
STATECD:DB '  Current drive:     ','$'
STATEUSR:DB '  Current user:      ','$'
STATELOGIN:DB '  Login vector:      ','$'
STATEROONLY:DB '  Read-only vector:  ','$'

HELPMSG:DB 13,10,'SYSINFO - CP/M system information',13,10,13,10
        DB 'Usage: SYSINFO [option]',13,10,13,10
        DB '  /MEM      Display memory layout',13,10
        DB '  /IO       Display IOBYTE and device assignments',13,10
        DB '  /VECTORS  Display standard low-memory vectors',13,10
        DB '  /STATE    Display current drive/user and public drive vectors',13,10
        DB '  /DISK [drives]  Display disk summaries; default is current',13,10
        DB '  /DISK /LOGGED   Display summaries for logged-in drives',13,10
        DB '  /DPB [drives]   Display raw/decoded disk parameter blocks',13,10
        DB '  /ALL      Display summary and all current-drive details',13,10
        DB '  /H        Display this help',13,10
        DB 13,10,'Drive lists use the form A: B: C:.',13,10
        DB 13,10,'With no option, display a system summary.',13,10,'$'
BADOPT: DB 13,10,'SYSINFO: invalid option; use SYSINFO /H',13,10,'$'
UNKNOWN:DB 'Unknown',13,10,'$'
CRLF:   DB 13,10,'$'
COLON:  DB ':',13,10,'$'
YES:    DB 'Yes',13,10,'$'
NO:     DB 'No',13,10,'$'
UNAVAIL:DB '  Unavailable',13,10,'$'
OPENPAR:DB 'h  (', '$'
CLOSEPAR:DB ')',13,10,'$'
NONE:    DB 'none$'

DISKHEAD:DB 13,10,'Disk ','$'
DSTATUS:DB 'Status:',13,10,'$'
DLOGGED:DB '  Logged in:              ','$'
DREADONLY:DB '  Read-only:              ','$'
DCURRENT:DB '  Current drive:          ','$'
DGEOM:  DB 13,10,'Geometry:',13,10,'$'
DSECSIZE:DB '  Logical sector bytes:   ','$'
DSPT:   DB '  Records per track:      ','$'
DBLOCK: DB '  Allocation block bytes: ','$'
DALLOCS:DB '  Allocation blocks:      ','$'
DDIRENTS:DB '  Directory entries:      ','$'
DRESERVED:DB '  Reserved tracks:        ','$'

DPBADDR:DB 'DPB:',13,10,'  Address:  ','$'
FSPT:   DB '  SPT:      ','$'
FBSH:   DB '  BSH:      ','$'
FBLM:   DB '  BLM:      ','$'
FEXM:   DB '  EXM:      ','$'
FDSM:   DB '  DSM:      ','$'
FDRM:   DB '  DRM:      ','$'
FAL0:   DB '  AL0:      ','$'
FAL1:   DB '  AL1:      ','$'
FCKS:   DB '  CKS:      ','$'
FOFF:   DB '  OFF:      ','$'

CTTY: DB 'TTY',0
CCRT: DB 'CRT',0
CBAT: DB 'BAT',0
CUC1: DB 'UC1',0
RDTY: DB 'TTY',0
RPTR: DB 'PTR',0
RUR1: DB 'UR1',0
RUR2: DB 'UR2',0
PUTTY:DB 'TTY',0
PPTP: DB 'PTP',0
PUP1: DB 'UP1',0
PUP2: DB 'UP2',0
LTTY: DB 'TTY',0
LCRT: DB 'CRT',0
LLPT: DB 'LPT',0
LUL1: DB 'UL1',0
CONTAB:DW CTTY,CCRT,CBAT,CUC1
RDRTAB:DW RDTY,RPTR,RUR1,RUR2
PUNTAB:DW PUTTY,PPTP,PUP1,PUP2
LSTTAB:DW LTTY,LCRT,LLPT,LUL1
BITTAB:DW 0001H,0002H,0004H,0008H,0010H,0020H,0040H,0080H
        DW 0100H,0200H,0400H,0800H,1000H,2000H,4000H,8000H

OPBUF:  DS 10
IOVAL:  DB 0
DSTART: DB 0
PTAILP: DW 0
PTAILN: DB 0
SELMODE:DB 0
LOGFLAG:DB 0
DRVMASK:DW 0
LOGINMASK:DW 0
ROMASK: DW 0
WORKMASK:DW 0
LOGINWORK:DW 0
ROWORK: DW 0
ORIGDRV:DB 0
CURINDEX:DB 0
REPORTDPB:DB 0
DPBPTR:DW 0
DPBBUF:DS 15
STATECUR:DB 0
STATEUSER:DB 0
STLOGV: DW 0
STROV:  DW 0
STATEWORK:DW 0
STATEIDX:DB 0
STATEFIRST:DB 0
        DS 128
STACKTOP:
        END
