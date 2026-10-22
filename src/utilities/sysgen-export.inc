; Disk-to-package header construction. Payload is preserved byte-for-byte.
; Names and filesystem publication are separate from these pure buffer helpers.
XHEADER:
        LD HL,PKGHEADER
        LD DE,PKGHEADER+1
        LD BC,127
        XOR A
        LD (HL),A
        LDIR
        LD HL,PKGMAGIC
        LD DE,PKGHEADER
        LD BC,10
        LDIR
        CALL FINDDESC
        RET NZ
        PUSH HL
        LD DE,MAGIC
        LD B,8
        CALL XCMP
        POP HL
        RET NZ
        LD DE,10
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD DE,16
        ADD HL,DE
        JR C,XBAD
; The saved A: binding must lie wholly inside the 52-record resident carrier.
        PUSH HL
        LD DE,SYSBASE
        OR A
        SBC HL,DE
        JR C,XBOUND
        LD DE,52*128-64+1
        OR A
        SBC HL,DE
        JR NC,XBOUND
        POP HL
        CALL ABSTOIMG
        LD DE,PKGHEADER+16
        LD BC,64
        LDIR
; A structurally valid package must describe sufficient reserved system space.
        LD BC,(PKGHEADER+17)
        LD DE,(PKGHEADER+30)
        CALL RESCOUNT
        JR C,XBAD
        LD DE,SYSRECS
        OR A
        SBC HL,DE
        JR C,XBAD
; Compare normalized boot geometry with the binding used for actual reads.
; The on-disk binding, not live unsaved settings, owns package metadata.
        LD HL,PKGHEADER+16
        LD DE,EXPECT
        LD BC,64
        LDIR
        LD HL,SOURCE
        LD DE,TARGET
        LD BC,64
        LDIR
        LD HL,EXPECT
        CALL XNORM
        LD HL,TARGET
        CALL XNORM
        LD HL,EXPECT+16
        LD DE,TARGET+16
        LD B,45
        JP XCMP
XBOUND: POP HL
XBAD:  LD A,1
        OR A
        RET
; Equality comparison; zero on full match, nonzero on difference.
XCMP:  LD A,(DE)
        CP (HL)
        RET NZ
        INC DE
        INC HL
        DJNZ XCMP
        XOR A
        RET
; Normalize a private binding from cylinder to surface-track notation.
XNORM: PUSH HL
        LD DE,19
        ADD HL,DE
        LD A,(HL)
        AND 020H
        JR Z,XNEND
        LD A,(HL)
        AND 0DFH
        OR 040H
        LD (HL),A
        POP HL
        PUSH HL
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        SRL D
        RR E
        LD (HL),D
        DEC HL
        LD (HL),E
        LD DE,13
        ADD HL,DE
        SLA (HL)
        INC HL
        RL (HL)
XNEND: POP HL
        RET

; Publication uses fixed reserved recovery names in the output drive/user.
; Never delete a pre-existing recovery file or roll back a failed rename:
; a disk error can have changed only some directory extents. Preserve evidence.
XEXPORTGO:
        CALL READSOURCE
        JR Z,XREADOK
        LD (STATUS),A
        JP SOURCEBAD
XREADOK:CALL XHEADER
        JP NZ,PKGBAD
        LD A,(XARG2)
        OR A
        JR NZ,XDRIVE
        LD C,25
        CALL BDOS
        INC A
        LD (XARG2),A
XDRIVE:LD (XTEMP),A
        LD (XBACK),A
        LD HL,XARG2+1
        LD DE,XTEMP+1
        LD B,11
        CALL XCMP
        JP Z,XRESERVED
        LD HL,XARG2+1
        LD DE,XBACK+1
        LD B,11
        CALL XCMP
        JP Z,XRESERVED
        LD DE,XTEMP
        CALL XPROBE
        CP 1
        JP NZ,XRECOVERY
        LD DE,XBACK
        CALL XPROBE
        CP 1
        JP NZ,XRECOVERY
        LD DE,XARG2
        CALL XPROBE
        CP 2
        JP Z,XFAIL
        OR A
        JR NZ,XCREATE
        LD A,(XARG2+9)
        LD B,A
        LD A,(XARG2+10)
        OR B
        AND 080H
        JP NZ,XPROTECTED
        LD A,1
        LD (XOLD),A
        LD HL,XREPLACE
        CALL PUTS
        CALL SG_ASK
        CP 'Y'
        JP NZ,0
XCREATE:
        LD DE,XTEMP
        CALL XRESET
        LD C,22
        CALL BDOS
        INC A
        JP Z,XFAIL
        LD A,1
        LD (XCREATED),A
        LD HL,0
        LD (XINDEX),HL
XWRLOOP:
        CALL BREAKCK
        JP Z,XABORT
        CALL XRECPTR
        LD C,26
        CALL BDOS
        LD DE,XTEMP
        LD C,21
        CALL BDOS
        OR A
        JP NZ,XINCOMPLETE
        CALL XNEXT
        JR C,XWRLOOP
        LD DE,XTEMP
        LD C,16
        CALL BDOS
        INC A
        JP Z,XINCOMPLETE
        LD DE,XTEMP
        CALL XVERIFY
        JP NZ,XINCOMPLETE
; From this point retain verified/recovery files on failure. No automatic
; rollback after rename failure: directory updates are not an atomic exchange.
        XOR A
        LD (XCREATED),A
        LD A,(XOLD)
        OR A
        JR Z,XPUBLISH
        LD HL,XARG2
        LD DE,XBACK
        CALL XRENAME
        JP NZ,XRENAMEBAD
XPUBLISH:
        LD HL,XTEMP
        LD DE,XARG2
        CALL XRENAME
        JP NZ,XRENAMEBAD
        LD DE,XARG2
        CALL XVERIFY
        JP NZ,XRENAMEBAD
        LD A,(XOLD)
        OR A
        JR Z,XDONE
        LD DE,XBACK
        CALL XRESET
        LD C,19
        CALL BDOS
        INC A
        JR Z,XBACKLEFT
XDONE: LD HL,XCOMPLETE
        JP REPORT
XBACKLEFT:
        LD HL,XLEFTMSG
        JP REPORT
XRENAMEBAD:
        LD HL,XRENMSG
        JP REPORT
XABORT:LD HL,XSTOPMSG
        LD (XERROR),HL
        JR XCLEAN
XINCOMPLETE:
        LD HL,XFAILMSG
        LD (XERROR),HL
XCLEAN:LD A,(XCREATED)
        OR A
        JR Z,XFAIL
        LD DE,XTEMP
        LD C,16
        CALL BDOS
        LD DE,XTEMP
        CALL XRESET
        LD C,19
        CALL BDOS
        INC A
        JR Z,XCLEANBAD
        LD HL,(XERROR)
        JP REPORT
XCLEANBAD:
        LD HL,XCLEANMSG
        JP REPORT
XFAIL: LD HL,XFAILMSG
        JP REPORT
XRECOVERY:
        LD HL,XRECMSG
        JP REPORT
XPROTECTED:
        LD HL,XPROTMSG
        JP REPORT
XRESERVED:
        LD HL,XRESMSG
        JP REPORT

; Clear private FCB state while preserving its exact drive/name.
XRESET:PUSH DE
        EX DE,HL
        LD DE,12
        ADD HL,DE
        LD B,24
        XOR A
XRLOOP:LD (HL),A
        INC HL
        DJNZ XRLOOP
        POP DE
        RET
; Return 0 exists (closed), 1 absent, 2 close failed. No creation/deletion.
XPROBE:LD (XFILE),DE
        CALL XRESET
        LD C,15
        CALL BDOS
        INC A
        JR Z,XABSENT
        LD DE,(XFILE)
        LD C,16
        CALL BDOS
        INC A
        JR Z,XPROBEERR
        XOR A
        RET
XABSENT:LD A,1
        OR A
        RET
XPROBEERR:LD A,2
        OR A
        RET
; XINDEX 0 is header; 1..160 are unmodified protected-system records.
XRECPTR:
        LD HL,(XINDEX)
        LD A,H
        OR L
        LD DE,PKGHEADER
        RET Z
        DEC HL
        JP IMAGEPTR
XNEXT: LD HL,(XINDEX)
        INC HL
        LD (XINDEX),HL
        LD DE,SYSRECS+1
        OR A
        SBC HL,DE
        RET
; Reopen and compare header/payload, require immediate EOF, then checked close.
XVERIFY:
        LD (XFILE),DE
        CALL XRESET
        LD C,15
        CALL BDOS
        INC A
        JP Z,XBAD
        LD HL,0
        LD (XINDEX),HL
XVLOOP:LD DE,VERIFY
        LD C,26
        CALL BDOS
        LD DE,(XFILE)
        LD C,20
        CALL BDOS
        OR A
        JR NZ,XVCLOSEBAD
        CALL XRECPTR
        EX DE,HL
        LD DE,VERIFY
        LD B,128
        CALL XCMP
        JR NZ,XVCLOSEBAD
        CALL XNEXT
        JR C,XVLOOP
        LD DE,(XFILE)
        LD C,20
        CALL BDOS
        CP 1
        JR NZ,XVCLOSEBAD
        LD DE,(XFILE)
        LD C,16
        CALL BDOS
        INC A
        JP Z,XBAD
        XOR A
        RET
XVCLOSEBAD:
        LD DE,(XFILE)
        LD C,16
        CALL BDOS
        JP XBAD
; HL old, DE new exact private FCBs; build the standard 32-byte rename request.
XRENAME:
        LD (XNEW),DE
        PUSH HL
        LD HL,XRENFCB
        LD DE,XRENFCB+1
        LD BC,35
        XOR A
        LD (HL),A
        LDIR
        POP HL
        LD DE,XRENFCB
        LD BC,12
        LDIR
        LD HL,(XNEW)
        LD DE,XRENFCB+16
        LD BC,12
        LDIR
        LD DE,XRENFCB
        LD C,23
        CALL BDOS
        INC A
        JP Z,XBAD
        XOR A
        RET
XTEMP: DB 0,'SYSGEN  $$$'
        DS 24
XBACK: DB 0,'SYSGEN  BAK'
        DS 24
XRENFCB:DS 36
XOLD: DB 0
XCREATED:DB 0
XINDEX:DW 0
XFILE: DW 0
XNEW: DW 0
XERROR:DW 0
XREPLACE:DB 'Replace existing package (Y/N)? ',0
XCOMPLETE:DB 13,10,'Package exported and verified.',13,10,0
XLEFTMSG:DB 13,10,'Package exported and verified. Previous package retained as SYSGEN.BAK.',13,10,0
XRENMSG:DB 13,10,'Package publication failed. Files retained; inspect output, SYSGEN.$$$ and SYSGEN.BAK.',13,10,0
XFAILMSG:DB 13,10,'Package export failed. No completed package published.',13,10,0
XSTOPMSG:DB 13,10,'Package export stopped. No completed package published.',13,10,0
XRECMSG:DB 13,10,'Recovery file exists or cannot be checked: SYSGEN.$$$ or SYSGEN.BAK.',13,10,0
XPROTMSG:DB 13,10,'Existing package is protected. No replacement made.',13,10,0
XRESMSG:DB 13,10,'SYSGEN.$$$ and SYSGEN.BAK are reserved recovery names.',13,10,0
XCLEANMSG:DB 13,10,'Export failed; incomplete SYSGEN.$$$ could not be removed.',13,10,0

XLOWMEM:LD HL,XMEMMSG
        JP REPORT
XMEMMSG:DB 13,10,'SYSGEN needs 36K of transient memory.',13,10,0
