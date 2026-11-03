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
        CALL CRLF
        LD HL,VIEWLEFT
        LD B,8
        CALL VTEXT
        LD A,(VIEWCOMPARE)
        OR A
        JR Z,VIEWROWS
        LD HL,VIEWVS
        CALL PUTS
        LD HL,VIEWRIGHT
        LD B,8
        CALL VTEXT
VIEWROWS:
        CALL CRLF
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
        CP 3
        JP Z,MENU
        CP 'Q'
        JP Z,MENU
        CP '>'
        JP Z,VMAPNEXT
        CP '<'
        JP Z,VMAPPREV
        CP 'A'
        JR NZ,VPAGE
        LD A,(VIEWDIFF)
        XOR 1
        LD (VIEWDIFF),A
        JP VIEWSCREEN
VPAGE:  SUB '1'
        CP 4
        JR NC,VIEWPROMPT
        INC A
        LD (VIEWPAGE),A
        JP VIEWSCREEN
VPRINTVAL:
        LD DE,(VIEWOFFSET)
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
        CP 2
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
        LD HL,VIEWSELECT
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        LD IX,WORKBUF+128
        LD A,(WORKBUF+8)
        LD (VIEWREMAIN),A
VSEARCH:
        LD A,(VIEWREMAIN)
        OR A
        JP Z,NOIMPORT
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
        LD DE,WORKBUF
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
        JR Z,VCAPTRACKS
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
VIEWLEFT:DS 76
VIEWRIGHT:DS 76
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
        DB 1
        DW VADDR0
        DW 59
        DB 1
        DW VADDR1
        DW 65535
VADDR0:DB 'Addressing flags: ',0
VADDR1:DB 'Sector map count: ',0
VDPB:
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

VMAPNEXT:LD A,(VIEWMAPSTART)
        ADD A,8
        JP C,VIEWSCREEN
        CP 255
        JP Z,VIEWSCREEN
        LD (VIEWMAPSTART),A
        JP VIEWSCREEN
VMAPPREV:LD A,(VIEWMAPSTART)
        SUB 8
        JP C,VIEWSCREEN
        LD (VIEWMAPSTART),A
        JP VIEWSCREEN
VMAPS:  LD HL,VMAPTITLE
        CALL PUTS
        LD A,(VIEWMAPSTART)
        LD (VIEWMAPSLOT),A
        LD B,8
VMAPROW:PUSH BC
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
        LD HL,VIEWMAPSLOT
        INC (HL)
        POP BC
        RET Z
        DJNZ VMAPROW
        RET
VMAPVALUE:
        LD A,(VIEWMAPSLOT)
        CP (IX+55)
        JR NC,VMAPABSENT
        LD E,A
        LD D,0
        LD L,(IX+60)
        LD H,(IX+61)
        ADD HL,DE
        LD DE,WORKBUF
        ADD HL,DE
        LD A,(HL)
        CALL COUNTDEC
        LD A,'/'
        CALL PUTC
        LD C,(IX+56)
        LD L,(IX+62)
        LD H,(IX+63)
        LD A,H
        OR L
        JR Z,VMAPSIZE
        LD DE,WORKBUF
        ADD HL,DE
        LD A,(HL)
        CP 081H
        JR NZ,VMAPSIZE
        INC HL
        INC HL
        LD A,(VIEWMAPSLOT)
        LD E,A
        LD D,0
        ADD HL,DE
        LD C,(HL)
VMAPSIZE:LD A,C
        CALL SIZEVALUE
        JP EDPRINT
VMAPABSENT:LD HL,VMAPNONE
        JP PUTS
VIEWMAPSTART:DB 0
VIEWMAPSLOT:DB 0
VMAPTITLE:DB 'Slot ID/bytes (< previous, > next)',13,10,0
VMAPNONE:DB 'absent',0
