; Read-only view overlay, loaded below the persistent editor.
; WORKBUF, editor data and session metadata are never destinations.
VIEWENTRY:
        LD A,1
        LD (VIEWACTIVE),A
        LD HL,VIEWLEFT
        LD (VIEWSIDE),HL
        CALL VSELECT
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VIEWSTART
        LD HL,VIEWRIGHT
        LD (VIEWSIDE),HL
        CALL VSELECT
VIEWSTART:
        XOR A
        LD (VIEWMAPSTART),A
        LD A,1
        LD (VIEWPAGE),A
        LD A,(VIEWCOMPARE)
        LD (VIEWDIFF),A
VIEWSCREEN:
        LD A,(0)
        CP 0C3H
        CALL Z,UI_CLEAR
        LD HL,VIEWTITLE
        CALL PUTS
        LD A,(VIEWPAGE)
        CALL COUNTDEC
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VMODEDONE
        LD HL,VMODEALL
        LD A,(VIEWDIFF)
        OR A
        JR Z,VMODEPRINT
        LD HL,VMODEDIFF
VMODEPRINT:CALL PUTS
VMODEDONE:CALL CRLF
        LD HL,VIEWLEFT
        LD B,8
        CALL VIDTEXT
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VIEWROWS
        LD HL,VIEWVS
        CALL PUTS
        LD HL,VIEWRIGHT
        LD B,8
        CALL VIDTEXT
VIEWROWS:
        CALL CRLF
        LD HL,VIEWLEFT+8
        LD B,32
        CALL VIDTEXT
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VDESCDONE
        LD HL,VIEWVS
        CALL PUTS
        LD HL,VIEWRIGHT+8
        LD B,32
        CALL VIDTEXT
VDESCDONE:CALL CRLF
        LD A,(VIEWPAGE)
        DEC A
        LD L,A
        LD H,0
        ADD HL,HL
        LD DE,VIEWTABLES
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD (VIEWROW),HL
VNEXTROW:
        LD HL,(VIEWROW)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD A,D
        AND E
        CP 255
        JP Z,VIEWPROMPT
        LD A,(HL)
        INC HL
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD (VIEWROW),HL
        LD (VIEWWIDTH),A
        LD (VIEWOFFSET),DE
        PUSH BC
        LD HL,VIEWLEFT
        CALL VVALUE
        LD (VIEWVALUE),HL
        LD HL,VIEWRIGHT
        CALL VVALUE
        LD (VIEWOTHER),HL
        LD DE,(VIEWVALUE)
        OR A
        SBC HL,DE
        LD A,(VIEWWIDTH)
        CP 4
        JR NZ,VCMP16
        LD HL,VIEWLEFT
        LD DE,(VIEWOFFSET)
        ADD HL,DE
        LD BC,VIEWRIGHT-VIEWLEFT
        PUSH HL
        ADD HL,BC
        EX DE,HL
        POP HL
        LD B,4
        CALL CMPFIELD
        JR VCMPDONE
VCMP16:LD HL,(VIEWVALUE)
        LD DE,(VIEWOTHER)
        OR A
        SBC HL,DE
VCMPDONE:LD A,0
        JR Z,VSAME
        INC A
VSAME:  LD (VIEWCHANGED),A
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VSHOW
        LD A,(VIEWDIFF)
        OR A
        JR Z,VSHOW
        LD A,(VIEWCHANGED)
        OR A
        JR NZ,VSHOW
        POP BC
        JP VNEXTROW
VSHOW:  POP HL
        CALL PUTS
        LD HL,VIEWLEFT
        CALL VPRINTVAL
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VENDROW
        LD HL,VIEWVS
        CALL PUTS
        LD HL,VIEWRIGHT
        CALL VPRINTVAL
        LD A,(VIEWCHANGED)
        OR A
        JR Z,VENDROW
        LD A,'*'
        CALL PUTC
VENDROW:CALL CRLF
        JP VNEXTROW
VIEWPROMPT:
        LD A,(VIEWPAGE)
        CP 2
        CALL Z,VMAPS
        LD HL,VIEWHELP
        CALL ASKCHOICE
VIEWKEY:
        CP 3
        JP Z,MENU
        CP 'Q'
        JP Z,MENU
        CP '>'
        JP Z,VMAPNEXT
        CP '.'
        JP Z,VMAPNEXT
        CP '<'
        JP Z,VMAPPREV
        CP ','
        JP Z,VMAPPREV
        CP 'A'
        JR NZ,VPAGE
        LD A,(VIEWDIFF)
        XOR 1
        LD (VIEWDIFF),A
        JP VIEWSCREEN
VPAGE:  SUB '1'
        CP 4
        JR NC,VIEWBADKEY
        INC A
        LD (VIEWPAGE),A
        JP VIEWSCREEN
VIEWBADKEY:CALL BADCHOICE
        LD HL,VIEWHELP
        CALL ASKCHOICE
        JP VIEWKEY
VPRINTVAL:
        LD A,(VIEWWIDTH)
        CP 4
        JR Z,VPRINT32
        CALL VVALUE
        JP EDPRINT
VPRINT32:LD DE,(VIEWOFFSET)
        ADD HL,DE
        LD C,(HL)
        INC HL
        LD B,(HL)
        LD A,(VIEWWIDTH)
        CP 1
        JR NZ,VPRINTWORD
        LD B,0
VPRINTWORD:
        CP 4
        JR NZ,VPRINT16
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        LD H,B
        LD L,C
        JP EDDEC32
VPRINT16:LD H,B
        LD L,C
        JP EDPRINT
VVALUE: LD DE,(VIEWOFFSET)
        ADD HL,DE
        LD E,(HL)
        LD D,0
        LD A,(VIEWWIDTH)
        CP 3
        JR C,VNORMALWIDTH
        CP 4
        JR Z,VVALRET
        SUB 5
        LD B,A
        LD A,E
        JR Z,VFLAGREADY
VFLAGSHIFT:SRL A
        DJNZ VFLAGSHIFT
VFLAGREADY:AND 1
        LD E,A
        JR VVALRET
VNORMALWIDTH:CP 2
        JR NZ,VVALRET
        INC HL
        LD D,(HL)
VVALRET:EX DE,HL
        RET
VTEXT:  LD A,(HL)
        CALL PUTC
        INC HL
        DJNZ VTEXT
        RET
VSELECT:
        LD HL,VSOURCEMSG
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        CP '@'
        JP Z,VEDITOR
        CP ':'
        JP Z,VDRIVE
        CP '/'
        JP Z,VFILE
        LD HL,WORKBUF
        LD (VIEWBASE),HL
        JP VSEARCHSTART
VFILE: LD HL,VFILEMSG
        CALL ASKNAME
        CALL TOINPUT
        LD HL,INPUT+9
        LD DE,VFDBEXT
        CALL MATCH3
        JP NZ,BADNAME
        CALL OPENIN
        LD HL,FDFRAM
VFILEREAD:LD (POS),HL
        LD DE,0A500H
        OR A
        SBC HL,DE
        JR NC,VFILELIMIT
        LD DE,(POS)
        CALL SETDMA
        LD DE,INPUT
        LD C,20
        CALL BDOS
        CP 1
        JR Z,VFILEEND
        OR A
        JP NZ,IOERR
        LD HL,(POS)
        LD DE,128
        ADD HL,DE
        JR VFILEREAD
VFILELIMIT:
        LD DE,INBUF
        CALL SETDMA
        LD DE,INPUT
        LD C,20
        CALL BDOS
        CP 1
        JP NZ,MEMERR
VFILEEND:CALL CLOSEIN
        LD HL,(POS)
        LD DE,FDFRAM
        OR A
        SBC HL,DE
        LD (FDBLEN),HL
        CALL FDBVALID
        JP C,BADFDB
        CALL CHECKCANON
        CALL SEMANTICS
        LD HL,FDFRAM
        LD (VIEWBASE),HL
        LD HL,VIEWSELECT
        CALL ASK
VSEARCHSTART:
        LD HL,(VIEWBASE)
        LD DE,128
        ADD HL,DE
        PUSH HL
        POP IX
        LD HL,(VIEWBASE)
        LD DE,8
        ADD HL,DE
        LD A,(HL)
        LD (VIEWREMAIN),A
VSEARCH:
        LD A,(VIEWREMAIN)
        OR A
        JR NZ,VSEARCHFOUND
        LD HL,VNOTFOUND
        CALL PUTS
        JP VSELECT
VSEARCHFOUND:
        PUSH IX
        POP HL
        LD DE,ANSWER
        LD B,8
VCMP:
        LD A,(DE)
        OR A
        JR Z,VPAD
        INC DE
        JR VCHAR
VPAD:   LD A,' '
VCHAR:  CP (HL)
        JP NZ,VSKIP
        INC HL
        DJNZ VCMP
        LD A,(DE)
        OR A
        JP NZ,VSKIP
        PUSH IX
        POP HL
        LD DE,(VIEWSIDE)
        LD BC,64
        LDIR
VNORMALIZE:
        XOR A
        LD (VIEWUNIT),A
        ; Derive effective values from the independent logical-track units.
        LD L,(IX+57)
        LD H,0
        BIT 0,(IX+58)
        JR Z,VCAPTRACKS
        BIT 7,(IX+58)
        JR Z,VCAPDOUBLE
        PUSH HL
        LD L,(IX+62)
        LD H,(IX+63)
        LD DE,(VIEWBASE)
        ADD HL,DE
        LD A,(HL)
        CP 081H
        JR NZ,VCAPUNIT
        INC HL
        LD E,(HL)
        LD D,0
        INC HL
        ADD HL,DE
VCAPUNIT:LD A,(HL)
        CP 082H
        POP HL
        JR NZ,VCAPDOUBLE
        LD A,1
        LD (VIEWUNIT),A
        JR VCAPTRACKS
VCAPDOUBLE:ADD HL,HL
VCAPTRACKS:
        LD E,(IX+40)
        LD D,(IX+41)
        CALL MULTIPLY
        LD HL,(PRODUCT)
        LD DE,(PRODUCT+2)
        LD B,7
        CALL VSHIFT
        LD BC,64
        CALL VSTORE32
        LD L,(IX+53)
        LD H,(IX+54)
        LD E,(IX+40)
        LD D,(IX+41)
        CALL MULTIPLY
        LD HL,(PRODUCT)
        LD DE,(PRODUCT+2)
        LD B,7
        CALL VSHIFT
        LD BC,68
        CALL VSTORE32
        LD HL,128
        LD DE,0
        LD B,(IX+42)
        CALL VSHIFT
        LD BC,72
        CALL VSTORE32
        LD HL,32
        LD E,(IX+47)
        LD D,(IX+48)
        CALL MULTIPLY
        LD HL,(PRODUCT)
        LD DE,32
        ADD HL,DE
        LD (PRODUCT),HL
        LD HL,(PRODUCT+2)
        LD DE,0
        ADC HL,DE
        EX DE,HL
        LD HL,(PRODUCT)
        LD BC,586
        CALL VSTORE32
        ; DSM is the last allocation block, so include block zero.
        LD L,(IX+45)
        LD H,(IX+46)
        LD DE,128
        CALL MULTIPLY
        LD HL,(PRODUCT)
        LD DE,128
        ADD HL,DE
        LD (PRODUCT),HL
        LD HL,(PRODUCT+2)
        LD DE,0
        ADC HL,DE
        EX DE,HL
        LD HL,(PRODUCT)
        LD B,(IX+42)
        CALL VSHIFT
        LD BC,590
        CALL VSTORE32
        LD HL,(VIEWSIDE)
        LD DE,68
        ADD HL,DE
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        PUSH DE
        PUSH BC
        LD HL,(VIEWSIDE)
        LD DE,586
        ADD HL,DE
        LD C,(HL)
        INC HL
        LD B,(HL)
        INC HL
        LD E,(HL)
        INC HL
        LD D,(HL)
        POP HL
        ADD HL,BC
        EX DE,HL
        POP BC
        ADC HL,BC
        EX DE,HL
        LD BC,594
        CALL VSTORE32
        LD HL,(VIEWSIDE)
        LD DE,598
        ADD HL,DE
        LD A,(VIEWUNIT)
        LD (HL),A
        INC HL
        LD (HL),1
        INC HL
        LD (HL),64
        LD HL,(VIEWSIDE)
        LD DE,76
        ADD HL,DE
        EX DE,HL
        LD L,(IX+60)
        LD H,(IX+61)
        PUSH DE
        LD DE,(VIEWBASE)
        ADD HL,DE
        POP DE
        LD C,(IX+55)
        LD B,0
        LDIR
        LD HL,(VIEWSIDE)
        LD DE,331
        ADD HL,DE
        LD B,(IX+55)
        LD A,(IX+56)
VSIZEFILL:LD (HL),A
        INC HL
        DJNZ VSIZEFILL
        LD L,(IX+62)
        LD H,(IX+63)
        LD A,H
        OR L
        RET Z
        LD DE,(VIEWBASE)
        ADD HL,DE
        LD A,(HL)
        CP 081H
        RET NZ
        INC HL
        LD C,(HL)
        LD B,0
        INC HL
        PUSH HL
        LD HL,(VIEWSIDE)
        LD DE,331
        ADD HL,DE
        EX DE,HL
        POP HL
        LDIR
        RET
VSHIFT: LD A,B
        OR A
        RET Z
VSHIFTL:ADD HL,HL
        RL E
        RL D
        DJNZ VSHIFTL
        RET
VSTORE32:
        PUSH DE
        PUSH HL
        LD HL,(VIEWSIDE)
        ADD HL,BC
        POP BC
        LD (HL),C
        INC HL
        LD (HL),B
        INC HL
        POP DE
        LD (HL),E
        INC HL
        LD (HL),D
        RET
VSKIP:  LD DE,64
        ADD IX,DE
        LD HL,VIEWREMAIN
        DEC (HL)
        JP VSEARCH
VIEWLEFT:DS 610
VIEWRIGHT:DS 610
VIEWROW:DW 0
VIEWSIDE:DW 0
VIEWOFFSET:DW 0
VIEWVALUE:DW 0
VIEWOTHER:DW 0
VIEWWIDTH:DB 0
VIEWCHANGED:DB 0
VIEWREMAIN:DB 0
VIEWPAGE:DB 1
VIEWDIFF:DB 1
VIEWTITLE:DB 'Format details/compare  Page ',0
VIEWVS:DB ' | ',0
VIEWSELECT:DB 'Working catalogue ID: ',0
VIEWHELP:DB '1-4 Page, A All/differences, Q or BREAK Return: ',0
VIEWTABLES: DW VGEOM,VADDR,VDPB,VLAYOUT
VGEOM:
        DW 598
        DB 1
        DW VUNITTXT
        DW 58
        DB 5
        DW VSIDES
        DW 58
        DB 6
        DW VENCODING
        DW 58
        DB 7
        DW VINVERT
        DW 57
        DB 1
        DW VGEOM0
        DW 55
        DB 1
        DW VGEOM1
        DW 56
        DB 1
        DW VGEOM2
        DW 65535
VGEOM0:DB 'Cylinders: ',0
VGEOM1:DB 'Sectors per surface: ',0
VGEOM2:DB 'Sector size code: ',0
VADDR:
        DW 58
        DB 8
        DW VSIDEORDER
        DW 58
        DB 9
        DW VDIRSIDE
        DW 58
        DB 10
        DW VTRACKIDS
        DW 58
        DB 11
        DW VSECTORIDS
        DW 58
        DB 1
        DW VADDR0
        DW 59
        DB 1
        DW VADDR1
        DW 65535
VADDR0:DB 'Addressing flags: ',0
VADDR1:DB 'Sector map count: ',0
VDPB:
        DW 599
        DB 1
        DW VVERSIONTXT
        DW 600
        DB 1
        DW VSTRIDETXT
        DW 40
        DB 2
        DW VDPB0
        DW 42
        DB 1
        DW VDPB1
        DW 43
        DB 1
        DW VDPB2
        DW 44
        DB 1
        DW VDPB3
        DW 45
        DB 2
        DW VDPB4
        DW 47
        DB 2
        DW VDPB5
        DW 49
        DB 1
        DW VDPB6
        DW 50
        DB 1
        DW VDPB7
        DW 51
        DB 2
        DW VDPB8
        DW 53
        DB 2
        DW VDPB9
        DW 65535
VDPB0:DB 'SPT: ',0
VDPB1:DB 'BSH: ',0
VDPB2:DB 'BLM: ',0
VDPB3:DB 'EXM: ',0
VDPB4:DB 'DSM: ',0
VDPB5:DB 'DRM: ',0
VDPB6:DB 'AL0: ',0
VDPB7:DB 'AL1: ',0
VDPB8:DB 'CKS: ',0
VDPB9:DB 'OFF: ',0
VLAYOUT:
        DW 586
        DB 4
        DW VDIRSIZE
        DW 590
        DB 4
        DW VALLOC
        DW 594
        DB 4
        DW VDIREND
        DW 64
        DB 4
        DW VRAWTXT
        DW 68
        DB 4
        DW VDIRTXT
        DW 72
        DB 4
        DW VBLOCKTXT
        DW 53
        DB 2
        DW VLAYOUT0
        DW 65535
VLAYOUT0:DB 'Reserved logical tracks: ',0

VRAWTXT:DB 'Raw capacity bytes: ',0
VDIRTXT:DB 'Directory byte offset: ',0
VBLOCKTXT:DB 'Allocation block bytes: ',0

VMAPNEXT:CALL VMAPCOUNT
        LD B,A
        LD A,(VIEWMAPSTART)
        ADD A,8
        JP C,VIEWSCREEN
        CP B
        JP NC,VIEWSCREEN
        LD (VIEWMAPSTART),A
        JP VIEWSCREEN
VMAPPREV:LD A,(VIEWMAPSTART)
        SUB 8
        JP C,VIEWSCREEN
        LD (VIEWMAPSTART),A
        JP VIEWSCREEN
VMAPCOUNT:LD A,(VIEWLEFT+55)
        LD B,A
        LD A,(VIEWCOMPARE)
        OR A
        LD A,B
        RET Z
        LD A,(VIEWRIGHT+55)
        CP B
        RET NC
        LD A,B
        RET
VMAPS:  LD HL,VMAPTITLE
        CALL PUTS
        CALL VMAPCOUNT
        LD (VIEWMAPTOTAL),A
        LD B,A
        LD A,(VIEWMAPSTART)
        CALL MAPRANGE
        XOR A
        LD (VIEWMAPSHOWN),A
        LD A,(VIEWMAPSTART)
        LD (VIEWMAPSLOT),A
        LD B,8
VMAPROW:PUSH BC
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VMAPSHOWROW
        LD A,(VIEWDIFF)
        OR A
        JR Z,VMAPSHOWROW
        LD IX,VIEWLEFT
        CALL VMAPFETCH
        PUSH HL
        LD IX,VIEWRIGHT
        CALL VMAPFETCH
        POP DE
        OR A
        SBC HL,DE
        JR Z,VMAPADVANCE
VMAPSHOWROW:
        LD A,(VIEWMAPSLOT)
        LD B,A
        LD A,(VIEWMAPTOTAL)
        CP B
        JR Z,VMAPSTOP
        XOR A
        INC A
        LD (VIEWMAPSHOWN),A
        LD A,(VIEWMAPSLOT)
        INC A
        CALL COUNTDEC
        LD A,' '
        CALL PUTC
        LD IX,VIEWLEFT
        CALL VMAPVALUE
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VMAPEND
        LD HL,VIEWVS
        CALL PUTS
        LD IX,VIEWRIGHT
        CALL VMAPVALUE
VMAPEND:CALL CRLF
VMAPADVANCE:
        LD HL,VIEWMAPSLOT
        INC (HL)
        POP BC
        JR Z,VMAPFINISH
        DJNZ VMAPROW
VMAPFINISH:LD A,(VIEWMAPSHOWN)
        OR A
        RET NZ
        LD HL,VMAPEMPTY
        JP PUTS
VMAPSTOP:POP BC
        JR VMAPFINISH
VMAPVALUE:
        LD A,(VIEWMAPSLOT)
        CP (IX+55)
        JR NC,VMAPABSENT
        LD E,A
        LD D,0
        PUSH IX
        POP HL
        LD BC,76
        ADD HL,BC
        ADD HL,DE
        LD A,(HL)
        CALL COUNTDEC
        LD A,'/'
        CALL PUTC
        PUSH IX
        POP HL
        LD BC,331
        ADD HL,BC
        ADD HL,DE
        LD C,(HL)
VMAPSIZE:LD A,C
        CALL SIZEVALUE
        JP EDPRINT
VMAPABSENT:LD HL,VMAPNONE
        JP PUTS
VIEWMAPTOTAL:DB 0
VIEWMAPSHOWN:DB 0
VIEWMAPSTART:DB 0
VIEWMAPSLOT:DB 0
VMAPTITLE:DB 'Slot ID/bytes: ,< Previous   .> Next  ',0
VMAPEMPTY:DB 'No map differences in this range.',13,10,0
VMAPNONE:DB 'absent',0

VEDITOR:
        LD A,(EDSOURCE)
        OR A
        JP Z,MENU
        JR VSNAPEDITOR
VDRIVE:
        LD A,(ANSWER+1)
        SUB 'A'
        CP 1
        JP C,BADNAME
        CP 4
        JP NC,BADNAME
        LD (VDRIVENO),A
VSNAPEDITOR:
        LD HL,EDITBIND
        LD DE,VSAVEBIND
        LD BC,64
        LDIR
        LD HL,EDIDENT
        LD DE,VSAVEID
        LD BC,40
        LDIR
        LD HL,EDIDS
        LD DE,VSAVEMAP
        LD BC,510
        LDIR
        LD HL,VRESTOREERROR
        LD (VIEWCLEANUP),HL
        LD A,(ANSWER)
        CP ':'
        JR NZ,VBUILD
        LD A,(VDRIVENO)
        CALL EDCAPTURE
        JP C,EDERROR
        CALL EDCLEARID
        CALL EDEXPAND
VBUILD:CALL EDMAKE
        LD HL,FDFRAM
        LD (VIEWBASE),HL
        LD IX,FDFRAM+128
        LD HL,FDFRAM+128
        LD DE,(VIEWSIDE)
        LD BC,64
        LDIR
        CALL VNORMALIZE
        LD HL,EDIDENT
        LD DE,(VIEWSIDE)
        LD BC,40
        LDIR
        CALL VRESTORE
        RET
VRESTORE:
        LD HL,0
        LD (VIEWCLEANUP),HL
        XOR A
        LD (EDITCHECK),A
        LD HL,VSAVEBIND
        LD DE,EDITBIND
        LD BC,64
        LDIR
        LD HL,VSAVEID
        LD DE,EDIDENT
        LD BC,40
        LDIR
        LD HL,VSAVEMAP
        LD DE,EDIDS
        LD BC,510
        LDIR
        RET
VSOURCEMSG:DB 'Source: catalogue ID, / file, @ editor, :B-:D drive: ',0
VFILEMSG:DB 'Source .FDB filename: ',0
VFDBEXT:DB 'FDB'
VIEWBASE:DW 0
VDRIVENO:DB 0
VSAVEBIND:DS 64
VSAVEID:DS 40
VSAVEMAP:DS 510

VRESTOREERROR:CALL VRESTORE
        LD HL,VINVALID
        JP EXITMSG
VINVALID:DB 'Cannot inspect this source; working format preserved.',13,10,0

VSIDES:DB 'Two sides (0 no, 1 yes): ',0
VENCODING:DB 'Recording (0 FM, 1 MFM): ',0
VINVERT:DB 'Inversion (0 no, 1 yes): ',0
VSIDEORDER:DB 'Side order (0 alternating, 1 side-major): ',0
VDIRSIDE:DB 'Side 1 (0 forward, 1 reverse): ',0
VTRACKIDS:DB 'Track IDs (0 per-cylinder, 1 continuous): ',0
VSECTORIDS:DB 'Sector IDs (0 restart, 1 continuous): ',0

VMAPFETCH:
        LD A,(VIEWMAPSLOT)
        CP (IX+55)
        LD HL,65535
        RET NC
        LD E,A
        LD D,0
        PUSH IX
        POP HL
        LD BC,76
        ADD HL,BC
        ADD HL,DE
        LD A,(HL)
        PUSH AF
        LD BC,255
        ADD HL,BC
        LD L,(HL)
        POP AF
        LD H,A
        RET

VIDTEXT:LD A,(HL)
        CP 32
        JP NZ,VTEXT
        LD HL,VUNKNOWN
        JP PUTS
VUNKNOWN:DB '<unknown>',0

VDIRSIZE:DB 'Directory bytes: ',0
VALLOC:DB 'Allocated filesystem bytes: ',0
VDIREND:DB 'Directory end byte: ',0

VIEWUNIT:DB 0
VUNITTXT:DB 'Logical track (0 surface, 1 cylinder): ',0
VVERSIONTXT:DB 'FDB encoding version: ',0
VSTRIDETXT:DB 'FDB descriptor bytes: ',0

VMODEALL:DB '  All values',0
VMODEDIFF:DB '  Differences only',0
VNOTFOUND:DB 'ID not found; select a source again.',13,10,0
