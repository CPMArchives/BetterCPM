; CONFIG H -- SAVE ALL CURRENT STARTUP DEFAULTS.  07-Sep-2026
; Keep saving out of the resident system. Embedded build records validate
; fixed carrier bytes with CRC-32 before any editable defaults are used.
; 4000 = header, 4080 = original, 5A80 = startup old, 6000 = proposed,
; 8000 = readback. The carrier may use no more than its assigned 52 records.
; These buffers borrow the format catalogue. FDBLOAD puts it back on exit.
SGHEAD  EQU 04000H
SGOLD   EQU 04080H
SGSTOLD EQU 05A80H
SGNEW   EQU 06000H
SGDMA   EQU 08000H
SYSGEN: LD A,(CF_MODE)                 ; /SHOW shares validation/read path only
        CP 1
        JR NZ,SGEDIT
        XOR A
        LD (SGSTFLAG),A
        JP SGNOSTATE
SGEDIT: LD HL,SGTITLE
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
; Select an embedded build record by the actual BIOS record geometry. The
; existing public-address and bounds checks below then validate its layout.
        CALL SGDISKSET
        JP NZ,SGIOERR
        LD HL,SGVALID
SGVPICK:
        LD DE,SGHEAD
        LD BC,16
        LDIR
        LD DE,SGCRCEX
        LD BC,4
        LDIR
        PUSH HL
        LD HL,(SGHEAD+14)
        LD BC,(SGSPT)
        OR A
        SBC HL,BC
        JR NZ,SGVNEXT
        LD B,0
        CALL API
        LD DE,8
        ADD HL,DE
        LD DE,SGHEAD+10
        LD BC,4
        CALL SGCMP
        JR Z,SGVFOUND
SGVNEXT:
        POP HL
        LD DE,SGVEND
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JR C,SGVPICK
        JP SGWRONG
SGVFOUND:
        POP HL
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
; Preserve the exact original carrier for rollback. Normalize a private copy
; for CRC validation; editable fields never contribute to the fingerprint.
        LD HL,SGNEW
        LD DE,SGOLD
        CALL SGSIZE
        LDIR
        LD HL,(SGPHOFF)
        LD BC,24
        CALL SGZERO
        LD HL,(SGLOFF)
        LD DE,16
        ADD HL,DE
        LD A,4
SGMASK: PUSH AF
        PUSH HL
        LD BC,64
        CALL SGZERO
        POP HL
        LD DE,80
        ADD HL,DE
        POP AF
        DEC A
        JR NZ,SGMASK
        CALL IO_MASK
        JP NZ,SGWRONG
        LD HL,SGNEW
        CALL SGSIZE
        CALL SGCRC32
        LD HL,SGCRC
        LD DE,SGCRCEX
        LD BC,4
        CALL SGCMP
        JP NZ,SGWRONG
; Restore saved configuration fields after the check, before inspection/editing.
        LD HL,SGOLD
        LD DE,SGNEW
        CALL SGSIZE
        LDIR
; Inspection stops here: the installed carrier has been checked against this
; build, masking only the established editable fields. Never reach save logic.
        LD A,(CF_MODE)
        CP 1
        JP Z,CF_SDRIVES
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
SGWRONG:LD HL,SGWRONGMSG
        JR SGREPORT
SGIOERR:LD HL,SGREADMSG
        JR SGREPORT
SGSTBAD:LD HL,SGSTBADMSG
SGREPORT:CALL CRLF
        CALL PUTS
        LD A,(CF_MODE)
        CP 1
        JP Z,DONE                      ; inspection never pauses or saves
        CALL PAUSE
SGEXIT: LD DE,1
        LD C,37
        CALL BDOS
        CALL FDBLOAD
        JP MAIN
; Check a table is wholly inside the carrier. Return its relative offset.
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
SGZERO: LD DE,SGNEW
        ADD HL,DE
SGZLOOP:LD (HL),0
        INC HL
        DEC BC
        LD A,B
        OR C
        JR NZ,SGZLOOP
        RET

; CRC-32/ISO-HDLC: reflected polynomial EDB88320, init/final xor FFFFFFFF.
; HL=bytes, BC=length. Result is little endian in SGCRC. This is a build-
; compatibility/corruption check, not authentication of untrusted system code.
SGCRC32:
        LD DE,SGCRC
        LD A,255
        LD (DE),A
        INC DE
        LD (DE),A
        INC DE
        LD (DE),A
        INC DE
        LD (DE),A
        LD A,B
        OR C
        JR Z,SGCRFINI
SGCRBYTE:
        LD A,(SGCRC)
        XOR (HL)
        LD (SGCRC),A
        INC HL
        PUSH HL
        PUSH BC
        LD B,8
SGCRBIT:
        LD HL,SGCRC+3
        SRL (HL)
        DEC HL
        RR (HL)
        DEC HL
        RR (HL)
        DEC HL
        RR (HL)
        JR NC,SGCRNEXT
        LD A,(HL)
        XOR 020H
        LD (HL),A
        INC HL
        LD A,(HL)
        XOR 083H
        LD (HL),A
        INC HL
        LD A,(HL)
        XOR 0B8H
        LD (HL),A
        INC HL
        LD A,(HL)
        XOR 0EDH
        LD (HL),A
SGCRNEXT:
        DJNZ SGCRBIT
        POP BC
        POP HL
        DEC BC
        LD A,B
        OR C
        JR NZ,SGCRBYTE
SGCRFINI:
        LD HL,SGCRC
        LD B,4
SGCRFINAL:
        LD A,(HL)
        CPL
        LD (HL),A
        INC HL
        DJNZ SGCRFINAL
        RET

; Read installed startup defaults into the gap after the original carrier.
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
SGASK:  DB 'Save all current settings on system disk A: (Y/N)? ',0
SGOK:   DB 13,10,'All current settings saved and verified.',13,10,0
SGWRONGMSG:DB 'Boot disk does not match this system. Nothing saved.',13,10,0
SGREADMSG:DB 'Cannot read boot system records. Nothing saved.',13,10,0
SGSTBADMSG:DB 'Pending startup command is invalid. Edit or clear it first.',13,10,0
SGRESTORED:DB 'Save failed. Original configuration restored.',13,10,0
SGDAMAGED:DB 'Save failed; restoration also failed.',13,10
        DB 'Boot disk may be damaged. Use your backup.',13,10,0
SGCRC:  DS 4
SGCRCEX:DS 4
; @config-validation@
; @config-iobyte@
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
