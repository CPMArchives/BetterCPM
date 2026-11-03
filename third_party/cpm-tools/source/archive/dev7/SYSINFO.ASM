; SYSINFO Version 1.0.0-dev7 - add map, version, and short overview reports
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
        CP      9
        JP      Z,SPACEINFO
        CP      10
        JP      Z,BIOSINFO
        CP      11
        JP      Z,CHECKINFO
        CP      12
        JP      Z,DRIVESINFO
        CP      13
        JP      Z,ALLOCINFO
        CP      14
        JP      Z,MAPINFO
        CP      15
        JP      Z,VERINFO
        CP      16
        JP      Z,SHORTINFO
        LD      DE,BADOPT
        CALL    PUTS
        RET

; Return A=0 default, 1 /MEM, 2 /IO, 3 /VECTORS, 4 /ALL, 5 /H,
; 6 /DISK, 7 /DPB, 8 /STATE, 9 /SPACE, 10 /BIOS, 11 /CHECK,
; 12 /DRIVES, 13 /ALLOC, 14 /MAP, 15 /VER or /VERSION,
; 16 /ALL:SHORT, or FF invalid.
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
        CP      'a'
        JP      C,PCSTORE
        CP      'z'+1
        JP      NC,PCSTORE
        AND     5FH             ; fold letters only; preserve ':' in ALL:SHORT
PCSTORE:
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
        LD      HL,OPBUF
        LD      DE,TXTSPACE
        CALL    STREQ
        OR      A
        JP      NZ,PSPACEOPT
        LD      HL,OPBUF
        LD      DE,TXTBIOS
        CALL    STREQ
        OR      A
        JP      NZ,PBIOS
        LD      HL,OPBUF
        LD      DE,TXTCHECK
        CALL    STREQ
        OR      A
        JP      NZ,PCHECKOPT
        LD      HL,OPBUF
        LD      DE,TXTDRIVES
        CALL    STREQ
        OR      A
        JP      NZ,PDRIVES
        LD      HL,OPBUF
        LD      DE,TXTALLOC
        CALL    STREQ
        OR      A
        JP      NZ,PALLOC
        LD      HL,OPBUF
        LD      DE,TXTMAP
        CALL    STREQ
        OR      A
        JP      NZ,PMAP
        LD      HL,OPBUF
        LD      DE,TXTVER
        CALL    STREQ
        OR      A
        JP      NZ,PVER
        LD      HL,OPBUF
        LD      DE,TXTVERSION
        CALL    STREQ
        OR      A
        JP      NZ,PVER
        LD      HL,OPBUF
        LD      DE,TXTALLSHORT
        CALL    STREQ
        OR      A
        JP      NZ,PALLSHORT
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
PBIOS: LD      C,10
        JP      PCHECK
PCHECKOPT:
        LD      C,11
        JP      PCHECK
PMAP:  LD      C,14
        JP      PCHECK
PVER:  LD      C,15
        JP      PCHECK
PALLSHORT:
        LD      C,16
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
        JP      PARGINIT
PSPACEOPT:
        LD      A,9
        JP      PARGINIT
PDRIVES:
        LD      A,12
        JP      PARGINIT
PALLOC: LD      A,13
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

; /LOGGED is accepted only as the sole operand of a disk-set report.
PARGOPT:
        LD      A,(SELMODE)
        CP      6
        JP      Z,PLOGMODE
        CP      9
        JP      Z,PLOGMODE
        CP      12
        JP      Z,PLOGMODE
        CP      13
        JP      NZ,PBAD
PLOGMODE:
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
        JP      DISKSETUP
SPACEINFO:
        LD      A,2
        LD      (REPORTDPB),A
        JP      DISKSETUP
DRIVESINFO:
        LD      A,3
        LD      (REPORTDPB),A
        LD      HL,(DRVMASK)
        LD      A,H
        OR      L
        JP      NZ,DRIVESHEAD
        LD      A,1
        LD      (LOGFLAG),A
DRIVESHEAD:
        LD      DE,DRVHEAD
        CALL    PUTS
        JP      DISKSETUP
ALLOCINFO:
        LD      A,4
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
        LD      A,(REPORTDPB)
        CP      3
        JP      Z,SHOWDRVX
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
        CP      1
        JP      Z,SHOWDPB
        CP      2
        JP      Z,SHOWSPACE
        CP      4
        JP      Z,SHOWALLOC
        JP      SHOWDISK
SHOWDRVX:
        POP     AF
        JP      SHOWDRVROW
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

; Report capacity from the DPB and current allocation vector. Function 27
; returns the public in-memory bitmap; one set bit denotes one allocated block.
; Only DSM+1 meaningful bits are counted, so padding bits in the last byte do
; not affect the result. Values are printed in KiB to keep 16-bit arithmetic.
SHOWSPACE:
        CALL    CALCSPACE
        OR      A
        JP      Z,SPACEFAIL
        LD      DE,SPACEHEAD
        CALL    PUTS
        LD      DE,SPTOTALK
        CALL    PUTS
        LD      HL,(SPTOTAL)
        CALL    SCALEKB
        CALL    PDECEND
        LD      DE,SPUSEDK
        CALL    PUTS
        LD      HL,(SPUSED)
        CALL    SCALEKB
        CALL    PDECEND
        LD      DE,SPFREEK
        CALL    PUTS
        LD      HL,(SPFREE)
        CALL    SCALEKB
        CALL    PDECEND
        LD      DE,SPBLOCKS
        CALL    PUTS
        LD      HL,(SPTOTAL)
        CALL    DEC16
        LD      DE,SPSLASH
        CALL    PUTS
        LD      HL,(SPFREE)
        CALL    DEC16
        LD      DE,CRLF
        JP      PUTS
SPACEFAIL:
        LD      DE,SPACEUNAV
        JP      PUTS

; Calculate total, used, and free allocation blocks for the drive in CURINDEX.
; Return A=1 on success or zero when BDOS supplies no allocation vector.
CALCSPACE:
        LD      A,(CURINDEX)
        LD      E,A
        LD      C,14
        CALL    BDOS
        LD      C,27
        CALL    BDOS
        LD      (ALVPTR),HL
        LD      A,H
        OR      L
        JP      Z,CALCFAIL
        LD      HL,(DPBBUF+5)
        INC     HL
        LD      (SPTOTAL),HL
        LD      B,H
        LD      C,L
        LD      HL,(ALVPTR)
        LD      DE,0
        LD      A,080H
        LD      (SPMASK),A
SPCOUNT:
        LD      A,(SPMASK)
        AND     (HL)
        JP      Z,SPNEXT
        INC     DE
SPNEXT:DEC     BC
        LD      A,B
        OR      C
        JP      Z,SPDONE
        LD      A,(SPMASK)
        RRCA
        LD      (SPMASK),A
        JP      NC,SPCOUNT
        INC     HL
        JP      SPCOUNT
SPDONE:EX      DE,HL
        LD      (SPUSED),HL
        EX      DE,HL
        LD      A,(ORIGDRV)
        LD      E,A
        LD      C,14
        CALL    BDOS
        LD      HL,(SPUSED)
        EX      DE,HL
        LD      HL,(SPTOTAL)
        OR      A
        CALL    SUBHLDE
        LD      (SPFREE),HL
        LD      A,1
        RET
CALCFAIL:
        LD      A,(ORIGDRV)
        LD      E,A
        LD      C,14
        CALL    BDOS
        XOR     A
        RET

; Compact logged/specified-drive row. A is FETCHDPB success status.
SHOWDRVROW:
        PUSH    AF
        LD      A,(CURINDEX)
        ADD     A,'A'
        CALL    PUTCH
        LD      DE,DRVCOL
        CALL    PUTS
        POP     AF
        OR      A
        JP      Z,DRVROWBAD
        LD      A,(CURINDEX)
        LD      C,A
        LD      A,(ORIGDRV)
        CP      C
        LD      A,'C'
        JP      Z,DRVSTATE
        LD      HL,(LOGINWORK)
        LD      A,L
        AND     1
        LD      A,'L'
        JP      NZ,DRVSTATE
        LD      A,'-'
DRVSTATE:
        CALL    PUTCH
        LD      DE,DRVSEP
        CALL    PUTS
        LD      HL,(ROWORK)
        LD      A,L
        AND     1
        LD      A,'R'
        JP      NZ,DRVRO
        LD      A,'-'
DRVRO:  CALL    PUTCH
        LD      DE,DRVSEP
        CALL    PUTS
        CALL    BLOCKKB
        CALL    DEC16
        LD      DE,DRVSEP
        CALL    PUTS
        CALL    CALCSPACE
        OR      A
        JP      Z,DRVSPBAD
        LD      HL,(SPTOTAL)
        CALL    SCALEKB
        CALL    DEC16
        LD      DE,DRVSEP
        CALL    PUTS
        LD      HL,(SPUSED)
        CALL    SCALEKB
        CALL    DEC16
        LD      DE,DRVSEP
        CALL    PUTS
        LD      HL,(SPFREE)
        CALL    SCALEKB
        CALL    DEC16
        LD      DE,CRLF
        JP      PUTS
DRVROWBAD:
        LD      DE,DRVUNAV
        JP      PUTS
DRVSPBAD:
        LD      DE,DRVSPUN
        JP      PUTS

; Detailed allocation report for one drive after FETCHDPB.
SHOWALLOC:
        CALL    CALCSPACE
        OR      A
        JP      Z,ALLOCBAD
        LD      DE,ALLOCHEAD
        CALL    PUTS
        LD      DE,ALBLKBYTES
        CALL    PUTS
        LD      HL,128
        LD      A,(DPBBUF+2)
        LD      B,A
ALBSH: LD      A,B
        OR      A
        JP      Z,ALBSDONE
        ADD     HL,HL
        DEC     B
        JP      ALBSH
ALBSDONE:
        CALL    PDECEND
        LD      DE,ALTOTAL
        CALL    PUTS
        LD      HL,(SPTOTAL)
        CALL    PDECEND
        LD      DE,ALUSED
        CALL    PUTS
        LD      HL,(SPUSED)
        CALL    PDECEND
        LD      DE,ALFREE
        CALL    PUTS
        LD      HL,(SPFREE)
        CALL    PDECEND
        LD      DE,ALUSEDK
        CALL    PUTS
        LD      HL,(SPUSED)
        CALL    SCALEKB
        CALL    PDECEND
        LD      DE,ALFREEK
        CALL    PUTS
        LD      HL,(SPFREE)
        CALL    SCALEKB
        CALL    PDECEND
        LD      DE,ALVBYTES
        CALL    PUTS
        LD      HL,(SPTOTAL)
        LD      DE,7
        ADD     HL,DE
        CALL    SHRHL
        CALL    SHRHL
        CALL    SHRHL
        CALL    PDECEND
        LD      DE,ALDIRBLK
        CALL    PUTS
        CALL    COUNTDIR
        LD      L,A
        LD      H,0
        JP      PDECEND
ALLOCBAD:
        LD      DE,ALLOCUNAV
        JP      PUTS

; Return allocation-block size in KiB in HL.
BLOCKKB:
        LD      HL,1
        LD      A,(DPBBUF+2)
        SUB     3
        RET     Z
        RET     C
        LD      B,A
BLKKS: ADD     HL,HL
        DEC     B
        JP      NZ,BLKKS
        RET

; Count directory-reserved allocation blocks in AL0/AL1.
COUNTDIR:
        LD      HL,DPBBUF+9
        LD      B,2
        LD      D,0
CDNEXT:LD      A,(HL)
        LD      C,8
CDBIT: RLA
        JP      NC,CDZERO
        INC     D
CDZERO:DEC     C
        JP      NZ,CDBIT
        INC     HL
        DEC     B
        JP      NZ,CDNEXT
        LD      A,D
        RET

; Convert allocation blocks to KiB. CP/M block size is 128 << BSH bytes,
; hence blocks are multiplied by 2^(BSH-3).
SCALEKB:
        LD      A,(DPBBUF+2)
        SUB     3
        RET     Z
        RET     C
        LD      B,A
SPKSCL:ADD     HL,HL
        DEC     B
        JP      NZ,SPKSCL
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

; Decode the documented seventeen-entry CP/M 2.2 BIOS jump table. The table
; base is obtained from the page-zero warm-boot vector; each entry must be a
; three-byte JMP before its target address is displayed. No BIOS entry is
; called, so this report cannot alter device or disk state.
BIOSINFO:
        LD      DE,BIOSHEAD
        CALL    PUTS
        CALL    GETBIOS
        OR      A
        JP      Z,BIOSNONE
        LD      (BIOSPTR),HL
        PUSH    HL
        LD      DE,BIOSBASE
        CALL    PUTS
        POP     HL
        CALL    HEX16
        CALL    PUTH
        XOR     A
        LD      (BIOSIDX),A
BIOSLOOP:
        LD      A,(BIOSIDX)
        ADD     A,A
        LD      E,A
        LD      D,0
        LD      HL,BIOSTAB
        ADD     HL,DE
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        CALL    PUTZ
        LD      HL,(BIOSPTR)
        LD      A,(HL)
        CP      0C3H
        JP      NZ,BIOSBAD
        INC     HL
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      A,D
        OR      E
        JP      Z,BIOSBAD
        EX      DE,HL
        CALL    HEX16
        CALL    PUTH
        JP      BIOSNEXT
BIOSBAD:
        LD      DE,BIOSINV
        CALL    PUTS
BIOSNEXT:
        LD      HL,(BIOSPTR)
        INC     HL
        INC     HL
        INC     HL
        LD      (BIOSPTR),HL
        LD      A,(BIOSIDX)
        INC     A
        LD      (BIOSIDX),A
        CP      17
        JP      NZ,BIOSLOOP
        RET
BIOSNONE:
        LD      DE,BIOSUNAV
        JP      PUTS

; Inspect public CP/M structures without turning implementation preferences
; into compatibility claims. Broken documented vectors and tables are FAIL;
; unusual but legal address placement is WARN. No BIOS routine is executed.
CHECKINFO:
        XOR     A
        LD      (CHKPASSN),A
        LD      (CHKWARNN),A
        LD      (CHKFAILN),A
        LD      DE,CHECKHEAD
        CALL    PUTS

        LD      DE,CKWARM
        CALL    PUTS
        CALL    GETWARM
        OR      A
        JP      Z,CKWARMF
        CALL    CKPASS
        JP      CKBDOSV
CKWARMF:
        CALL    CKFAIL

CKBDOSV:LD      DE,CKBDOS
        CALL    PUTS
        CALL    GETBDOS
        OR      A
        JP      Z,CKBDOSF
        LD      (CHKBDOSA),HL
        CALL    CKPASS
        JP      CKORDER
CKBDOSF:
        CALL    CKFAIL

CKORDER:LD      DE,CKADDR
        CALL    PUTS
        CALL    GETBDOS
        OR      A
        JP      Z,CKORDERW
        LD      (CHKBDOSA),HL
        CALL    GETBIOS
        OR      A
        JP      Z,CKORDERW
        LD      (CHKBIOSA),HL
        LD      A,(CHKBDOSA+1)
        OR      A
        JP      Z,CKORDERW
        LD      HL,(CHKBDOSA)
        EX      DE,HL
        LD      HL,(CHKBIOSA)
        CALL    SUBHLDE
        JP      C,CKORDERW
        LD      A,H
        OR      L
        JP      Z,CKORDERW
        CALL    CKPASS
        JP      CKBTABLE
CKORDERW:
        CALL    CKWARN

CKBTABLE:
        LD      DE,CKBIOS
        CALL    PUTS
        CALL    GETBIOS
        OR      A
        JP      Z,CKBIOSF
        LD      B,17
CKBLOOP:LD      A,(HL)
        CP      0C3H
        JP      NZ,CKBIOSF
        INC     HL
        LD      E,(HL)
        INC     HL
        LD      D,(HL)
        LD      A,D
        OR      E
        JP      Z,CKBIOSF
        INC     HL
        DEC     B
        JP      NZ,CKBLOOP
        CALL    CKPASS
        JP      CKDPB
CKBIOSF:
        CALL    CKFAIL

CKDPB: LD      DE,CKDPBL
        CALL    PUTS
        LD      C,25
        CALL    BDOS
        LD      (ORIGDRV),A
        LD      (CURINDEX),A
        CALL    FETCHDPB
        OR      A
        JP      Z,CKDPBF
        CALL    CKPASS
        JP      CKGEOM
CKDPBF:CALL    CKFAIL
        LD      DE,CKGEOML
        CALL    PUTS
        CALL    CKFAIL
        LD      DE,CKALLOCL
        CALL    PUTS
        CALL    CKFAIL
        JP      CKSUMMARY

CKGEOM:LD      DE,CKGEOML
        CALL    PUTS
        LD      A,(DPBBUF+2)
        CP      3
        JP      C,CKGEOMF
        CP      8
        JP      NC,CKGEOMF
        LD      B,A
        LD      A,1
CKGSH: ADD     A,A
        DEC     B
        JP      NZ,CKGSH
        DEC     A
        LD      C,A
        LD      A,(DPBBUF+3)
        CP      C
        JP      NZ,CKGEOMF
        CALL    CKPASS
        JP      CKALLOC
CKGEOMF:
        CALL    CKFAIL

CKALLOC:
        LD      DE,CKALLOCL
        CALL    PUTS
        CALL    CALCSPACE
        OR      A
        JP      Z,CKALLOCF
        LD      HL,(SPUSED)
        EX      DE,HL
        LD      HL,(SPFREE)
        ADD     HL,DE
        EX      DE,HL
        LD      HL,(SPTOTAL)
        CALL    SUBHLDE
        LD      A,H
        OR      L
        JP      NZ,CKALLOCF
        CALL    CKPASS
        JP      CKSUMMARY
CKALLOCF:
        CALL    CKFAIL

CKSUMMARY:
        LD      DE,CKSUMTXT
        CALL    PUTS
        LD      A,(CHKPASSN)
        CALL    CKDEC
        LD      DE,CKPASSW
        CALL    PUTS
        LD      A,(CHKWARNN)
        CALL    CKDEC
        LD      DE,CKWARNW
        CALL    PUTS
        LD      A,(CHKFAILN)
        CALL    CKDEC
        LD      DE,CKFAILW
        JP      PUTS

CKPASS:LD      A,(CHKPASSN)
        INC     A
        LD      (CHKPASSN),A
        LD      DE,CKPASST
        CALL    PUTS
        RET
CKWARN:LD      A,(CHKWARNN)
        INC     A
        LD      (CHKWARNN),A
        LD      DE,CKWARNT
        CALL    PUTS
        RET
CKFAIL:LD      A,(CHKFAILN)
        INC     A
        LD      (CHKFAILN),A
        LD      DE,CKFAILT
        CALL    PUTS
        RET
CKDEC: LD      L,A
        LD      H,0
        JP      DEC16

; Concise public memory map. Bounds are reported only where CP/M documents a
; discoverable address; no attempt is made to guess CCP or physical RAM top.
MAPINFO:
        LD      DE,MAPHEAD
        CALL    PUTS
        LD      DE,MAPPAGE
        CALL    PUTS
        LD      DE,MAPTPA
        CALL    PUTS
        LD      HL,0100H
        CALL    HEX16
        LD      DE,RANGESEP
        CALL    PUTS
        CALL    GETBDOS
        OR      A
        JP      Z,MAPTPAUNK
        DEC     HL
        CALL    HEX16
        CALL    PUTH
        JP      MAPBDOS
MAPTPAUNK:
        LD      DE,UNKNOWN
        CALL    PUTS
MAPBDOS:
        LD      DE,MAPBDOSL
        CALL    PUTS
        CALL    GETBDOS
        CALL    PADDR
        LD      DE,MAPWARML
        CALL    PUTS
        CALL    GETWARM
        CALL    PADDR
        LD      DE,MAPBIOSL
        CALL    PUTS
        CALL    GETBIOS
        CALL    PADDR
        LD      DE,MAPDMAL
        CALL    PUTS
        LD      HL,DMADEF
        CALL    HEX16
        JP      PUTH

VERINFO:
        LD      DE,VERHEAD
        CALL    PUTS
        LD      DE,VERUTILITY
        CALL    PUTS
        LD      DE,VERCPM
        CALL    PUTS
        CALL    VERSION
        LD      DE,VERCPU
        JP      PUTS

; Short overview deliberately omits detailed jump, DPB, allocation, and check
; tables. It combines the existing system summary, public state, and compact
; logged-drive inventory.
SHORTINFO:
        CALL    SUMMARY
        CALL    STATEINFO
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        LD      (LOGFLAG),A
        JP      DRIVESINFO

ALLINFO:
        CALL    SUMMARY
        CALL    STATEINFO
        CALL    MEMORY
        CALL    IOINFO
        CALL    VECTORS
        CALL    BIOSINFO
        CALL    CHECKINFO
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        LD      (LOGFLAG),A
        CALL    DISKINFO
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        CALL    DPBINFO
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        CALL    SPACEINFO
        XOR     A
        LD      (DRVMASK),A
        LD      (DRVMASK+1),A
        JP      ALLOCINFO

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
TXTSPACE:DB 'SPACE',0
TXTBIOS:DB 'BIOS',0
TXTCHECK:DB 'CHECK',0
TXTDRIVES:DB 'DRIVES',0
TXTALLOC:DB 'ALLOC',0
TXTMAP: DB 'MAP',0
TXTVER: DB 'VER',0
TXTVERSION:DB 'VERSION',0
TXTALLSHORT:DB 'ALL:SHORT',0
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
        DB '  /BIOS     Display the standard BIOS jump table',13,10
        DB '  /CHECK    Audit public CP/M structures without changing state',13,10
        DB '  /STATE    Display current drive/user and public drive vectors',13,10
        DB '  /DISK [drives]  Display disk summaries; default is current',13,10
        DB '  /DISK /LOGGED   Display summaries for logged-in drives',13,10
        DB '  /DPB [drives]   Display raw/decoded disk parameter blocks',13,10
        DB '  /SPACE [drives] Display total, used, and free disk space',13,10
        DB '  /SPACE /LOGGED  Display space for logged-in drives',13,10
        DB '  /DRIVES [drives] Compact drive inventory; default is logged',13,10
        DB '  /ALLOC [drives]  Display allocation details; default is current',13,10
        DB '  /ALLOC /LOGGED   Display allocation for logged-in drives',13,10
        DB '  /MAP      Display a concise public memory map',13,10
        DB '  /VER      Display utility and CP/M versions (/VERSION also)',13,10
        DB '  /ALL:SHORT  Display a compact system and drive overview',13,10
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

SPACEHEAD:DB 'Space:',13,10,'$'
SPACEUNAV:DB 'Space:',13,10,'  Allocation vector unavailable',13,10,'$'
SPTOTALK:DB '  Total KiB:              ','$'
SPUSEDK: DB '  Used KiB:               ','$'
SPFREEK: DB '  Free KiB:               ','$'
SPBLOCKS:DB '  Total/free blocks:      ','$'
SPSLASH: DB ' / ','$'

DRVHEAD:DB 13,10,'Drive Inventory',13,10
        DB 'Drive St RO BlkK TotalK UsedK FreeK',13,10
        DB '----- -- -- ---- ------ ----- -----',13,10,'$'
DRVCOL: DB ':  ','$'
DRVSEP: DB '  ','$'
DRVUNAV:DB 'unavailable',13,10,'$'
DRVSPUN:DB 'space unavailable',13,10,'$'

ALLOCHEAD:DB 'Allocation:',13,10,'$'
ALLOCUNAV:DB 'Allocation:',13,10,'  Allocation vector unavailable',13,10,'$'
ALBLKBYTES:DB '  Block bytes:             ','$'
ALTOTAL:DB '  Total blocks:            ','$'
ALUSED: DB '  Allocated blocks:        ','$'
ALFREE: DB '  Free blocks:             ','$'
ALUSEDK:DB '  Allocated KiB:           ','$'
ALFREEK:DB '  Free KiB:                ','$'
ALVBYTES:DB '  Allocation-vector bytes: ','$'
ALDIRBLK:DB '  Directory blocks:        ','$'

MAPHEAD:DB 13,10,'CP/M Public Memory Map',13,10,'$'
MAPPAGE:DB '  Page zero:       0000h-00FFh',13,10,'$'
MAPTPA: DB '  TPA:             ','$'
MAPBDOSL:DB '  BDOS entry:      ','$'
MAPWARML:DB '  Warm-boot target: ','$'
MAPBIOSL:DB '  BIOS table:      ','$'
MAPDMAL:DB '  Default DMA:     ','$'
RANGESEP:DB 'h-','$'

VERHEAD:DB 13,10,'SYSINFO Version Report',13,10,'$'
VERUTILITY:DB '  Utility:         1.0.0-dev7',13,10,'$'
VERCPM: DB '  CP/M:            ','$'
VERCPU: DB '  Processor floor: Intel 8080',13,10,'$'

BIOSHEAD:DB 13,10,'Standard CP/M 2.2 BIOS Jump Table',13,10,'$'
BIOSBASE:DB '  Table base: ','$'
BIOSINV: DB 'Invalid jump',13,10,'$'
BIOSUNAV:DB '  Unavailable: warm-boot vector is not a valid JMP',13,10,'$'
BBOOT:  DB '  BOOT:    ',0
BWBOOT: DB '  WBOOT:   ',0
BCONST: DB '  CONST:   ',0
BCONIN: DB '  CONIN:   ',0
BCONOUT:DB '  CONOUT:  ',0
BLIST:  DB '  LIST:    ',0
BPUNCH: DB '  PUNCH:   ',0
BREADER:DB '  READER:  ',0
BHOME:  DB '  HOME:    ',0
BSELDSK:DB '  SELDSK:  ',0
BSETTRK:DB '  SETTRK:  ',0
BSETSEC:DB '  SETSEC:  ',0
BSETDMA:DB '  SETDMA:  ',0
BREAD:  DB '  READ:    ',0
BWRITE: DB '  WRITE:   ',0
BLISTST:DB '  LISTST:  ',0
BSECTRAN:DB '  SECTRAN: ',0
BIOSTAB:DW BBOOT,BWBOOT,BCONST,BCONIN,BCONOUT,BLIST,BPUNCH,BREADER
        DW BHOME,BSELDSK,BSETTRK,BSETSEC,BSETDMA,BREAD,BWRITE,BLISTST
        DW BSECTRAN

CHECKHEAD:DB 13,10,'CP/M Structural Health Check',13,10,'$'
CKWARM: DB '  Page-zero warm-boot vector: ','$'
CKBDOS: DB '  Page-zero BDOS vector:      ','$'
CKADDR: DB '  BDOS/BIOS address order:    ','$'
CKBIOS: DB '  BIOS jump table (17):       ','$'
CKDPBL: DB '  Current-drive DPB:          ','$'
CKGEOML:DB '  DPB block geometry:         ','$'
CKALLOCL:DB '  Allocation accounting:      ','$'
CKPASST:DB 'PASS',13,10,'$'
CKWARNT:DB 'WARN',13,10,'$'
CKFAILT:DB 'FAIL',13,10,'$'
CKSUMTXT:DB 'Summary: ','$'
CKPASSW:DB ' pass, ','$'
CKWARNW:DB ' warn, ','$'
CKFAILW:DB ' fail',13,10,'$'

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
ALVPTR: DW 0
SPTOTAL:DW 0
SPUSED: DW 0
SPFREE: DW 0
SPMASK: DB 0
BIOSPTR:DW 0
BIOSIDX:DB 0
CHKPASSN:DB 0
CHKWARNN:DB 0
CHKFAILN:DB 0
CHKBDOSA:DW 0
CHKBIOSA:DW 0
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
