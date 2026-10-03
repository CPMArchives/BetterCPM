; CONFIG H -- SAVE ALL CURRENT STARTUP DEFAULTS.  07-Sep-2026
; Keep SYSGEN out of the resident system. The reference file belongs to
; this particular build; compare its fixed bytes before touching a track.
; 4000 = header, 4080 = original, 5A80 = startup old, 6000 = proposed,
; 8000 = readback. The carrier may use no more than its assigned 52 records.
; These buffers borrow the format catalogue. FDBLOAD puts it back on exit.
SGHEAD  EQU 04000H
SGOLD   EQU 04080H
SGSTOLD EQU 05A80H
SGNEW   EQU 06000H
SGDMA   EQU 08000H
SYSGEN: LD HL,SGTITLE
        CALL HEADER
        LD A,(STDIRTY)                  ; retain pending-state participation
        LD (SGSTFLAG),A
        OR A
        JR Z,SGNOSTATE
        LD A,(STSTATE)
        CP 1
        JP NZ,SGSTBAD
        LD HL,STPEND                    ; validate before the first disk write
        LD DE,SGDMA
        LD BC,256
        LDIR
        CALL STVALID
        JP NZ,SGSTBAD
SGNOSTATE:
        LD HL,SGFCB+12
        LD DE,SGFCB+13
        LD BC,23
        LD (HL),0
        LDIR
        LD DE,SGFCB
        LD C,15
        CALL BDOS
        INC A
        JP Z,SGFILE
        LD DE,SGHEAD
        CALL SGREADF
        JP NZ,SGFILE
        LD HL,SGHEAD
        LD DE,SGMAGIC
        LD BC,6
        CALL SGCMP
        JP NZ,SGFILE
        LD A,(SGHEAD+6)
        OR A
        JP Z,SGFILE
        CP 53
        JP NC,SGFILE
        LD (SGCOUNT),A
        LD HL,SGOLD
SGLOAD: LD (SGPTR),HL
        EX DE,HL
        CALL SGREADF
        JP NZ,SGFILE
        LD HL,(SGPTR)
        LD DE,128
        ADD HL,DE
        LD A,(SGCOUNT)
        DEC A
        LD (SGCOUNT),A
        JR NZ,SGLOAD
        LD DE,SGDMA
        CALL SGREADF
        CP 1
        JP NZ,SGFILE
        LD DE,SGFCB
        LD C,16
        CALL BDOS
; Obtain the table addresses from the running BIOS, not a build address.
        LD B,0
        CALL API
        LD DE,8
        ADD HL,DE
        LD DE,SGHEAD+10
        LD BC,4
        CALL SGCMP
        JP NZ,SGWRONG
        LD HL,(SGHEAD+10)
        LD BC,24
        CALL SGRANGE
        JP C,SGWRONG
        LD (SGPHOFF),HL
        LD HL,(SGHEAD+12)
        LD BC,320
        CALL SGRANGE
        JP C,SGWRONG
        LD (SGLOFF),HL
; The warm-boot vector locates the standard BIOS jump table on either
; machine. All disk addresses below are CP/M's 128-byte BIOS records.
        LD HL,(1)
        DEC HL
        DEC HL
        DEC HL
        LD (SGBASE),HL
        LD BC,0
        LD E,0
        LD A,27
        CALL SGBIOS
        LD A,H
        OR L
        JP Z,SGWRONG
        LD DE,10
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD (SGDPB),HL
        LD C,(HL)
        INC HL
        LD B,(HL)
        LD (SGSPT),BC
        LD HL,(SGHEAD+14)
        OR A
        SBC HL,BC
        JP NZ,SGWRONG
        LD A,B
        OR C
        JP Z,SGWRONG
; The carrier must fit wholly below the allocation area. OFF counts
; BIOS tracks, whose size is SPT records (not physical controller sectors).
        LD HL,(SGDPB)
        LD DE,13
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD A,D
        OR E
        JP Z,SGWRONG
        LD HL,0
        LD BC,(SGSPT)
SGRES:  ADD HL,BC
        JR C,SGRESOK
        DEC DE
        LD A,D
        OR E
        JR NZ,SGRES
        LD A,(SGHEAD+6)
        ADD A,8
        LD E,A
        LD D,0
        OR A
        SBC HL,DE
        JP C,SGWRONG
SGRESOK:
; Restrict this first edition to the known boot carrier starting at 8.
        LD A,(SGHEAD+7)
        CP 8
        JP NZ,SGWRONG
        LD (SGFIRST),A
        CALL SGSTRD                    ; preserve startup records for rollback
        JP NZ,SGIOERR
        XOR A
        LD (SGINDEX),A
SGDISK: CALL SGPTRS
        LD (SGIOBUF),DE
        XOR A
        CALL SGIO
        JP NZ,SGIOERR
        CALL SGNEXT
        JR NZ,SGDISK
; Replace only the reference's editable bytes with their on-disk values.
; It then remains a complete original image, ready for a possible undo.
        LD HL,(SGPHOFF)
        LD BC,24
        CALL SGMERGE
        LD HL,(SGLOFF)
        LD DE,16
        ADD HL,DE
        LD A,4
SGMASK: PUSH AF
        PUSH HL
        LD BC,64
        CALL SGMERGE
        POP HL
        LD DE,80
        ADD HL,DE
        POP AF
        DEC A
        JR NZ,SGMASK
        LD HL,SGOLD
        LD DE,SGNEW
        CALL SGSIZE
        CALL SGCMP
        JP NZ,SGWRONG
; Fetch the live definitions through the public API. Leave DPH pointers,
; allocation maps and other running scratch alone -- they are not defaults.
        XOR A
        LD (SGDRIVE),A
SGLIVE: LD A,(SGDRIVE)
        LD (SGREQ),A
        LD DE,SGREQ
        LD B,1
        CALL API
        JP NZ,SGWRONG
        LD A,(SGDRIVE)
        LD L,A
        LD H,0
        ADD HL,HL
        LD D,H
        LD E,L
        ADD HL,HL
        ADD HL,DE
        LD DE,(SGPHOFF)
        ADD HL,DE
        LD DE,SGNEW
        ADD HL,DE
        EX DE,HL
        LD HL,SGREQ+1
        LD BC,6
        LDIR
        LD A,(SGDRIVE)
        LD (SGREQ),A
        LD DE,SGREQ
        LD B,3
        CALL API
        JP NZ,SGWRONG
        LD A,(SGDRIVE)
        LD L,A
        LD H,0
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD D,H
        LD E,L
        ADD HL,HL
        ADD HL,HL
        ADD HL,DE
        LD DE,(SGLOFF)
        ADD HL,DE
        LD DE,SGNEW+16
        ADD HL,DE
        EX DE,HL
        LD HL,SGREQ+1
        LD BC,64
        LDIR
        LD A,(SGDRIVE)
        INC A
        LD (SGDRIVE),A
        CP 4
        JR NZ,SGLIVE
        LD HL,SGASK
        CALL PUTS
        CALL KEY
        CP 'Y'
        JP NZ,SGEXIT
        CALL SGSTWR                    ; pending values override saved values
        JR NZ,SGSTUNDO
        XOR A
        LD (SGINDEX),A
SGSAVE: CALL SGDIFF
        JR Z,SGSKIP
        CALL SGPTRS
        LD (SGIOBUF),DE
        LD A,1
        CALL SGIO
        JR NZ,SGUNDO
        CALL SGVERIFY
        JR NZ,SGUNDO
SGSKIP: CALL SGNEXT
        JR NZ,SGSAVE
        XOR A
        LD (STDIRTY),A
        LD HL,SGOK
        JP SGREPORT
SGSTUNDO:                              ; failed startup write: restore it only
        CALL SGSTROLL
        LD HL,SGRESTORED
        OR A
        JP Z,SGREPORT
        LD HL,SGDAMAGED
        JP SGREPORT
; Include the failing record in the undo: a failed write may be partial.
; This protects an ordinary I/O failure, not loss of power during SYSGEN.
SGUNDO: LD A,(SGINDEX)
        INC A
        LD (SGSTOP),A
        XOR A
        LD (SGINDEX),A
        LD (SGFAILED),A
SGROLL: CALL SGDIFF
        JR Z,SGRSTEP
        CALL SGPTRS
        LD (SGIOBUF),HL
        LD A,1
        CALL SGIO
        CALL Z,SGVERIFY
        JR Z,SGRSTEP
        LD A,1
        LD (SGFAILED),A
SGRSTEP:LD A,(SGINDEX)
        INC A
        LD (SGINDEX),A
        LD HL,SGSTOP
        CP (HL)
        JR NZ,SGROLL
        CALL SGSTROLL                  ; include startup state in rollback
        JR Z,SGRSTATE
        LD A,1
        LD (SGFAILED),A
SGRSTATE:
        LD HL,SGRESTORED
        LD A,(SGFAILED)
        OR A
        JP Z,SGREPORT
        LD HL,SGDAMAGED
        JP SGREPORT
SGFILE: LD HL,SGFILEMSG
        JR SGREPORT
SGWRONG:LD HL,SGWRONGMSG
        JR SGREPORT
SGIOERR:LD HL,SGREADMSG
        JR SGREPORT
SGSTBAD:LD HL,SGSTBADMSG
SGREPORT:CALL CRLF
        CALL PUTS
        CALL PAUSE
SGEXIT: LD DE,1
        LD C,37
        CALL BDOS
        CALL FDBLOAD
        JP MAIN
SGREADF:LD C,26
        CALL BDOS
        LD DE,SGFCB
        LD C,20
        CALL BDOS
        OR A
        RET
; Check a table is wholly inside the reference. Return its relative offset.
SGRANGE:LD DE,(SGHEAD+8)
        OR A
        SBC HL,DE
        RET C
        PUSH HL
        ADD HL,BC
        EX DE,HL
        CALL SGSIZE
        LD H,B
        LD L,C
        OR A
        SBC HL,DE
        POP HL
        RET
SGSIZE: LD A,(SGHEAD+6)
        LD B,0
        LD C,A
        SRL C
        RR B
        LD A,B
        LD B,C
        LD C,A
        RET
SGMERGE:LD DE,SGNEW
        ADD HL,DE
        PUSH HL
        LD DE,SGNEW-SGOLD
        OR A
        SBC HL,DE
        EX DE,HL
        POP HL
        LDIR
        RET

; Read installed startup defaults into the gap after the reference image.
SGSTRD: LD A,(SGSTFLAG)
        OR A
        RET Z
        XOR A
        LD (SGHEAD+7),A
        INC A
        LD (SGINDEX),A
        LD HL,SGSTOLD
        LD (SGIOBUF),HL
        XOR A
        CALL SGIO
        JR NZ,SGSTEND
        LD A,2
        LD (SGINDEX),A
        LD HL,SGSTOLD+128
        LD (SGIOBUF),HL
        XOR A
        CALL SGIO
SGSTEND:PUSH AF
        LD A,(SGFIRST)
        LD (SGHEAD+7),A
        POP AF
        OR A
        RET

; Write and verify the proposed startup defaults before the carrier records.
SGSTWR: LD A,(SGSTFLAG)
        OR A
        RET Z
        XOR A
        LD (SGHEAD+7),A
        INC A
        LD (SGINDEX),A
        LD HL,STPEND
        LD (SGIOBUF),HL
        CALL STSAVEONE
        JR NZ,SGSTWEND
        LD A,2
        LD (SGINDEX),A
        LD HL,STPEND+128
        LD (SGIOBUF),HL
        CALL STSAVEONE
SGSTWEND:
        PUSH AF
        LD A,(SGFIRST)
        LD (SGHEAD+7),A
        POP AF
        OR A
        RET

; Restore and verify both original startup records. Z means full recovery.
SGSTROLL:
        LD A,(SGSTFLAG)
        OR A
        RET Z
        XOR A
        LD (SGHEAD+7),A
        LD (SGSTFAIL),A
        LD A,2
        LD (SGINDEX),A
        LD HL,SGSTOLD+128
        LD (SGIOBUF),HL
        CALL STRESTORE
        JR Z,SGSTRONE
        LD A,1
        LD (SGSTFAIL),A
SGSTRONE:
        LD A,1
        LD (SGINDEX),A
        LD HL,SGSTOLD
        LD (SGIOBUF),HL
        CALL STRESTORE
        JR Z,SGSTRDONE
        LD A,1
        LD (SGSTFAIL),A
SGSTRDONE:
        LD A,(SGFIRST)
        LD (SGHEAD+7),A
        LD A,(SGSTFAIL)
        OR A
        RET
; Compare BC bytes. Z means equal; no caller depends on the pointers.
SGCMP:  LD A,(DE)
        CP (HL)
        RET NZ
        INC HL
        INC DE
        DEC BC
        LD A,B
        OR C
        JR NZ,SGCMP
        RET
SGPTRS: LD A,(SGINDEX)
        LD H,0
        LD L,A
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        ADD HL,HL
        LD DE,SGOLD
        ADD HL,DE
        PUSH HL
        LD DE,SGNEW-SGOLD
        ADD HL,DE
        EX DE,HL
        POP HL
        RET
SGDIFF: CALL SGPTRS
        LD BC,128
        JP SGCMP
SGNEXT: LD A,(SGINDEX)
        INC A
        LD (SGINDEX),A
        LD HL,SGHEAD+6
        CP (HL)
        RET
SGVERIFY:LD HL,(SGIOBUF)
        PUSH HL
        LD HL,SGDMA
        LD (SGIOBUF),HL
        XOR A
        CALL SGIO
        POP HL
        RET NZ
        LD DE,SGDMA
        LD BC,128
        JP SGCMP
; A=0 read, A=1 write. SGIOBUF is the full 128-byte transfer buffer.
SGIO:   LD (SGWRITE),A
        LD BC,0
        LD E,0
        LD A,27
        CALL SGBIOS
        LD A,H
        OR L
        JR NZ,SGSELECTED
        LD A,1
        OR A
        RET
SGSELECTED:
        LD A,(SGINDEX)
        LD HL,SGHEAD+7
        ADD A,(HL)
        LD L,A
        LD H,0
        LD DE,(SGSPT)
        LD BC,0
SGDIV:  OR A
        SBC HL,DE
        JR C,SGDIVEND
        INC BC
        JR SGDIV
SGDIVEND:ADD HL,DE
        PUSH HL
        LD A,30
        CALL SGBIOS
        POP BC
        LD A,33
        CALL SGBIOS
        LD BC,(SGIOBUF)
        LD A,36
        CALL SGBIOS
        LD A,(SGWRITE)
        OR A
        LD A,39
        JR Z,SGTRANSFER
        LD BC,0
        LD A,42
SGTRANSFER:CALL SGBIOS
        OR A
        RET
SGBIOS: LD HL,(SGBASE)
        PUSH DE
        LD E,A
        LD D,0
        ADD HL,DE
        POP DE
        JP (HL)
; Select boot drive A and publish its DPB and logical records/track.
SGDISKSET:
        LD HL,(1)
        DEC HL
        DEC HL
        DEC HL
        LD (SGBASE),HL
        LD BC,0
        LD E,0
        LD A,27
        CALL SGBIOS
        LD A,H
        OR L
        JR Z,SGDSBAD
        LD DE,10
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD (SGDPB),HL
        LD C,(HL)
        INC HL
        LD B,(HL)
        LD A,B
        OR C
        JR Z,SGDSBAD
        LD (SGSPT),BC
        XOR A
        RET
SGDSBAD:LD A,1
        OR A
        RET
SGTITLE:DB 'Save all current settings as startup defaults',0
SGMAGIC:DB 'BCSG',1,5
SGASK:  DB 'Save all current settings on system disk A: (Y/N)? ',0
SGOK:   DB 13,10,'All current settings saved and verified.',13,10,0
SGFILEMSG:DB 'Missing or invalid A:SYSGEN.DAT for this build.',13,10,0
SGWRONGMSG:DB 'Boot disk does not match this system. Nothing saved.',13,10,0
SGREADMSG:DB 'Cannot read boot system records. Nothing saved.',13,10,0
SGSTBADMSG:DB 'Pending startup command is invalid. Edit or clear it first.',13,10,0
SGRESTORED:DB 'Save failed. Original configuration restored.',13,10,0
SGDAMAGED:DB 'Save failed; restoration also failed.',13,10
        DB 'Boot disk may be damaged. Use your backup.',13,10,0
SGFCB:  DB 1,'SYSGEN  DAT'
        DS 24
SGCOUNT:DB 0
SGINDEX:DB 0
SGDRIVE:DB 0
SGSTOP: DB 0
SGFAILED:DB 0
SGWRITE:DB 0
SGSTFLAG:DB 0
SGSTFAIL:DB 0
SGFIRST:DB 0
SGPTR:  DW 0
SGBASE: DW 0
SGDPB:  DW 0
SGSPT:  DW 0
SGPHOFF:DW 0
SGLOFF: DW 0
SGIOBUF:DW 0
SGREQ:  DS 80
