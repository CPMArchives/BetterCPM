; Result renderer. 79 printable columns, 23 content rows; no terminal backend.
; First TEXT occurrence on a line chooses its one bounded excerpt. All matcher
; events still contribute to counts; HEX rows are independent. Rereads use a
; cloned FCB/private DMA and restore scan DMA before returning to the engine.
RHOOK:
        LD A,(RWHY)
        CP 1
        JR Z,DNEWFILE
        CP 3
        JP Z,DERROR
        CP 2
        RET NZ
        XOR A
        LD (DOUTPUT),A
        CALL DPOLL
        LD A,(DSUPP)
        OR A
        RET NZ
        LD A,(SRESULT)
        AND 1
        CALL NZ,DTEXTROW
        LD A,(SRESULT)
        AND 2
        CALL NZ,DHEXROW
        RET
DNEWFILE:
        LD HL,DLAST
        JP RZERO4
DTEXTROW:
        LD HL,STLINE
        LD DE,DLAST
        CALL DCMP4
        RET Z
        CALL RCOPY4
        LD HL,RFILE
        LD DE,DFCB
        LD BC,36
        LDIR
        XOR A
        LD (DCACHE),A
        LD HL,STSTART
        LD DE,DPOS
        CALL RCOPY4
        ; Preserve a CR immediately before a match beginning on paired LF.
        CALL DGET
        RET C
        CP 10
        LD A,0
        JR NZ,DLFINIT
        INC A
DLFINIT:
        LD (DSKIPCR),A
        LD A,64
        LD (DBACK),A
        XOR A
        LD (DLEFT),A
DBACKUP:
        LD HL,DPOS
        CALL RNZ4
        JR Z,DBACKEND
        CALL RDEC4
        CALL DGET
        RET C
        LD B,A
        LD A,(DSKIPCR)
        LD C,A
        XOR A
        LD (DSKIPCR),A
        LD A,B
        CP 13
        JR NZ,DBACKLF
        LD A,C
        OR A
        JR NZ,DBACKUP
        JR DBACKBRK
DBACKLF:
        CP 10
        JR Z,DBACKBRK
DBACKMORE:
        LD A,(DBACK)
        DEC A
        LD (DBACK),A
        JR NZ,DBACKUP
        LD HL,DPOS
        CALL RNZ4
        JR Z,DBACKEND
        LD A,1
        LD (DLEFT),A
        JR DBACKEND
DBACKBRK:
        LD HL,DPOS
        CALL SINC32
DBACKEND:
        LD HL,STSTART
        LD DE,DEND
        CALL RCOPY4
        LD A,(STLEN)
        LD B,A
DENDADD:
        LD HL,DEND
        PUSH BC
        CALL SINC32
        POP BC
        DJNZ DENDADD
        CALL DNAME
        LD HL,DTAGTEXT
        CALL DTEXT
        LD HL,STLINE
        LD DE,DLINEVAL
        CALL RCOPY4
        XOR A
        LD (DLINEVAL+4),A
        LD (DLINEVAL+5),A
        LD (DLINEVAL+6),A
        LD (DLINEVAL+7),A
        LD HL,DLINEVAL
        CALL DDECIMAL
        LD HL,DCOLON
        CALL DTEXT
        LD A,(DLEFT)
        OR A
        LD HL,DELLIP
        CALL NZ,DTEXT
        LD A,192
        LD (DBUDGET),A
DEXCERPT:
        LD A,(DSUPP)
        OR A
        RET NZ
        CALL DGET
        JR C,DEXEND
        LD (DBYTE),A
        ; A terminator within the actual pattern remains visible data.
        LD HL,DPOS
        LD DE,DEND
        CALL DCMP4
        JR C,DEXPRINT
        LD A,(DBYTE)
        CP 13
        JR Z,DEXEND
        CP 10
        JR Z,DEXEND
DEXPRINT:
        LD A,(DBYTE)
        CALL DSHOW
        LD HL,DPOS
        CALL SINC32
        LD A,(DBYTE)
        CP 13
        JR Z,DEXTERM
        CP 10
        JR NZ,DEXBUDG
DEXTERM:
        LD HL,DPOS
        LD DE,DEND
        CALL DCMP4
        JR NC,DEXEND
DEXBUDG:
        LD A,(DBUDGET)
        DEC A
        LD (DBUDGET),A
        JR NZ,DEXCERPT
        ; Mark only an actually omitted edge, not EOF or the next line.
        CALL DGET
        JR C,DEXEND
        CP 13
        JR Z,DEXEND
        CP 10
        JR Z,DEXEND
        LD HL,DELLIP
        CALL DTEXT
DEXEND:
        JP DLINE
DHEXROW:
        LD A,(DSUPP)
        OR A
        RET NZ
        CALL DNAME
        LD HL,DTAGHEX
        CALL DTEXT
        LD HL,SHSTART
        CALL DHEX32
        JP DLINE
; Absolute byte access via a cloned open FCB. Carry: EOF or read failure;
; EOF does not create data. Read failures emit essential errors and mark the
; aggregate scan incomplete. The main matcher and random-record cursor stay intact.
DGET:
        LD A,(DPOS)
        RLCA
        AND 1
        LD C,A
        LD HL,(DPOS+1)
        LD A,(DPOS+3)
        ADD HL,HL
        RLA
        LD (DFCB+35),A
        LD A,L
        OR C
        LD (DFCB+33),A
        LD A,H
        LD (DFCB+34),A
        LD HL,DFCB+35
        LD DE,RFILELEN+2
        LD B,3
DGETLIM:
        LD A,(DE)
        CP (HL)
        JR C,DGETEOF
        JR NZ,DGETOK
        DEC DE
        DEC HL
        DJNZ DGETLIM
DGETEOF:
        SCF
        RET
DGETOK:
        LD A,(DCACHE)
        OR A
        JR Z,DGETREAD
        LD HL,DFCB+33
        LD DE,DCACHED
        LD B,3
DGETCMP:
        LD A,(DE)
        CP (HL)
        JR NZ,DGETREAD
        INC HL
        INC DE
        DJNZ DGETCMP
        JR DGETBYTE
DGETREAD:
        LD DE,DBUF
        LD C,26
        CALL RBDOS
        LD DE,DFCB
        LD C,33
        CALL RBDOS
        PUSH AF
        LD DE,RDATA
        LD C,26
        CALL RBDOS
        POP AF
        OR A
        JR NZ,DGETERR
        LD HL,DFCB+33
        LD DE,DCACHED
        LD BC,3
        LDIR
        LD A,1
        LD (DCACHE),A
DGETBYTE:
        LD A,(DPOS)
        AND 127
        LD E,A
        LD D,0
        LD HL,DBUF
        ADD HL,DE
        LD A,(HL)
        OR A
        RET
DGETERR:
        XOR A
        LD (DCACHE),A
        LD A,1
        LD (DREADERR),A
        LD A,5
        CALL RFAIL
        XOR A
        LD (DREADERR),A
        SCF
        RET
; Unsigned little-endian four-byte comparison HL versus DE, pointers preserved.
DCMP4:
        PUSH HL
        PUSH DE
        LD BC,3
        ADD HL,BC
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD B,4
DCMPLOOP:
        LD A,(DE)
        LD C,A
        LD A,(HL)
        CP C
        JR NZ,DCMPDONE
        DEC HL
        DEC DE
        DJNZ DCMPLOOP
DCMPDONE:
        POP DE
        POP HL
        RET
DSHOW:
        CP 32
        JR C,DSHOWHEX
        CP 127
        JP C,DPRINT
DSHOWHEX:
        PUSH AF
        LD A,'<'
        CALL DPRINT
        POP AF
        CALL DHEX8
        LD A,'>'
        JP DPRINT
DNAME:
        CALL DDU
        LD HL,RFILE+1
        LD B,8
        CALL DFIELD
        LD HL,RFILE+9
        LD A,(HL)
        CP ' '
        RET Z
        LD A,'.'
        CALL DPRINT
        LD B,3
        JP DFIELD
DDU:
        LD A,(RDRIVE)
        ADD A,'A'
        CALL DPRINT
        LD A,(RUSER)
        LD B,0
DUSERTEN:
        CP 10
        JR C,DUSERONE
        SUB 10
        INC B
        JR DUSERTEN
DUSERONE:
        PUSH AF
        LD A,B
        OR A
        JR Z,DUSERLOW
        ADD A,'0'
        CALL DPRINT
DUSERLOW:
        POP AF
        ADD A,'0'
        CALL DPRINT
        LD A,':'
        JP DPRINT
DFIELD:
        LD A,(HL)
        CP ' '
        CALL NZ,DSHOW
        INC HL
        DJNZ DFIELD
        RET
DERROR:
        LD A,(DOUTPUT)
        PUSH AF
        LD A,1
        LD (DOUTPUT),A
        LD HL,DERRMSG
        CALL DTEXT
        LD A,(RERROR)
        CP 3
        JR C,DERRDU
        CALL DNAME
        JR DERRLABEL
DERRDU:
        CALL DDU
DERRLABEL:
        LD A,(RERROR)
        ADD A,A
        LD E,A
        LD D,0
        LD HL,DERRTAB
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        CALL DTEXT
        LD A,(RERROR)
        CP 5
        JR Z,DERRPOS
        CP 7
        JR NZ,DERRDONE
DERRPOS:
        LD HL,DERRAT
        CALL DTEXT
        LD HL,SPOS
        LD A,(DREADERR)
        OR A
        JR Z,DERRHEX
        LD HL,DPOS
DERRHEX:
        CALL DHEX32
DERRDONE:
        CALL DLINE
        POP AF
        LD (DOUTPUT),A
        RET
DSUMMARY:
        LD A,1
        LD (DOUTPUT),A
        XOR A
        LD (PPAGED),A
        LD HL,RFILES
        LD DE,DFILESMSG
        CALL DSTAT
        LD HL,RMATCHED
        LD DE,DMATCHMSG
        CALL DSTAT
        LD HL,RTEXT
        LD DE,DTEXTMSG
        CALL DSTAT
        LD HL,RHEX
        LD DE,DHEXMSG
        CALL DSTAT
        LD HL,RTOTAL
        LD DE,DTOTALMSG
        CALL DSTAT
        LD A,(RINCOMP)
        OR A
        RET Z
        LD HL,DINCOMPL
        JP DTEXT
DSTAT:
        PUSH HL
        EX DE,HL
        CALL DTEXT
        POP HL
        CALL DDECIMAL
        JP DLINE
DDECIMAL:
        LD DE,DNUM
        LD BC,8
        LDIR
        LD HL,DNUMBUF+20
        LD (HL),0
DDECOUT:
        PUSH HL
        LD HL,DNUM+7
        LD B,8
        LD D,0
DDECBYTE:
        LD E,(HL)
        PUSH HL
        LD H,D
        LD L,E
        LD DE,10
        LD C,0
DDECDIV:
        OR A
        SBC HL,DE
        JR C,DDECEND
        INC C
        JR DDECDIV
DDECEND:
        ADD HL,DE
        LD D,L
        POP HL
        LD (HL),C
        DEC HL
        DJNZ DDECBYTE
        POP HL
        DEC HL
        LD A,D
        ADD A,'0'
        LD (HL),A
        PUSH HL
        LD HL,DNUM
        LD B,8
        XOR A
DDECNZ:
        OR (HL)
        INC HL
        DJNZ DDECNZ
        POP HL
        JR NZ,DDECOUT
        JP DTEXT
DHEX32:
        LD BC,3
        ADD HL,BC
        LD B,4
DHEXLOOP:
        LD A,(HL)
        CALL DHEX8
        DEC HL
        DJNZ DHEXLOOP
        RET
DHEX8:
        PUSH AF
        RRCA
        RRCA
        RRCA
        RRCA
        CALL DHEX4
        POP AF
DHEX4:
        AND 15
        ADD A,'0'
        CP '9'+1
        JR C,DHEXDONE
        ADD A,7
DHEXDONE:
        JP DPRINT
DTEXT:
        LD A,(HL)
        OR A
        RET Z
        CP 13
        JR Z,DTEXTCR
        CP 10
        JR Z,DTEXTLF
        CALL DPRINT
        INC HL
        JR DTEXT
DTEXTCR:
        INC HL
        JR DTEXT
DTEXTLF:
        CALL DLINE
        INC HL
        JR DTEXT
DPRINT:
        PUSH AF
        LD A,(DOUTPUT)
        OR A
        JR NZ,DPRINTGO
        LD A,(DSUPP)
        OR A
        JR NZ,DPRINTNO
DPRINTGO:
        LD A,(DCOL)
        CP 79
        CALL NC,DLINE
        LD A,(DOUTPUT)
        OR A
        JR NZ,DPRINTYES
        LD A,(DSUPP)
        OR A
        JR NZ,DPRINTNO
DPRINTYES:
        POP AF
        CALL DPUT
        PUSH AF
        LD A,(DCOL)
        INC A
        LD (DCOL),A
DPRINTNO:
        POP AF
        RET
DPUT:
        PUSH AF
        PUSH BC
        PUSH DE
        LD E,A
        LD C,6
        CALL RBDOS
        POP DE
        POP BC
        POP AF
        RET
DLINE:
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        CALL DLINE1
        POP HL
        POP DE
        POP BC
        POP AF
        RET
DLINE1:
        LD A,(DOUTPUT)
        OR A
        JR NZ,DLINEGO
        LD A,(DSUPP)
        OR A
        RET NZ
DLINEGO:
        LD A,13
        CALL DPUT
        LD A,10
        CALL DPUT
        XOR A
        LD (DCOL),A
        LD A,(DOUTPUT)
        OR A
        RET NZ
        LD A,(PPAGED)
        OR A
        RET Z
        LD A,(DROWS)
        INC A
        LD (DROWS),A
        CP 23
        RET C
        LD A,1
        LD (DOUTPUT),A
        LD HL,DPROMPT
        CALL DTEXT
DWAIT:
        LD E,255
        LD C,6
        CALL RBDOS
        CP 3
        JP Z,DSTOP
        CP ' '
        JR Z,DPAGE
        CP 13
        JR NZ,DWAIT
DPAGE:
        CALL DLINE
        XOR A
        LD (DROWS),A
        LD (DOUTPUT),A
        RET
DPOLL:
        LD A,(DSUPP)
        OR A
        RET NZ
        LD A,(PPAGED)
        OR A
        RET NZ
        LD C,11
        CALL RBDOS
        OR A
        RET Z
        LD E,255
        LD C,6
        CALL RBDOS
        CP 3
        RET NZ
DSTOP:
        LD A,1
        LD (DSUPP),A
        LD (DOUTPUT),A
        XOR A
        LD (PPAGED),A
        CALL DLINE
        LD HL,DSTOPMSG
        CALL DTEXT
        XOR A
        LD (DOUTPUT),A
        RET
DBADMSG: DB 'SEARCH: Invalid command.',13,10,0
DUSAGE: DB 'Usage: SEARCH [options] "pattern" filespec [options]',13,10
        DB 'Use SEARCH /HELP for help.',13,10,0
DTAGTEXT: DB ' [TEXT] line ',0
DTAGHEX: DB ' [HEX] offset ',0
DCOLON: DB ': ',0
DELLIP: DB '[...]',0
DERRMSG: DB 'SEARCH: ',0
DERRTAB: DW DERRUNK,DERRLOC,DERRDIR,DERROPEN,DERRUNK,DERRREAD,DERRCLOS,DERROVER
DERRUNK: DB ' Unknown error',0
DERRLOC: DB ' Location unavailable',0
DERRDIR: DB ' Directory search failed',0
DERROPEN: DB ' Cannot open file',0
DERRREAD: DB ' Read error',0
DERRCLOS: DB ' Cannot close file',0
DERROVER: DB ' Numeric overflow',0
DERRAT: DB ' at offset ',0
DFILESMSG: DB 'Files searched: ',0
DMATCHMSG: DB 'Files matched: ',0
DTEXTMSG: DB 'Text matches: ',0
DHEXMSG: DB 'Hex matches: ',0
DTOTALMSG: DB 'Total matches: ',0
DINCOMPL: DB 'Search incomplete; totals cover successfully searched data only.',13,10,0
DPROMPT: DB 'Space/Enter: next page; Ctrl-C: stop display',0
DSTOPMSG: DB 'DISPLAY INTERRUPTED',13,10,'SEARCH CONTINUING...',13,10,0
