; First DRI fast-copy transaction: one exact disk source, named/drive destination.
; Supported effective parameters G/O/R/V/W. Others fail before any file I/O.
PT_COPY:
        XOR A
        LD (PT_SRCOPEN),A
        LD (PT_CREATED),A
        LD (PT_TOPEN),A
        LD HL,PT_RR
        LD (HL),A
        INC HL
        LD (HL),A
        INC HL
        LD (HL),A
        LD A,(PP_COUNT)
        CP 2
        JP NZ,PT_UNSUP
        LD A,(OP_DATA+80)
        CP 2
        JP NZ,PT_UNSUP
        LD A,(OP_DATA+84)
        OR A
        JP NZ,PT_UNSUP
        LD A,(OP_DATA)
        CP 4
        JP Z,PT_UNSUP
        LD A,(OP_DATA+2)
        CP 4
        JP NC,PT_DRIVEERR
        LD A,(OP_DATA+82)
        CP 4
        JP NC,PT_DRIVEERR
        LD HL,OP_DATA+124
        LD B,26
        LD C,0
PT_OPTIONS:
        LD A,(HL)
        OR A
        JR Z,PT_ONEXT
        LD A,C
        CP 6
        JR Z,PT_ONEXT
        CP 14
        JR Z,PT_ONEXT
        CP 17
        JR Z,PT_ONEXT
        CP 21
        JR Z,PT_ONEXT
        CP 22
        JP NZ,PT_UNSUP
PT_ONEXT:
        INC HL
        INC C
        DJNZ PT_OPTIONS
        LD HL,OP_DATA+88
        LD DE,PT_SFCB
        LD BC,36
        LDIR
        LD HL,OP_DATA+8
        LD DE,PT_DFCB
        LD BC,36
        LDIR
        LD A,(OP_DATA)
        CP 3
        JR NZ,PT_DNAMED
        LD HL,PT_SFCB+1
        LD DE,PT_DFCB+1
        LD BC,11
        LDIR
PT_DNAMED:
        LD HL,PT_DFCB
        LD DE,PT_TFCB
        LD BC,36
        LDIR
        LD HL,PT_TFCB+9
        LD (HL),'$'
        INC HL
        LD (HL),'$'
        INC HL
        LD (HL),'$'
        ; The staging name must not be the intended destination itself.
        LD HL,PT_DFCB+1
        LD DE,PT_TFCB+1
        CALL PT_EQUAL
        JP Z,PT_IDENT
        LD A,(OP_DATA+2)
        LD HL,OP_DATA+82
        CP (HL)
        JR NZ,PT_PREFLIGHT
        LD A,(OP_DATA+3)
        INC HL
        CP (HL)
        JR NZ,PT_PREFLIGHT
        LD HL,PT_DFCB+1
        LD DE,PT_SFCB+1
        CALL PT_EQUAL
        JP Z,PT_IDENT
        LD HL,PT_TFCB+1
        LD DE,PT_SFCB+1
        CALL PT_EQUAL
        JP Z,PT_IDENT
PT_PREFLIGHT:
        CALL PT_SOURCE
        LD DE,PT_SFCB
        LD C,15
        CALL 5
        CP 0FFH
        JP Z,PT_NOFILE
        LD A,1
        LD (PT_SRCOPEN),A
        LD A,(PT_SFCB+10)
        AND 80H
        JR Z,PT_TARGET
        LD A,(OP_DATA+141)
        OR A
        JP Z,PT_NOFILE
PT_TARGET:
        CALL PT_DEST
        LD C,29
        CALL 5
        LD A,(OP_DATA+2)
        LD B,A
        INC B
PT_RODRIVE:
        LD A,L
        RRCA
        LD L,A
        DJNZ PT_RODRIVE
        AND 80H
        JP NZ,PT_READONLY
        ; Remove an old writable staging file, but never override its RO flag.
        LD DE,PT_TFCB
        LD C,15
        CALL 5
        CP 0FFH
        JR Z,PT_MAKE
        LD A,(PT_TFCB+9)
        AND 80H
        JP NZ,PT_TEMPERR
        LD DE,PT_TFCB
        LD C,19
        CALL 5
        CP 0FFH
        JP Z,PT_TEMPERR
PT_MAKE:
        LD HL,PT_TFCB+1
        LD B,11
PT_TCLEAR:
        LD A,(HL)
        AND 7FH
        LD (HL),A
        INC HL
        DJNZ PT_TCLEAR
        LD HL,PT_TFCB+12
        LD B,24
        XOR A
PT_TZERO:
        LD (HL),A
        INC HL
        DJNZ PT_TZERO
        LD DE,PT_TFCB
        LD C,22
        CALL 5
        CP 0FFH
        JP Z,PT_NOSPACE
        LD A,1
        LD (PT_CREATED),A
        LD (PT_TOPEN),A
PT_LOOP:
        CALL PT_SOURCE
        LD DE,PT_DATA
        LD C,26
        CALL 5
        LD DE,PT_SFCB
        LD C,20
        CALL 5
        CP 1
        JP Z,PT_EOF
        OR A
        JP NZ,PT_READERR
        CALL PT_DEST
        LD DE,PT_DATA
        LD C,26
        CALL 5
        LD DE,PT_TFCB
        LD C,21
        CALL 5
        OR A
        JP NZ,PT_WRITEERR
        LD A,(OP_DATA+145)
        OR A
        JR Z,PT_ADVANCE
        LD HL,PT_TFCB
        LD DE,PT_VFCB
        LD BC,36
        LDIR
        LD HL,PT_RR
        LD DE,PT_VFCB+33
        LD BC,3
        LDIR
        LD DE,PT_VBUF
        LD C,26
        CALL 5
        LD DE,PT_VFCB
        LD C,33
        CALL 5
        OR A
        JP NZ,PT_VERIFYERR
        LD HL,PT_DATA
        LD DE,PT_VBUF
        LD B,128
PT_COMPARE:
        LD A,(DE)
        CP (HL)
        JP NZ,PT_VERIFYERR
        INC HL
        INC DE
        DJNZ PT_COMPARE
PT_ADVANCE:
        LD HL,PT_RR
        INC (HL)
        JP NZ,PT_LOOP
        INC HL
        INC (HL)
        JP NZ,PT_LOOP
        INC HL
        INC (HL)
        JP NZ,PT_LOOP
        JP PT_READERR
PT_EOF:
        LD DE,PT_SFCB
        LD C,16
        CALL 5
        XOR A
        LD (PT_SRCOPEN),A
        CALL PT_DEST
        ; DRI direct copies preserve SFUB (unused bytes in the last record).
        LD A,(PT_SFCB+13)
        LD (PT_TFCB+13),A
        LD DE,PT_TFCB
        LD C,16
        CALL 5
        CP 0FFH
        JP Z,PT_CLOSEERR
        XOR A
        LD (PT_TOPEN),A
        ; Old destination survives until transfer, verification and close succeed.
        LD DE,PT_DFCB
        LD C,15
        CALL 5
        CP 0FFH
        JR Z,PT_INSTALL
        LD A,(PT_DFCB+9)
        AND 80H
        JR Z,PT_DELETE
        LD A,(OP_DATA+146)
        OR A
        JR NZ,PT_CLEARRO
        LD DE,PT_ASK
        LD C,9
        CALL 5
        LD C,1
        CALL 5
        AND 0DFH
        CP 'Y'
        JR Z,PT_CLEARRO
        LD DE,PT_NOTDEL
        CALL PT_PRINT
        JP PT_CLEAN
PT_CLEARRO:
        LD HL,PT_DFCB+9
        RES 7,(HL)
        LD DE,PT_DFCB
        LD C,30
        CALL 5
        CP 0FFH
        JP Z,PT_REPLACEERR
PT_DELETE:
        LD DE,PT_DFCB
        LD C,19
        CALL 5
        CP 0FFH
        JP Z,PT_REPLACEERR
PT_INSTALL:
        LD HL,PT_DFCB
        LD DE,PT_TFCB+16
        LD BC,12
        LDIR
        LD DE,PT_TFCB
        LD C,23
        CALL 5
        CP 0FFH
        JP Z,PT_RENAMEERR
        XOR A
        LD (PT_CREATED),A
        JP PT_CLEAN
PT_SOURCE:
        LD A,(OP_DATA+82)
        LD D,A
        LD A,(OP_DATA+83)
        JR PT_SETDU
PT_DEST:
        LD A,(OP_DATA+2)
        LD D,A
        LD A,(OP_DATA+3)
PT_SETDU:
        PUSH AF
        LD E,D
        LD C,14
        CALL 5
        POP AF
        LD E,A
        LD C,32
        JP 5
PT_EQUAL:
        LD B,11
PT_EQLOOP:
        LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DJNZ PT_EQLOOP
        RET
PT_UNSUP:
        LD DE,P_DEVM
        JP P_ERROR
PT_IDENT:
        LD DE,PT_IDMSG
        JP P_ERROR
PT_DRIVEERR:
        LD DE,PT_DRM
        JP P_ERROR
PT_NOFILE:
        LD DE,PT_NOMSG
        JR PT_FAIL
PT_READONLY:
        LD DE,PT_ROMSG
        JR PT_FAIL
PT_TEMPERR:
        LD DE,PT_TMPMSG
        JR PT_FAIL
PT_NOSPACE:
        LD DE,PT_SPMSG
        JR PT_FAIL
PT_READERR:
        LD DE,PT_RDMSG
        JR PT_FAIL
PT_WRITEERR:
        LD DE,PT_WRMSG
        JR PT_FAIL
PT_VERIFYERR:
        LD DE,PT_VMSG
        JR PT_FAIL
PT_CLOSEERR:
        LD DE,PT_CMSG
        JR PT_FAIL
PT_REPLACEERR:
        LD DE,PT_REPLMSG
        JR PT_FAIL
PT_RENAMEERR:
        ; Retain the completed staging file after final-name installation fails.
        XOR A
        LD (PT_CREATED),A
        LD DE,PT_RENMSG
PT_FAIL:
        CALL PT_PRINT
        CALL P_CANCEL
PT_CLEAN:
        LD A,(PT_SRCOPEN)
        OR A
        JR Z,PT_CT
        CALL PT_SOURCE
        LD DE,PT_SFCB
        LD C,16
        CALL 5
PT_CT:
        LD A,(PT_CREATED)
        OR A
        JR Z,PT_RESTORE
        CALL PT_DEST
        LD A,(PT_TOPEN)
        OR A
        JR Z,PT_REMOVE
        LD DE,PT_TFCB
        LD C,16
        CALL 5
PT_REMOVE:
        LD DE,PT_TFCB
        LD C,19
        CALL 5
        CP 0FFH
        JR NZ,PT_RESTORE
        LD DE,PT_KEEPMSG
        CALL PT_PRINT
PT_RESTORE:
        LD A,(P_DRIVE)
        LD E,A
        LD C,14
        CALL 5
        LD A,(P_USER)
        LD E,A
        LD C,32
        CALL 5
        LD DE,0080H
        LD C,26
        JP 5
PT_PRINT:
        LD C,9
        JP 5
PT_SRCOPEN: DB 0
PT_CREATED: DB 0
PT_TOPEN: DB 0
PT_RR: DS 3
PT_SFCB: DS 36
PT_DFCB: DS 36
PT_TFCB: DS 36
PT_VFCB: DS 36
PT_DATA: DS 128
PT_VBUF: DS 128
PT_DRM: DB 'INVALID DRIVE',13,10,'$'
PT_IDMSG: DB 'INVALID FORMAT: source/destination staging-name conflict.',13,10,'$'
PT_NOMSG: DB 'NO FILE',13,10,'$'
PT_ROMSG: DB 'DESTINATION DRIVE IS R/O',13,10,'$'
PT_TMPMSG: DB 'CANNOT REMOVE TEMPORARY FILE',13,10,'$'
PT_SPMSG: DB 'NO DIRECTORY SPACE',13,10,'$'
PT_RDMSG: DB 'DISK READ ERROR',13,10,'$'
PT_WRMSG: DB 'DISK WRITE ERROR',13,10,'$'
PT_VMSG: DB 'VERIFY ERROR',13,10,'$'
PT_CMSG: DB 'CANNOT CLOSE DESTINATION FILE',13,10,'$'
PT_REPLMSG: DB 'CANNOT REPLACE DESTINATION FILE',13,10,'$'
PT_RENMSG: DB 'CANNOT RENAME TEMPORARY FILE',13,10,'$'
PT_ASK: DB 'DESTINATION IS R/O, DELETE (Y/N)?$'
PT_NOTDEL: DB 13,10,'**NOT DELETED**',13,10,'$'
PT_KEEPMSG: DB 'CLEANUP FAILED: temporary file remains.',13,10,'$'
