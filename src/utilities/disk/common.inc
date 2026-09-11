; DISK UTILITY COMMON ROUTINES -- 07-Sep-2026
; All system work goes through BDOS. No TRS-80 addresses live here.
; Private buffers: 4000-7FFF FDF text, 8000-A7FF write-track stream.
; Keep the program below 3E00; the private stack ends at 4000.
BDOS    EQU 5
FDFRAM  EQU 04000H
FDFLIM  EQU 07F80H
TRACKBF EQU 08000H
TRKLIM  EQU 0A800H

; Preserve loop registers across console calls. Strings end in zero.
PUTC:   PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD C,2
        CALL BDOS
        POP HL
        POP DE
        POP BC
        POP AF
        RET
PUTS:   LD A,(HL)
        INC HL
        OR A
        RET Z
        CALL PUTC
        JR PUTS
CRLF:   LD A,13
        CALL PUTC
        LD A,10
        JP PUTC
KEY:    LD C,6
        LD E,0FFH
        CALL BDOS
        OR A
        JR Z,KEY
        CP 'a'
        RET C
        CP 'z'+1
        RET NC
        AND 05FH
        RET
PAUSE:  LD HL,WAITMSG
        CALL PUTS
        CALL KEY
        RET
; HL = heading. One inverse row, then a blank row.
HEADER: PUSH HL
        LD A,28
        CALL PUTC
        POP HL
        LD B,79
HEADLP: LD A,(HL)
        OR A
        JR Z,HEADSP
        INC HL
        JR HEADCH
HEADSP: LD A,' '
HEADCH: CALL INVERSE
        DJNZ HEADLP
        CALL CRLF
        JP CRLF
; Optional inverse output falls back to plain text on other consoles.
INVERSE:PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        LD E,A
        LD A,(HASREV)
        OR A
        JR Z,INVPLAIN
        LD C,204
        JR INVCALL
INVPLAIN:LD C,2
INVCALL:CALL BDOS
        POP HL
        POP DE
        POP BC
        POP AF
        RET
CHOICE: LD HL,CHMSG
        CALL PUTS
        LD A,' '
        CALL INVERSE
        LD A,']'
        CALL PUTC
        CALL KEY
        PUSH AF
        LD A,13
        CALL PUTC
        LD HL,CHMSG
        CALL PUTS
        POP AF
        PUSH AF
        CALL PUTC
        LD A,']'
        CALL PUTC
        CALL CRLF
        POP AF
        RET
; A = unsigned byte, decimal output, suppress leading zeroes.
DECOUT: LD C,0
        LD B,100
        CALL DECDIG
        LD B,10
        CALL DECDIG
        ADD A,'0'
        JP PUTC
DECDIG: LD D,'0'
DECLP:  CP B
        JR C,DECDONE
        SUB B
        INC D
        JR DECLP
DECDONE:PUSH AF
        LD A,D
        CP '0'
        JR NZ,DECSHOW
        LD A,C
        OR A
        JR Z,DECSKIP
        LD A,D
DECSHOW:CALL PUTC
        LD C,1
DECSKIP:POP AF
        RET
; A menu ordinal -> [ A ] prefix. Preserve ordinal in A.
LABEL:  PUSH AF
        LD HL,LBRACK
        CALL PUTS
        POP AF
        PUSH AF
        ADD A,'A'
        CALL PUTC
        LD HL,RBRACK
        CALL PUTS
        POP AF
        RET
; Read an unsigned byte. ENTER accepts the original value in OLDVAL.
; Carry means cancel/invalid. Input uses function 6, so ^C is ours.
NUMBER: XOR A
        LD (NUMVAL),A
        LD (NDIGIT),A
NUMLP:  CALL KEY
        CP 3
        JR Z,NUMBAD
        CP 13
        JR Z,NUMEND
        CP '0'
        JR C,NUMLP
        CP '9'+1
        JR NC,NUMLP
        LD (DIGIT),A
        SUB '0'
        LD E,A
        LD D,0
        LD A,(NUMVAL)
        LD L,A
        LD H,0
        ADD HL,HL
        LD B,H
        LD C,L
        ADD HL,HL
        ADD HL,HL
        ADD HL,BC
        ADD HL,DE
        LD A,H
        OR A
        JR NZ,NUMBAD
        LD A,L
        LD (NUMVAL),A
        LD A,1
        LD (NDIGIT),A
        LD A,(DIGIT)
        CALL PUTC
        JR NUMLP
NUMEND: CALL CRLF
        LD A,(NDIGIT)
        OR A
        LD A,(NUMVAL)
        RET NZ
        LD A,(OLDVAL)
        OR A
        RET
NUMBAD: SCF
        RET
; API is deliberately independent of the loaded BIOS address.
; B = operation, DE = 80-byte request, A/Z = result.
API:    LD C,207
        CALL BDOS
        LD A,L
        OR A
        RET
INIT:   LD HL,(6)
        LD DE,0A880H
        OR A
        SBC HL,DE
        JP C,SMALL
        LD B,0
        CALL API
        LD DE,MAGIC
        LD B,8
CHKABI: LD A,(DE)
        CP (HL)
        JP NZ,BADABI
        INC DE
        INC HL
        DJNZ CHKABI
        LD C,204
        LD E,0
        CALL BDOS
        LD (HASREV),A
        RET
SMALL:  LD HL,SMALLMSG
        JR FATAL
BADABI: LD HL,ABIMSG
FATAL:  CALL PUTS
        CALL PAUSE
        JP 0
ERROR:  LD HL,ERRMSG
        CALL PUTS
        JP PAUSE
DONE:   JP 0

; Read DISK.FDF on the current drive, with A: as the fallback.
; A bounded RAM copy permits paging both ways without reopening the disk.
FLOAD:  LD HL,BUILTINS
        LD DE,FDFRAM
        LD BC,BUILTINEND-BUILTINS
        LDIR
        LD (FPOS),DE
  LD HL,FDFCB+12
        LD DE,FDFCB+13
        LD BC,23
        LD (HL),0
        LDIR                    ; DS bytes are not guaranteed to start at zero
        LD DE,FDFCB
        LD C,15
        CALL BDOS
        CP 0FFH
        JR NZ,FOPEN
        LD A,1
        LD (FDFCB),A
        LD DE,FDFCB
        LD C,15
        CALL BDOS
        CP 0FFH
        JP Z,FMISSING
FOPEN:  LD HL,(FPOS)
FREAD:  LD (FPOS),HL
        EX DE,HL
        LD C,26
        CALL BDOS
        LD DE,FDFCB
        LD C,20
        CALL BDOS
        CP 1
        JR Z,FEND
        OR A
        JP NZ,FBAD
        LD HL,(FPOS)
        LD DE,128
        ADD HL,DE
        LD DE,FDFLIM
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JR C,FREAD
        JP FBAD
FEND:   LD HL,(FPOS)
        LD (HL),26
        LD (FSTOP),HL
        LD DE,FDFCB
        LD C,16
        CALL BDOS
        LD DE,80H
        LD C,26
        CALL BDOS
        XOR A
        LD (FCOUNT),A
        LD HL,FDFRAM
        LD DE,FINDEX
; Only '*' at the start of a line introduces a definition.
FSCAN:  LD A,(HL)
        CP 26
        JR Z,FREADY
        CP '*'
        JR NZ,FNEXT
        LD A,(FCOUNT)
        CP 128
        JP NC,FBAD
        INC A
        LD (FCOUNT),A
        INC HL
        LD A,L
        LD (DE),A
        INC DE
        LD A,H
        LD (DE),A
        INC DE
FNEXT:  LD A,(HL)
        CP 26
        JR Z,FREADY
        INC HL
        CP 10
        JR NZ,FNEXT
        JR FSCAN
FREADY: LD A,(FCOUNT)
        OR A
        JP Z,FBAD
        RET
FMISSING:JP FEND       ; the assembled MM definitions need no FDF file
FBAD:   LD HL,FBADMSG
        JP FATAL
; A = catalogue index -> HL = descriptive name.
FNAME:  LD L,A
        LD H,0
        ADD HL,HL
        LD DE,FINDEX
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        RET
; Print one name, capped at 72 columns (no newline required in string).
PNAME:  LD B,72
PNAMEL: LD A,(HL)
        CP 13
        RET Z
        CP 10
        RET Z
        CP 26
        RET Z
        CALL PUTC
        INC HL
        DJNZ PNAMEL
        RET
; Parse one selected definition into BIND. Carry means malformed data.
; Width table follows the standard DPB, then the four FDF extensions.
FPARSE: CALL FNAME
FSKIP:  LD A,(HL)
        CP 26
        JP Z,PBAD
        INC HL
        CP 10
        JR NZ,FSKIP
        LD (PARPTR),HL
        LD HL,BIND
        LD DE,BIND+1
        LD BC,63
        LD (HL),0
        LDIR
        LD IX,BIND+1
        LD IY,WIDTHS
        LD B,14
PLOOP:  PUSH BC
        CALL PNUM
        POP BC
        RET C
        LD (IX+0),E
        INC IX
        LD A,(IY+0)
        INC IY
        CP 2
        JR Z,PWORD
        LD A,D
        OR A
        JP NZ,PBAD
        JR PNEXT
PWORD:  LD (IX+0),D
        INC IX
PNEXT:  DJNZ PLOOP
; FDF tail order is sectors,size,cylinders,flags, binding uses cyl,sec,size.
        LD A,(BIND+16)
        LD C,A
        LD A,(BIND+18)
        LD (BIND+16),A
        LD A,(BIND+17)
        LD (BIND+18),A
        LD A,C
        LD (BIND+17),A
        OR A
        JP Z,PBAD
        CP 33
        JP NC,PBAD
        LD B,A
        LD IX,BIND+20
PSKEW:  PUSH BC
        CALL PNUM
        POP BC
        RET C
        LD A,D
        OR A
        JP NZ,PBAD
        LD (IX+0),E
        INC IX
        DJNZ PSKEW
        OR A
        RET
; Decimal word scanner. Carry on overflow, bad delimiter, or premature EOF.
PNUM:   LD HL,(PARPTR)
PSPACE: LD A,(HL)
        CP ' '
        JR Z,PSINC
        CP 13
        JR Z,PSINC
        CP 10
        JR NZ,PSTART
PSINC:  INC HL
        JR PSPACE
PSTART: LD DE,0
        LD C,0
PDIG:   LD A,(HL)
        CP '0'
        JR C,PDELIM
        CP '9'+1
        JR NC,PDELIM
        SUB '0'
        PUSH HL
        PUSH AF
        EX DE,HL
        ADD HL,HL
        JP C,POVER
        LD D,H
        LD E,L
        ADD HL,HL
        JP C,POVER
        ADD HL,HL
        JP C,POVER
        ADD HL,DE
        JP C,POVER
        POP AF
        LD E,A
        LD D,0
        ADD HL,DE
        EX DE,HL
        POP HL
        JP C,PBAD
        INC HL
        LD C,1
        JR PDIG
POVER:  POP AF
        POP HL
        JP PBAD
PDELIM: LD A,C
        OR A
        JR Z,PBAD
        LD A,(HL)
        CP ','
        JR Z,POK
        CP 13
        JR Z,POK
        CP 10
        JR NZ,PBAD
POK:    INC HL
        LD (PARPTR),HL
        OR A
        RET
PBAD:   SCF
        RET

; Show the current binding's name if it occurs in the catalogue.
; CURB is kept separate because FPARSE uses BIND as scratch.
CURNAME:LD A,(CURB)
        CP 0FFH
        JP Z,CUNDEF
        XOR A
        LD (FINDIDX),A
CUFIND: LD A,(FINDIDX)
        CALL FPARSE
        JR C,CUNEXT
        LD HL,CURB+1
        LD DE,BIND+1
        LD B,63
CURAW:  LD A,(DE)
        CP (HL)
        JR NZ,CUNORM
        INC HL
        INC DE
        DJNZ CURAW
        JR CUFOUND
; The old SUPER entries have no size map in CONFIG's catalogue. FDF adds
; one when the drive is hooked up. Ask it to make the same pencilled-in
; copy after the ordinary comparison has failed. Most formats need no
; mapper at all and must keep matching their original catalogue record.
CUNORM: LD C,208
        LD B,0
        CALL BDOS
        LD A,H
        CP 046H
        JR NZ,CUNEXT
        LD A,L
        CP 044H
        JR NZ,CUNEXT
; Service 208 takes the setter's 80-byte request, one byte ahead of a bare
; catalogue binding. Make a dummy request rather than handing it a pointer
; with all the old MM fields shifted one place to the left.
        XOR A
        LD (REQ),A
        LD HL,BIND
        LD DE,REQ+1
        LD BC,64
        LDIR
        LD DE,REQ
        LD IX,REQ              ; extended validator shares the BIOS setter ABI
        LD C,208
        LD B,2
        CALL BDOS
        LD A,H
        CP 046H
        JR NZ,CUNEXT
        LD A,L
        CP 044H
        JR NZ,CUNEXT
CUCOMPARE:
        LD HL,CURB+1
        LD DE,REQ+2
        LD B,63
CUCMP:  LD A,(DE)
        CP (HL)
        JR NZ,CUNEXT
        INC HL
        INC DE
        DJNZ CUCMP
CUFOUND:
        LD A,(FINDIDX)
        CALL FNAME
        JP PNAME
CUNEXT: LD A,(FINDIDX)
        INC A
        LD (FINDIDX),A
        LD B,A
        LD A,(FCOUNT)
        CP B
        JR NZ,CUFIND
        LD HL,CUSTOM
        JP PUTS
CUNDEF: LD HL,UNDEF
        JP PUTS
WAITMSG:DB 13,10,'Push ENTER for menu.',0
CHMSG:  DB 'Your choice: [',0
LBRACK: DB '[ ',0
RBRACK: DB ' ] ',0
ERRMSG: DB 'Invalid or unsupported setting; no change made.',13,10,0
ABIMSG: DB 'Requires BetterCP/M disk BIOS ABI 5 (four drives).',13,10,0
SMALLMSG:DB 'Not enough transient memory (42K required).',13,10,0
FNOMSG: DB 'Cannot open DISK.FDF on current drive or A:.',13,10,0
FBADMSG:DB 'DISK.FDF is empty, unreadable or too large.',13,10,0
MAGIC:  DB 'BDCF',5,4,4,64
CUSTOM: DB 'Current BIOS format (not listed in format catalogue)',0
UNDEF:  DB 'Undefined disk drive',0
WIDTHS: DB 2,1,1,1,2,2,1,1,2,2,1,1,1,1
FDFCB:  DB 0,'DISK    FDF'
        DS 24
FCOUNT: DB 0
FPOS:   DW 0
FSTOP:  DW 0
PARPTR: DW 0
FINDIDX:DB 0
FINDEX: DS 256
BIND:   DS 64
CURB:   DS 64
REQ:    DS 80
PHREQ:  DS 80
OLDVAL: DB 0
NUMVAL: DB 0
NDIGIT: DB 0
DIGIT:  DB 0

HASREV: DB 0

        INCLUDE disk/builtins.inc
