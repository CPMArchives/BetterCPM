; SEARCH read-only traversal engine. Requires parser/selector/matcher modules.
; RRUN: configured DU_MAP / FS_FCB / FS_MASK and matcher patterns; calls BDOS.
; Resets eight-byte totals. Preserves entry drive/user; resets DMA to 0080h.
; Consumer owns its entry stack and must validate the whole command first.
; Native directory order, one scan per logical DU/name, constant storage.
; Directory traversal is replayed after file I/O (ordinary BDOS has no saved
; search cursor API). Earlier entries are checked by canonical name so extents
; do not duplicate scans. Quadratic directory work is an explicit initial cost.
; RHOOK callback sees RWHY: 1 opened file, 2 occurrence, 3 error, 4 file ended.
; RDRIVE/RUSER and RFILE identify file; RERROR identifies an error (see below).
; For occurrence, SRESULT and matcher start/line fields are current. Hook must
; not issue BDOS file/directory operations or mutate engine state. It may output
; console data; saved registers/flags protect scan accounting from the renderer.
; RRUN returns CF set iff RINCOMP nonzero; observed totals always available.
; Error codes: 1 location, 2 directory status, 3 open, 4 reserved, 5 read,
; 6 close, 7 numeric overflow. Errors are events, never normal EOF.
RRUN:
        LD C,25
        CALL RBDOS
        LD (ROLDDRV),A
        LD E,255
        LD C,32
        CALL RBDOS
        LD (ROLDUSR),A
        LD HL,RCOUNTS
        LD DE,RCOUNTS+1
        LD BC,RCOUNTEN-RCOUNTS-1
        LD (HL),0
        LDIR
        XOR A
        LD (RINCOMP),A
        LD HL,0
        LD (RDUINDEX),HL
RDU:
        LD BC,(RDUINDEX)
        CALL DU_NEXT
        JP C,RDONE
        LD (RDUINDEX),BC
        LD A,D
        LD (RDRIVE),A
        LD A,E
        LD (RUSER),A
        LD E,D
        LD C,14
        CALL RBDOS
        LD C,25
        CALL RBDOS
        LD B,A
        LD A,(RDRIVE)
        CP B
        JR NZ,RBADLOC
        LD A,(RUSER)
        LD E,A
        LD C,32
        CALL RBDOS
        LD E,255
        CALL RBDOS
        LD B,A
        LD A,(RUSER)
        CP B
        JR NZ,RBADLOC
        LD HL,RINDEX
        CALL RZERO4
RFILELOOP:
        CALL RGET
        JP C,RDU
        ; RGET leaves copied physical directory entry in RCAND.
        CALL RDUP
        JP C,RDU
        LD A,(RDUPL)
        OR A
        JR NZ,RADVANCE
        CALL RATTR
        OR A
        JR Z,RADVANCE
        CALL RSCAN
RADVANCE:
        LD HL,RINDEX
        CALL SINC32
        JR NC,RFILELOOP
        LD A,7
        CALL RFAIL
        JP RDU
RBADLOC:
        LD A,1
        CALL RFAIL
        JP RDU
RDONE:
        LD A,(ROLDDRV)
        LD E,A
        LD C,14
        CALL RBDOS
        LD A,(ROLDUSR)
        LD E,A
        LD C,32
        CALL RBDOS
        LD DE,0080H
        LD C,26
        CALL RBDOS
        LD A,(RINCOMP)
        OR A
        RET Z
        SCF
        RET
; Start a fresh physical directory search, private FCB/DMA every time.
RFIRST:
        LD HL,FS_FCB
        LD DE,RDIRFCB
        LD BC,36
        LDIR
        LD A,(RDRIVE)
        INC A
        LD (RDIRFCB),A
        LD A,'?'
        LD (RDIRFCB+12),A
        LD DE,RDIRDMA
        LD C,26
        CALL RBDOS
        LD DE,RDIRFCB
        LD C,17
        CALL RBDOS
        RET
RNEXT:
        LD DE,RDIRFCB
        LD C,18
        JP RBDOS
; Directory status -> HL entry, CF set on EOF or error. FF is documented EOF;
; stock BDOS cannot expose a directory I/O error that it converts to FF.
RDIRENT:
        CP 255
        JR Z,REOF
        CP 4
        JR NC,RBADDIR
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        ADD A,A
        LD L,A
        LD H,0
        LD DE,RDIRDMA
        ADD HL,DE
        OR A
        RET
RBADDIR:
        LD A,2
        CALL RFAIL
REOF:
        SCF
        RET
; Find the RINDEX-th physical matching entry from a fresh enumeration.
RGET:
        LD HL,RINDEX
        LD DE,RLEFT
        CALL RCOPY4
        CALL RFIRST
RGETLOOP:
        CALL RDIRENT
        RET C
        PUSH HL
        LD HL,RLEFT
        CALL RNZ4
        POP HL
        JR Z,RGETCOPY
        LD HL,RLEFT
        CALL RDEC4
        CALL RNEXT
        JR RGETLOOP
RGETCOPY:
        LD DE,RCAND
        LD BC,32
        LDIR
        OR A
        RET
; Any previous physical entry with the same canonical name makes a duplicate.
RDUP:
        XOR A
        LD (RDUPL),A
        LD HL,RINDEX
        CALL RNZ4
        RET Z
        LD DE,RLEFT
        CALL RCOPY4
        CALL RFIRST
RDUPLOOP:
        CALL RDIRENT
        JR C,RDUPFAIL
        INC HL
        LD DE,RCAND+1
        LD B,11
RDUPNAME:
        LD A,(DE)
        AND 127
        LD C,A
        LD A,(HL)
        AND 127
        CP C
        JR NZ,RDUPNEXT
        INC HL
        INC DE
        DJNZ RDUPNAME
        ; A prior extent suppresses this one only if it also passed the
        ; shared predicate. Attribute bits can differ on damaged/old media.
        LD DE,-3
        ADD HL,DE
        CALL RATTRH
        OR A
        JR Z,RDUPNEXT
        LD A,1
        LD (RDUPL),A
        OR A
        RET
RDUPNEXT:
        LD HL,RLEFT
        CALL RDEC4
        CALL RNZ4
        RET Z
        CALL RNEXT
        JR RDUPLOOP
RDUPFAIL:
        ; Unexpected EOF during replay means coverage cannot be established.
        ; Other directory status failures were already reported by RDIRENT.
        CP 255
        JR NZ,RDUPRET
        LD A,2
        CALL RFAIL
RDUPRET:
        SCF
        RET
; Apply shared attribute truth mask to candidate extension bits RO/SYS/ARC.
RATTR:
        LD HL,RCAND+9
RATTRH:
        LD B,3
        LD C,0
        LD E,1
RATTRBIT:
        LD A,(HL)
        AND 128
        JR Z,RATTRNXT
        LD A,C
        OR E
        LD C,A
RATTRNXT:
        LD A,E
        ADD A,A
        LD E,A
        INC HL
        DJNZ RATTRBIT
        LD B,C
        INC B
        LD A,(FS_MASK)
RATTRROT:
        RRCA
        DJNZ RATTRROT
        AND 128
        RET
RSCAN:
        ; Build a private concrete FCB; strip attribute high bits from names.
        LD HL,RFILE
        LD B,36
        XOR A
RFILECLR:
        LD (HL),A
        INC HL
        DJNZ RFILECLR
        LD A,(RDRIVE)
        INC A
        LD (RFILE),A
        LD HL,RCAND+1
        LD DE,RFILE+1
        LD B,11
RFILENAME:
        LD A,(HL)
        AND 127
        LD (DE),A
        INC HL
        INC DE
        DJNZ RFILENAME
        LD DE,RFILE
        LD C,15
        CALL RBDOS
        CP 255
        JR NZ,ROPENED
        LD A,3
        JP RFAIL
ROPENED:
        LD HL,RFILES
        CALL RINC8
        CALL SRESET
        XOR A
        LD (RHASMAT),A
        LD A,1
        CALL RNOTIFY
        LD DE,RFILE
        LD C,35
        CALL RBDOS
        ; CP/M 2.2 function 35 returns its result only in R0..R2.
        ; A is unspecified (DRI can return FFh on success), not an error flag.
RSIZED:
        LD HL,RFILE+33
        LD DE,RRECORDS
        LD BC,3
        LDIR
        XOR A
        LD (RRECORDS+3),A
        LD HL,RRECORD
        CALL RZERO4
RREAD:
        LD HL,RRECORDS
        CALL RNZ4
        JP Z,RCLOSE
        LD HL,RRECORD
        LD DE,RFILE+33
        LD BC,3
        LDIR
        LD DE,RDATA
        LD C,26
        CALL RBDOS
        LD DE,RFILE
        LD C,33
        CALL RBDOS
        OR A
        JR Z,RRECORDOK
        ; Even normal EOF here is early relative to the established record
        ; count, and therefore incomplete; never reuse stale DMA contents.
        LD A,5
        CALL RFAIL
        JP RCLOSE
RRECORDOK:
        LD HL,RDATA
        LD (RBYTEPTR),HL
        LD A,128
        LD (RBYTES),A
RBYTE:
        LD HL,(RBYTEPTR)
        LD A,(HL)
        INC HL
        LD (RBYTEPTR),HL
        CALL SFEED
        JR NC,RMATCHES
        LD A,7
        CALL RFAIL
        JP RCLOSE
RMATCHES:
        LD A,(SRESULT)
        OR A
        JR Z,RBYTENXT
        LD A,(RHASMAT)
        OR A
        JR NZ,RKNOWN
        LD HL,RMATCHED
        CALL RINC8
        LD A,1
        LD (RHASMAT),A
RKNOWN:
        LD A,(SRESULT)
        AND 1
        JR Z,RCHECKHX
        LD HL,RTEXT
        CALL RINC8
        LD HL,RTOTAL
        CALL RINC8
RCHECKHX:
        LD A,(SRESULT)
        AND 2
        JR Z,RREPORT
        LD HL,RHEX
        CALL RINC8
        LD HL,RTOTAL
        CALL RINC8
RREPORT:
        LD A,2
        CALL RNOTIFY
RBYTENXT:
        LD A,(RBYTES)
        DEC A
        LD (RBYTES),A
        JR NZ,RBYTE
        LD HL,RRECORD
        CALL SINC32
        LD HL,RRECORDS
        CALL RDEC4
        JP RREAD
RCLOSE:
        LD DE,RFILE
        LD C,16
        CALL RBDOS
        CP 255
        JR NZ,RFILEEND
        LD A,6
        CALL RFAIL
RFILEEND:
        LD A,4
        JP RNOTIFY
RFAIL:
        LD (RERROR),A
        LD A,1
        LD (RINCOMP),A
        LD A,3
        JP RNOTIFY
RNOTIFY:
        LD (RWHY),A
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        CALL RHOOK
        POP IX
        POP HL
        POP DE
        POP BC
        POP AF
        RET
RBDOS:
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        CALL 5
        POP IX
        POP HL
        POP DE
        POP BC
        RET
RINC8:
        LD B,8
RINCLOOP:
        INC (HL)
        RET NZ
        INC HL
        DJNZ RINCLOOP
        ; Saturate at max, latch a coverage/accounting error; never show a
        ; wrapped plausible small total. Caller must qualify the summary.
        DEC HL
        LD B,8
        LD A,255
RSAT:
        LD (HL),A
        DEC HL
        DJNZ RSAT
        LD A,7
        JP RFAIL
RCOPY4:
        PUSH HL
        LD BC,4
        LDIR
        POP HL
        RET
RZERO4:
        LD B,4
        XOR A
RZERO:
        LD (HL),A
        INC HL
        DJNZ RZERO
        RET
RNZ4:
        LD B,4
        XOR A
        PUSH HL
RNZ:
        OR (HL)
        INC HL
        DJNZ RNZ
        POP HL
        RET
RDEC4:
        LD B,4
        PUSH HL
RDEC:
        LD A,(HL)
        DEC (HL)
        OR A
        JR NZ,RDECDONE
        INC HL
        DJNZ RDEC
RDECDONE:
        POP HL
        RET
ROLDDRV: DB 0
ROLDUSR: DB 0
RDRIVE: DB 0
RUSER: DB 0
RINCOMP: DB 0
RERROR: DB 0
RWHY: DB 0
RDUPL: DB 0
RHASMAT: DB 0
RDUINDEX: DW 0
RINDEX: DS 4
RLEFT: DS 4
RRECORD: DS 4
RRECORDS: DS 4
RBYTEPTR: DW 0
RBYTES: DB 0
RCOUNTS:
RFILES: DS 8
RMATCHED: DS 8
RTEXT: DS 8
RHEX: DS 8
RTOTAL: DS 8
RCOUNTEN:
RDIRFCB: DS 36
RDIRDMA: DS 128
RCAND: DS 32
RFILE: DS 36
RDATA: DS 128
