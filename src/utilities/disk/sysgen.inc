; CONFIG H -- SAVE THE BOOT DISK'S DRIVE DEFINITIONS.  07-Sep-2026
; Keep SYSGEN out of the resident system. The reference file belongs to
; this particular build; compare its fixed bytes before touching a track.
; 4000 = file header, 4080 = original, 6000 = proposed, 8000 = readback.
; These buffers borrow the format catalogue. FLOAD puts it back on exit.
SGHEAD  EQU 04000H
SGOLD   EQU 04080H
SGNEW   EQU 06000H
SGDMA   EQU 08000H
SYSGEN: LD HL,SGTITLE
        CALL HEADER
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
        CP 64
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
        LD HL,SGOK
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
SGREPORT:CALL CRLF
        CALL PUTS
        CALL PAUSE
SGEXIT: LD DE,1
        LD C,37
        CALL BDOS
        CALL FLOAD
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
SGTITLE:DB 'Save current configuration on disk (SYSGEN)',0
SGMAGIC:DB 'BCSG',1,5
SGASK:  DB 'Save current drive settings on boot disk A: (Y/N)? ',0
SGOK:   DB 13,10,'Configuration saved and verified.',13,10,0
SGFILEMSG:DB 'Missing or invalid A:SYSGEN.DAT for this build.',13,10,0
SGWRONGMSG:DB 'Boot disk does not match this system. Nothing saved.',13,10,0
SGREADMSG:DB 'Cannot read boot system records. Nothing saved.',13,10,0
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
SGPTR:  DW 0
SGBASE: DW 0
SGDPB:  DW 0
SGSPT:  DW 0
SGPHOFF:DW 0
SGLOFF: DW 0
SGIOBUF:DW 0
SGREQ:  DS 80
