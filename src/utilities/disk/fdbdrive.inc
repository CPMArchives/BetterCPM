; FDB drive adapter. A = logical drive (B=1 .. D=3).
; Capture leaves EDITBIND intact on failure. Carry indicates refusal.
EDCAPTURE:
        CALL EDGETDEST
        RET C
        LD HL,EDREQUEST+1
        LD DE,EDITBIND
        LD BC,64
        LDIR
        OR A
        RET

; Use CONFIG's active-binding APIs. Preserve the destination's physical
; drive selector: a copied format must not reroute the destination.
EDSETDRIVE:
        CALL EDGETDEST
        RET C
        LD A,(EDREQUEST+1)
        PUSH AF
        LD HL,BIND
        LD DE,EDREQUEST+1
        LD BC,64
        LDIR
        POP AF
        LD (EDREQUEST+1),A
        LD A,(EDREQUEST+53)
        OR A
        JR Z,EDSETVALID
        LD IX,EDREQUEST
        LD BC,002B7H
        CALL BDOS
        LD DE,04644H
        OR A
        SBC HL,DE
        JR NZ,EDREFUSED
EDSETVALID:
        LD B,4
        CALL EDBINDAPI
        JR NZ,EDREFUSED
        LD A,(EDLOGICAL)
        LD B,A
        LD E,1
        LD D,0
EDRESETMASK:
        SLA E
        DJNZ EDRESETMASK
        LD C,37
        CALL BDOS
        OR A
        RET
EDGETDEST:
        CP 1
        JR C,EDREFUSED
        CP 4
        JR NC,EDREFUSED
        LD (EDLOGICAL),A
        LD (EDREQUEST),A
        LD B,3
        CALL EDBINDAPI
        JR NZ,EDREFUSED
        LD A,(EDREQUEST+1)
        CP 4
        JR NC,EDREFUSED
        OR A
        RET
EDREFUSED:
        SCF
        RET
EDBINDAPI:
        LD DE,EDREQUEST
        LD C,181
        CALL BDOS
        LD A,L
        OR A
        RET
EDLOGICAL: DB 0
EDREQUEST EQU INBUF
EDITBIND EQU CURB

EDDRIVEASK:
        LD HL,EDDRIVEMSG
        CALL ASKCHOICE
        SUB 'A'
        CP 1
        JP C,MENU
        CP 4
        JP NC,MENU
        RET
EDFROMDRIVE:
        CALL EDDISCARD
        CALL EDDRIVEASK
        CALL EDCAPTURE
        JP C,EDERROR
        CALL EDCLEARID
        CALL EDEXPAND
        LD A,(EDLOGICAL)
        ADD A,'A'
        LD (EDSOURCE),A
        JP EDSTART
EDBLANK:CALL EDDISCARD
        CALL EDCLEARID
        LD HL,EDITBIND
        LD DE,EDITBIND+1
        LD BC,63
        LD (HL),0
        LDIR
        CALL EDEXPAND
        LD A,'-'
        LD (EDSOURCE),A
        JP EDSTART
EDFROMCAT:
        CALL EDDISCARD
        LD HL,EDFILEMSG
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,MENU
        OR A
        JR Z,EDUSEWORK
        CALL PARSENAME
        CALL TOINPUT
        LD HL,INPUT
        LD DE,EDTEMPFILE
        LD BC,12
        LDIR
        LD A,2
        LD (ACTION),A
        JP READSOURCE
EDUSEWORK:
        LD HL,DEFAULTNAME
        LD DE,EDTEMPFILE
        LD BC,12
        LDIR
        LD HL,WORKBUF
        LD DE,FDFRAM
        LD BC,(WORKLEN)
        LD (FDBLEN),BC
        LDIR
EDCATREADY:
        LD HL,EDCATMSG
        CALL ASK
        LD HL,FDFRAM+128
        LD A,(FDFRAM+8)
        LD B,A
        OR A
        JP Z,EDERROR
EDSEARCH:PUSH HL
        PUSH BC
        LD DE,ANSWER
        LD B,8
EDIDMATCH:
        LD A,(DE)
        OR A
        JR NZ,EDLETTER
        LD A,' '
        JR EDMATCH
EDLETTER:INC DE
EDMATCH:CP (HL)
        JP NZ,EDNEXT
        INC HL
        DJNZ EDIDMATCH
        LD A,(DE)
        OR A
        JP NZ,EDNEXT
        POP BC
        POP HL
        PUSH HL
        POP IX
        LD DE,EDIDENT
        LD BC,40
        LDIR
        LD DE,EDITBIND+1
        LD BC,15
        LDIR
        LD A,(IX+55)
        LD (EDITBIND+17),A
        LD A,(IX+56)
        LD (EDITBIND+18),A
        LD A,(IX+57)
        LD (EDITBIND+16),A
        LD A,(IX+58)
        CALL FDBFLAGS
        LD A,B
        LD (EDITBIND+19),A
        XOR A
        LD (EDITBIND+52),A
        CALL EDUNIFORM
        LD L,(IX+60)
        LD H,(IX+61)
        LD DE,FDFRAM
        ADD HL,DE
        LD DE,EDIDS
        LD C,(IX+55)
        LD B,0
        LDIR
        BIT 7,(IX+58)
        JR Z,EDCATOK
        LD A,(HL)
        CP 081H
        JR NZ,EDCATCYL
        INC HL
        LD C,(HL)
        INC HL
        LD DE,EDCODES
        LDIR
        LD A,1
        LD (EDITBIND+52),A
EDCATCYL:
        LD A,(HL)
        CP 082H
        JR NZ,EDCATOK
        LD HL,EDITBIND+19
        SET 5,(HL)
EDCATOK:LD HL,EDTEMPFILE
        LD DE,EDFILE
        LD BC,12
        LDIR
        LD A,'#'
        LD (EDSOURCE),A
EDSTART:LD A,(EDSOURCE)
        CP 35
        LD A,0
        JR Z,EDPENDSET
        INC A
EDPENDSET:LD (EDPENDING),A
        LD A,1
        LD (EDPAGE),A
        XOR A
        LD (EDDIRTY),A
        LD (EDSLOT),A
        LD (EDMAPSTART),A
        LD HL,EDIDENT
        LD DE,EDOLDID
        LD BC,40
        LDIR
        LD HL,EDIDS
        LD DE,EDOLDMAP
        LD BC,510
        LDIR
        LD HL,EDITBIND
        LD DE,EDORIG
        LD BC,64
        LDIR
        JP EDSCREEN
EDNEXT: POP BC
        POP HL
        LD DE,64
        ADD HL,DE
        DEC B
        JP NZ,EDSEARCH
        JP EDERROR
EDCLEARID:
        LD HL,EDIDENT
        LD B,40
EDCLEAR:LD (HL),' '
        INC HL
        DJNZ EDCLEAR
        RET
EDDISCARD:
        LD A,(EDPENDING)
        OR A
        RET Z
        LD HL,EDDISMSG
        CALL ASKCHOICE
        CP 'Y'
        RET Z
        JP MENU
EDRESUME:LD A,(EDSOURCE)
        OR A
        JP Z,MENU
EDSCREEN:
        LD A,(0)
        CP 0C3H
        CALL Z,UI_CLEAR
        LD HL,(EDNOTICE)
        LD A,H
        OR L
        CALL NZ,PUTS
        LD HL,0
        LD (EDNOTICE),HL
        LD HL,EDTITLE
        CALL PUTS
        LD A,(EDPAGE)
        CALL COUNTDEC
        LD HL,EDSRCMSG
        CALL PUTS
        LD A,(EDSOURCE)
        CALL PUTC
        LD A,(EDSOURCE)
        CP 35
        JR NZ,EDHEADERID
        LD HL,EDFILE
        LD A,(EDFILE+1)
        OR A
        CALL NZ,SHOWNAME
EDHEADERID:CALL CRLF
        LD HL,EDIDENT
        LD DE,EDOLDID
        LD B,8
        CALL EDMARKTEXT
        LD B,8
        CALL EDFIXED
        LD DE,EDOLDID+8
        LD B,32
        CALL EDMARKTEXT
        LD B,32
        CALL EDFIXED
        LD HL,CLEANSTATE
        LD A,(EDDIRTY)
        OR A
        JR Z,EDSTATE
        LD HL,MODSTATE
EDSTATE:CALL PUTS
        CALL EDTABLE
        LD A,'A'
EDROW:  LD (EDKEY),A
        LD A,(IY+0)
        CP 255
        JR Z,EDOPTIONS
        LD A,(EDKEY)
        CALL PUTC
        LD A,' '
        CALL PUTC
        LD L,(IY+2)
        LD H,(IY+3)
        CALL PUTS
        CALL EDADDR
        LD A,(IY+1)
        CP 3
        JR C,EDWHOLE
        CALL EDBITMASK
        LD B,A
        LD A,(DE)
        XOR (HL)
        AND B
        JR Z,EDBITVAL
        LD A,'*'
        CALL PUTC
EDBITVAL:LD A,(HL)
        AND B
        LD A,'0'
        JR Z,EDBITSHOW
        INC A
EDBITSHOW:CALL PUTC
        JR EDENDROW
EDWHOLE:LD A,(DE)
        CP (HL)
        JR NZ,EDSTAR
        LD A,(IY+1)
        CP 2
        JR NZ,EDVALUE
        INC DE
        INC HL
        LD A,(DE)
        CP (HL)
        DEC HL
        JR Z,EDVALUE
EDSTAR: LD A,'*'
        CALL PUTC
EDVALUE:LD E,(HL)
        LD D,0
        LD A,(IY+1)
        CP 2
        JR NZ,EDSHOWVAL
        INC HL
        LD D,(HL)
EDSHOWVAL:
        EX DE,HL
        CALL EDPRINT
EDENDROW:CALL CRLF
        LD DE,4
        ADD IY,DE
        LD A,(EDKEY)
        INC A
        JR EDROW
EDOPTIONS:
        LD A,(EDPAGE)
        CP 1
        CALL Z,EDLAYOUT
        LD A,(EDPAGE)
        CP 2
        CALL Z,EDMAPSHOW
        LD HL,EDOPTS
        CALL ASKCHOICE
        CP 3
        JP Z,MENU
        CP 'Q'
        JP Z,MENU
        CP '1'
        JR C,EDCOMMAND
        CP '4'
        JR NC,EDCOMMAND
        SUB '0'
        LD (EDPAGE),A
        JP EDSCREEN
EDCOMMAND:
        CP 'V'
        JP Z,EDVALIDATE
        CP 'S'
        JP Z,EDSAVE
        CP '>'
        JP Z,EDMAPNEXT
        CP '<'
        JP Z,EDMAPPREV
        CP 'I'
        JR NZ,EDNOTID
        LD A,(EDPAGE)
        CP 1
        JP Z,EDIDEDIT
        LD A,'I'
EDNOTID:
        CP 'N'
        JP Z,EDNAMEEDIT
        CP 'M'
        JP Z,EDMAP
        SUB 'A'
        JP C,EDSCREEN
        LD B,A
        CALL EDTABLE
EDPICK: LD A,(IY+0)
        CP 255
        JP Z,EDSCREEN
        LD A,B
        OR A
        JR Z,EDCHOSEN
        LD DE,4
        ADD IY,DE
        DJNZ EDPICK
EDCHOSEN:
        LD A,(IY+0)
        CP 255
        JP Z,EDSCREEN
        PUSH IY
        CALL EDNUM
        POP IY
        PUSH DE
        CALL EDADDR
        POP DE
        LD A,(IY+1)
        CP 3
        JR C,EDSTDSET
        LD A,D
        OR A
        JP NZ,EDERROR
        LD A,E
        CP 2
        JP NC,EDERROR
        CALL EDBITMASK
        LD B,A
        CPL
        AND (HL)
        LD (HL),A
        LD A,E
        OR A
        JR Z,EDMOD
        LD A,(HL)
        OR B
        LD (HL),A
        JR EDMOD
EDSTDSET:LD A,(IY+1)
        CP 2
        JR Z,EDSETWORD
        LD A,D
        OR A
        JP NZ,EDERROR
        LD (HL),E
        JR EDMOD
EDSETWORD:LD (HL),E
        INC HL
        LD (HL),D
EDMOD:  LD A,1
        LD (EDPENDING),A
        LD (EDDIRTY),A
        JP EDSCREEN
EDADDR: LD E,(IY+0)
        LD D,0
        LD HL,EDORIG
        ADD HL,DE
        PUSH HL
        LD HL,EDITBIND
        ADD HL,DE
        POP DE
        RET
EDTABLE:LD A,(EDPAGE)
        LD IY,EDGEOM
        DEC A
        RET Z
        LD IY,EDADDRESS
        DEC A
        RET Z
        LD IY,EDDPB
        RET
EDNUM:  LD HL,EDNUMMSG
        CALL ASK
        LD A,(ANSWER)
        CP 3
        JP Z,EDSCREENRESET
        LD HL,ANSWER
        JP SCALAR
EDSCREENRESET:
        LD SP,STACKTOP
        JP EDSCREEN
EDFIXED:LD A,(HL)
        CP ' '
        JR NZ,EDFIXEDVAL
        PUSH HL
        LD HL,EDUNSET
        CALL PUTS
        POP HL
        LD E,B
        LD D,0
        ADD HL,DE
        RET
EDFIXEDVAL:LD A,' '
        CALL PUTC
EDFIXLP:LD A,(HL)
        CALL PUTC
        INC HL
        DJNZ EDFIXLP
        RET
EDIDEDIT:LD DE,EDIDENT
        LD B,8
        JR EDEDITTEXT
EDNAMEEDIT:LD DE,EDIDENT+8
        LD B,32
EDEDITTEXT:
        PUSH BC
        PUSH DE
        LD A,B
        CP 32
        LD A,0
        JR NZ,EDTEXTCASE
        INC A
EDTEXTCASE:LD (RAWANSWER),A
        LD HL,EDTXTMSG
        CALL ASK
        XOR A
        LD (RAWANSWER),A
        POP DE
        POP BC
        LD HL,ANSWER
        LD A,(HL)
        CP 3
        JP Z,EDSCREEN
        PUSH HL
        PUSH BC
EDTESTLEN:
        LD A,(HL)
        OR A
        JR Z,EDLENOK
        INC HL
        DJNZ EDTESTLEN
        LD A,(HL)
        OR A
        JP NZ,EDERROR
EDLENOK:POP BC
        POP HL
EDTEXTLP:LD A,(HL)
        OR A
        JR Z,EDPAD
        INC HL
        JR EDSTORE
EDPAD:  LD A,' '
EDSTORE:LD (DE),A
        INC DE
        DJNZ EDTEXTLP
        JP EDMOD
EDMAP:  LD HL,EDSLOTMSG
        CALL PUTS
        CALL EDNUM
        LD A,D
        OR A
        JP NZ,EDERROR
        LD A,E
        DEC A
        LD HL,EDITBIND+17
        CP (HL)
        JP NC,EDERROR
        LD (EDSLOT),A
        LD HL,EDSECTMSG
        CALL PUTS
        CALL EDNUM
        LD A,D
        OR A
        JP NZ,EDERROR
        LD A,E
        LD (EDTMP),A
        LD HL,EDSIZEQ
        CALL PUTS
        CALL EDNUM
        LD A,D
        OR A
        JP NZ,EDERROR
        LD A,E
        CP 4
        JP NC,EDERROR
        LD C,A
        LD A,(EDSLOT)
        LD E,A
        LD D,0
        LD HL,EDIDS
        ADD HL,DE
        LD A,(EDTMP)
        LD (HL),A
        LD A,(EDITBIND+52)
        OR A
        JR NZ,EDALREADYMIX
        PUSH BC
        PUSH DE
        LD HL,EDCODES
        LD DE,EDCODES+1
        LD A,(EDITBIND+18)
        LD (HL),A
        LD BC,254
        LDIR
        POP DE
        POP BC
EDALREADYMIX:LD HL,EDCODES
        ADD HL,DE
        LD (HL),C
        LD A,1
        LD (EDITBIND+52),A
        JP EDMOD
EDUNIFORM:
        LD HL,EDCODES
        LD DE,EDCODES+1
        LD BC,254
        LD A,(EDITBIND+18)
        LD (HL),A
        LDIR
        LD HL,EDIDS
        LD DE,EDIDS+1
        LD BC,254
        LD (HL),0
        LDIR
        RET
EDEXPAND:
        CALL EDUNIFORM
        LD HL,EDITBIND+20
        LD DE,EDIDS
        LD BC,32
        LDIR
        LD A,(EDITBIND+52)
        OR A
        RET Z
        LD HL,EDITBIND+53
        LD DE,EDCODES
        LD B,8
EDUNBYTE:LD C,(HL)
        INC HL
        PUSH BC
        LD B,4
EDUNPAIR:LD A,C
        AND 3
        LD (DE),A
        INC DE
        SRL C
        SRL C
        DJNZ EDUNPAIR
        POP BC
        DJNZ EDUNBYTE
        RET
EDPRINT:LD DE,10000
        LD B,0
        CALL EDDIG
        LD DE,1000
        CALL EDDIG
        LD DE,100
        CALL EDDIG
        LD DE,10
        CALL EDDIG
        LD A,L
        ADD A,'0'
        JP PUTC
EDDIG:  LD C,0
EDSUB:  OR A
        SBC HL,DE
        JR C,EDREM
        INC C
        JR EDSUB
EDREM:  ADD HL,DE
        LD A,B
        OR C
        RET Z
        LD B,1
        LD A,C
        ADD A,'0'
        JP PUTC
EDERROR:LD HL,EDBAD
        JP EXITMSG
EDDRIVEMSG:DB 'Logical drive B, C or D: ',0
EDCATMSG:DB 'Catalogue ID: ',0
EDDISMSG:DB 'Discard edited working format (Y/N)? ',0
EDTITLE:DB 13,10,'Format editor  Page ',0
EDSRCMSG:DB '/3  Source (drive, # catalogue, - blank): ',0
EDOPTS: DB '1-3 Page  I ID  N Name  M Map  V Validate  S Save/apply  Q Back: ',0
EDNUMMSG:DB 'Value: ',0
EDTXTMSG:DB 'New value: ',0
EDSLOTMSG:DB 'Slot 1-255. ',0
EDSECTMSG:DB 'Sector ID 0-255. ',0
EDSIZEQ:DB 'Size code 0-3 (128/256/512/1024). ',0
EDBAD:  DB 'Invalid selection, binding or field.',13,10,0
EDSOURCE:DB 0
EDDIRTY:DB 0
EDPAGE: DB 0
EDKEY:  DB 0
EDSLOT: DB 0
EDTMP:  DB 0
EDIDENT:DS 40
EDORIG: DS 64
EDGEOM:
        DB 16,1
        DW EDGEOM0
        DB 17,1
        DW EDGEOM1
        DB 18,1
        DW EDGEOM2
        DB 19,9
        DW EDGEOM3
        DB 19,10
        DW EDGEOM4
        DB 19,7
        DW EDGEOM5
        DB 19,8
        DW EDGEOM6
        DB 255
EDGEOM0: DB 'Cylinders: ',0
EDGEOM1: DB 'Sectors per surface: ',0
EDGEOM2: DB 'Max size (0=128 1=256 2=512 3=1024): ',0
EDGEOM3: DB 'Double sided: ',0
EDGEOM4: DB 'MFM recording: ',0
EDGEOM5: DB 'Inverted: ',0
EDGEOM6: DB 'Logical track (0=surface 1=cylinder): ',0
EDADDRESS:
        DB 19,4
        DW EDADDRESS0
        DB 19,3
        DW EDADDRESS1
        DB 19,5
        DW EDADDRESS2
        DB 19,6
        DW EDADDRESS3
        DB 52,1
        DW EDADDRESS4
        DB 255
EDADDRESS0: DB 'Side order (0=alternating 1=side-major): ',0
EDADDRESS1: DB 'Reverse side 1: ',0
EDADDRESS2: DB 'Continuous track IDs: ',0
EDADDRESS3: DB 'Continuous sector IDs: ',0
EDADDRESS4: DB 'Mixed sizes: ',0
EDDPB:
        DB 1,2
        DW EDDPB0
        DB 3,1
        DW EDDPB1
        DB 4,1
        DW EDDPB2
        DB 5,1
        DW EDDPB3
        DB 6,2
        DW EDDPB4
        DB 8,2
        DW EDDPB5
        DB 10,1
        DW EDDPB6
        DB 11,1
        DW EDDPB7
        DB 12,2
        DW EDDPB8
        DB 14,2
        DW EDDPB9
        DB 255
EDDPB0: DB 'SPT (records per logical track): ',0
EDDPB1: DB 'BSH (block shift): ',0
EDDPB2: DB 'BLM (block mask): ',0
EDDPB3: DB 'EXM (extent mask): ',0
EDDPB4: DB 'DSM (last allocation block): ',0
EDDPB5: DB 'DRM (last directory entry): ',0
EDDPB6: DB 'AL0 (directory bitmap high): ',0
EDDPB7: DB 'AL1 (directory bitmap low): ',0
EDDPB8: DB 'CKS (directory check size): ',0
EDDPB9: DB 'OFF (reserved logical tracks): ',0
EDVALIDATE:
        CALL EDMAKE
        LD HL,EDOKMSG
        LD (EDNOTICE),HL
        JP EDSCREEN
EDSAVE: LD HL,EDACTIONS
        CALL ASKCHOICE
        CP 'W'
        JP Z,EDWRITECAT
        CP 'D'
        JR Z,EDAPPLY
        CP 'K'
        JP NZ,EDSCREEN
EDPUTCAT:
        LD A,(EDIDENT)
        CP ' '
        JP Z,EDERROR
        LD A,(EDIDENT+8)
        CP ' '
        JP Z,EDERROR
        CALL EDMAKE
        LD A,1
        LD A,3
        LD (ACTION),A
        JP MERGEIMPORT
EDAPPLY:CALL EDMAKE
        XOR A
        CALL FDBBIND
        JP C,EDERROR
        CALL EDDRIVEASK
        LD (EDTARGET),A
        ADD A,'A'
        CALL PUTC
        LD HL,EDCONFIRM
        CALL ASKCHOICE
        CP 'Y'
        JP NZ,EDSCREEN
        LD A,(EDTARGET)
        CALL EDSETDRIVE
        JP C,EDERROR
        LD HL,EDAPPLIED
        LD (EDNOTICE),HL
        JP EDSCREEN
; Materialize a one-entry canonical catalogue, using the same DPB/geometry
; checks as import. Identity placeholders exist only for drive validation.
EDMAKE: LD HL,FDFRAM
        LD DE,FDFRAM+1
        LD BC,191
        LD (HL),0
        LDIR
        LD HL,HEADER
        LD DE,FDFRAM
        LD BC,16
        LDIR
        LD IX,FDFRAM+128
        LD HL,EDIDENT
        LD DE,FDFRAM+128
        LD BC,40
        LDIR
        LD A,(IX+0)
        CP ' '
        JR NZ,EDHASID
        LD (IX+0),'X'
EDHASID:LD A,(IX+8)
        CP ' '
        JR NZ,EDHASNAME
        LD (IX+8),'?'
EDHASNAME:
        LD HL,EDITBIND+1
        LD DE,FDFRAM+168
        LD BC,15
        LDIR
        LD A,(EDITBIND+16)
        LD (IX+57),A
        LD A,(EDITBIND+18)
        LD (IX+56),A
        LD A,(EDITBIND+17)
        OR A
        JP Z,EDERROR
        LD (IX+55),A
        LD (IX+59),A
        LD (HASIDS),A
        LD C,A
        LD B,0
        LD HL,EDIDS
        LD DE,POOLRAM
        LDIR
        LD (POOLPTR),DE
        LD HL,POOLRAM-FDFRAM
        LD (IX+60),L
        LD (IX+61),H
        LD E,0
EDFLAGS:LD A,E
        CALL FDBFLAGS
        LD A,(EDITBIND+19)
        AND 0DFH
        CP B
        JR Z,EDGOTFLAGS
        INC E
        JR EDFLAGS
EDGOTFLAGS:LD (IX+58),E
        LD A,(EDITBIND+19)
        AND 020H
        LD (CYLINDER),A
        XOR A
        LD (HASSIZES),A
        LD A,(EDITBIND+52)
        CP 2
        JP NC,EDERROR
        OR A
        JR Z,EDPACK
        LD A,(HASIDS)
        LD (HASSIZES),A
        LD C,A
        LD B,0
        LD HL,EDCODES
        LD DE,SIZES
        LDIR
EDPACK: LD HL,SEEN
        LD B,25
EDSEEN: LD (HL),1
        INC HL
        DJNZ EDSEEN
        CALL FINALFORMAT
        LD A,1
        LD (FCOUNT),A
        CALL PACKCAT
        CALL FDBVALID
        JP C,EDERROR
        CALL SEMANTICS
        RET
EDNOTICE:DW 0
EDTARGET:DB 0
EDACTIONS:DB 'D Apply to drive, K Put in catalogue, W Write catalogue, other Cancel: ',0
EDCONFIRM:DB ': Apply working format to this drive (Y/N)? ',0
EDAPPLIED:DB 'Active drive binding updated.',13,10,0
EDOKMSG:DB 'Format validates.',13,10,0

EDFILEMSG: DB 'Source filename (Return for working catalogue): ',0
EDIDS: DS 255
EDCODES: DS 255

EDBITMASK:LD A,(IY+1)
        SUB 3
        LD B,A
        OR A
        LD A,1
        RET Z
EDBITLP:ADD A,A
        DJNZ EDBITLP
        RET
EDMARKTEXT:
        PUSH HL
        CALL CMPFIELD
        POP HL
        RET Z
        LD A,'*'
        JP PUTC
EDMAPNEXT:
        LD A,(EDMAPSTART)
        ADD A,8
        JP C,EDSCREEN
        LD HL,EDITBIND+17
        CP (HL)
        JP NC,EDSCREEN
        LD (EDMAPSTART),A
        JP EDSCREEN
EDMAPPREV:
        LD A,(EDMAPSTART)
        SUB 8
        JP C,EDSCREEN
        LD (EDMAPSTART),A
        JP EDSCREEN
EDMAPSHOW:
        LD HL,EDMAPTITLE
        CALL PUTS
        LD A,(EDMAPSTART)
        LD E,A
        LD D,0
        LD B,8
EDMAPROW:
        LD A,(EDITBIND+17)
        CP E
        RET Z
        RET C
        PUSH BC
        PUSH DE
        LD A,E
        INC A
        CALL COUNTDEC
        LD A,' '
        CALL PUTC
        POP DE
        PUSH DE
        LD HL,EDIDS
        ADD HL,DE
        LD A,(HL)
        LD HL,EDOLDMAP
        ADD HL,DE
        CP (HL)
        PUSH AF
        LD A,'*'
        CALL NZ,PUTC
        POP AF
        CALL COUNTDEC
        LD A,' '
        CALL PUTC
        POP DE
        PUSH DE
        CALL EDSLOTCODE
        LD HL,EDOLDCODES
        ADD HL,DE
        CP (HL)
        PUSH AF
        LD A,'*'
        CALL NZ,PUTC
        POP AF
        CALL SIZEVALUE
        CALL EDPRINT
        CALL CRLF
        POP DE
        INC E
        POP BC
        DJNZ EDMAPROW
        RET
EDSLOTCODE:
        LD A,(EDITBIND+52)
        OR A
        LD A,(EDITBIND+18)
        JR Z,EDSLOTLIM
        LD HL,EDCODES
        ADD HL,DE
        LD A,(HL)
EDSLOTLIM:AND 3
        RET
; Use effective physical records per logical track even while SPT is stale.
EDLAYOUT:
        LD BC,0
        LD DE,0
EDRECLP:LD A,(EDITBIND+17)
        CP E
        JR Z,EDRECDONE
        CALL EDSLOTCODE
        LD H,A
        LD L,1
EDRECSHIFT:LD A,H
        OR A
        JR Z,EDRECSUM
        SLA L
        DEC H
        JR EDRECSHIFT
EDRECSUM:LD H,0
        ADD HL,BC
        LD B,H
        LD C,L
        INC E
        JR EDRECLP
EDRECDONE:
        LD H,B
        LD L,C
        LD A,(EDITBIND+19)
        BIT 5,A
        JR Z,EDTRACKUNIT
        BIT 6,A
        JR Z,EDTRACKUNIT
        ADD HL,HL
EDTRACKUNIT:LD (EDLRECS),HL
        LD A,(EDITBIND+16)
        LD L,A
        LD H,0
        LD A,(EDITBIND+19)
        BIT 6,A
        JR Z,EDTRACKCOUNT
        BIT 5,A
        JR NZ,EDTRACKCOUNT
        ADD HL,HL
EDTRACKCOUNT:LD (EDTRACKS),HL
        LD DE,(EDLRECS)
        CALL MULTIPLY
        LD HL,EDCAPMSG
        CALL PUTS
        CALL EDBYTES
        LD HL,EDOFFMSG
        CALL PUTS
        LD HL,(EDITBIND+14)
        LD DE,(EDLRECS)
        CALL MULTIPLY
        CALL EDBYTES
        LD HL,EDMAXMSG
        CALL PUTS
        LD HL,(EDTRACKS)
        LD DE,(EDITBIND+14)
        OR A
        SBC HL,DE
        JR C,EDNOBLOCK
        LD DE,(EDLRECS)
        CALL MULTIPLY
        LD HL,(PRODUCT)
        LD DE,(PRODUCT+2)
        LD A,D
        OR E
        JR Z,EDALLOC
        LD DE,1
        LD HL,0
EDALLOC:LD A,(EDITBIND+3)
        CP 8
        JR NC,EDNOBLOCK
        OR A
        JR Z,EDMAXDONE
        LD B,A
EDMAXLP:SRL D
        RR E
        RR H
        RR L
        DJNZ EDMAXLP
EDMAXDONE:
        LD A,H
        OR L
        OR E
        JR Z,EDNOBLOCK
        DEC HL
        PUSH HL
        CALL EDPRINT
        POP HL
        LD DE,(EDITBIND+6)
        OR A
        SBC HL,DE
        JP NC,CRLF
EDNOBLOCK:LD HL,EDWARN
        JP PUTS
EDBYTES:LD HL,(PRODUCT)
        LD DE,(PRODUCT+2)
        LD B,7
EDBYTESLP:ADD HL,HL
        RL E
        RL D
        DJNZ EDBYTESLP
EDDEC32:LD B,32
        XOR A
EDDIV10:ADD HL,HL
        RL E
        RL D
        RLA
        CP 10
        JR C,EDDIVNEXT
        SUB 10
        INC L
EDDIVNEXT:DJNZ EDDIV10
        PUSH AF
        LD A,H
        OR L
        OR E
        OR D
        CALL NZ,EDDEC32
        POP AF
        ADD A,'0'
        JP PUTC
EDCAPMSG:DB 'Raw bytes: ',0
EDOFFMSG:DB '  Directory byte: ',0
EDMAXMSG:DB '  Maximum DSM: ',0
EDWARN:DB '  ! invalid allocation',13,10,0
EDFILEEND:DB 0
EDMAPTITLE:DB 'Slot ID Bytes  (< previous, > next)',13,10,0
EDLRECS:DW 0
EDTRACKS:DW 0
EDMAPSTART:DB 0
EDOLDID:DS 40
EDOLDMAP:DS 255
EDOLDCODES:DS 255

EDINCLUDE:LD A,(EDPENDING)
        OR A
        RET Z
        LD HL,EDINCMSG
        CALL ASKCHOICE
        CP 'N'
        RET Z
        CP 'Y'
        JP NZ,MENU
        LD A,1
        LD (EDAFTER),A
        JP EDPUTCAT
EDEXITCHECK:LD A,(EDPENDING)
        OR A
        RET Z
        LD HL,EDQUITMSG
        CALL ASKCHOICE
        CP 'D'
        RET Z
        CP 'S'
        JP NZ,MENU
        LD A,2
        LD (EDAFTER),A
        JP EDPUTCAT
EDCOMMITTED:
        LD HL,IMPORTBUF+128
        LD DE,EDIDENT
        LD BC,40
        LDIR
        XOR A
        LD (EDPENDING),A
        LD (EDDIRTY),A
        LD HL,EDITBIND
        LD DE,EDORIG
        LD BC,64
        LDIR
        LD HL,EDIDS
        LD DE,EDOLDMAP
        LD BC,510
        LDIR
        LD HL,EDIDENT
        LD DE,EDOLDID
        LD BC,40
        LDIR
        LD A,(EDAFTER)
        OR A
        JP Z,MENU
        CALL DOSAVE
        LD A,(EDAFTER)
        CP 2
        JP Z,EXIT
        JP MENU
EDFILE: DS 12
EDTEMPFILE: DS 12
EDAFTER:DB 0
EDPENDING:DB 0
EDINCMSG:DB 'Include working format before saving (Y/N, other cancels)? ',0
EDQUITMSG:DB 'Working format pending: S Save, D Discard, C Cancel: ',0

EDUNSET:DB ' <unset>',0
