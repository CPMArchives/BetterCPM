; RomWBW backend for the shared CONFIG menus and pending BCST/PDS editor.
WB_ROUTE:
        LD A,(80H)
        LD E,A
        LD D,0
        LD HL,81H
        ADD HL,DE
        LD (HL),0
        LD HL,81H
        XOR A
        LD (WB_QUOTE),A
WB_SCAN:
        LD A,(HL)
        OR A
        RET Z
        CP '"'
        JR NZ,WB_SLASH
        LD A,(WB_QUOTE)
        XOR 1
        LD (WB_QUOTE),A
        JR WB_ADV
WB_SLASH:
        LD A,(WB_QUOTE)
        OR A
        JR NZ,WB_ADV
        LD A,(HL)
        CP '/'
        JR NZ,WB_ADV
        PUSH HL
        LD DE,WB_LOGOPT
        CALL U_PREFIX
        POP HL
        JR Z,WB_CLI
        PUSH HL
        LD DE,WB_UNITOPT
        CALL U_PREFIX
        POP HL
        JR Z,WB_CLI
        PUSH HL
        LD DE,WB_UNBOPT
        CALL U_PREFIX
        POP HL
        JR Z,WB_CLI
        PUSH HL
        LD DE,WB_SAVEOPT
        CALL U_PREFIX
        POP HL
        JR Z,WB_CLI
WB_ADV:
        INC HL
        JR WB_SCAN
WB_CLI:
        CALL WB_BLOCK
        JP DONE
WB_BLOCK:
        LD HL,WB_FCB+12
        LD DE,WB_FCB+13
        LD BC,23
        LD (HL),0
        LDIR
        LD DE,WB_FCB
        LD C,15
        CALL STA0CALL
        INC A
        JP Z,WB_UNSUP
        LD HL,08000H
WB_BLOAD:
        PUSH HL
        EX DE,HL
        LD C,26
        CALL BDOS
        LD DE,WB_FCB
        LD C,20
        CALL STA0CALL
        POP HL
        OR A
        JR NZ,WB_BEOF
        LD DE,128
        ADD HL,DE
        LD A,H
        CP 08EH
        JP NC,WB_UNSUP
        JR WB_BLOAD
WB_BEOF:
        CP 1
        JP NZ,WB_UNSUP
        LD DE,WB_FCB
        LD C,16
        CALL STA0CALL
        LD DE,80H
        LD C,26
        CALL BDOS
        CALL 08000H
        RET
WB_TEXT:
        LD DE,81H
        LD B,0
WB_TLOOP:
        LD A,(HL)
        OR A
        JR Z,WB_TDONE
        LD (DE),A
        INC DE
        INC HL
        INC B
        JR WB_TLOOP
WB_TDONE:
        LD A,B
        LD (80H),A
        XOR A
        LD (DE),A
        RET
WB_BMENU:
        LD HL,WB_BTITLE
        CALL HEADER
        LD HL,WB_SHOWARG
        CALL WB_TEXT
        CALL WB_BLOCK
        LD HL,WB_BHELP
        CALL PUTS
        LD HL,WB_SELTEXT
        CALL PUTS
        LD A,(WB_LOGICAL)
        CALL PUTC
        CALL CRLF
        CALL CHOICE
        CP 3
        JP Z,MAIN
        CP 'B'
        JR C,WB_BKEY
        CP 'E'
        JR NC,WB_BKEY
        LD (WB_LOGICAL),A
        JR WB_BMENU
WB_BKEY:
        CP 'N'
        JR Z,WB_BBIND
        CP 'U'
        JR Z,WB_BUNB
        CP 'S'
        JR Z,WB_BSAVE
        JR WB_BMENU
WB_BBIND:
        LD HL,WB_BPROM
        CALL EDNUMBER
        JR C,WB_BMENU
        LD A,D
        OR A
        JR NZ,WB_BMENU
        LD A,E
        CP 255
        JR Z,WB_BMENU
        LD (WB_NUMBER),A
        LD A,(WB_LOGICAL)
        LD (WB_BINDARG+9),A
        LD HL,WB_BINDARG
        CALL WB_TEXT
        LD A,(80H)
        LD E,A
        LD D,0
        LD HL,81H
        ADD HL,DE
        LD A,(WB_NUMBER)
        LD B,100
        CALL WB_DIGIT
        LD B,10
        CALL WB_DIGIT
        ADD A,'0'
        LD (HL),A
        INC HL
        LD (HL),0
        LD A,(80H)
        ADD A,3
        LD (80H),A
        JR WB_BCALL
WB_DIGIT:
        LD C,'0'
WB_DSUB:
        CP B
        JR C,WB_DDONE
        SUB B
        INC C
        JR WB_DSUB
WB_DDONE:
        LD (HL),C
        INC HL
        RET
WB_BUNB:
        LD A,(WB_LOGICAL)
        LD (WB_UNBARG+9),A
        LD HL,WB_UNBARG
        CALL WB_TEXT
        JR WB_BCALL
WB_BSAVE:
        LD HL,WB_SAVEARG
        CALL WB_TEXT
WB_BCALL:
        CALL WB_BLOCK
        CALL PAUSE
        JP WB_BMENU
WB_ALL:
        LD HL,WB_SAVEARG
        CALL WB_TEXT
        CALL WB_BLOCK
        JP STSAVE
WB_UNSUP:
        LD HL,WB_BADMSG
        CALL PUTS
        JP DONE
WB_SHOW:
        CALL WB_IOSHOW
        LD HL,WB_SHOWARG
        CALL WB_TEXT
        CALL WB_BLOCK
        CALL STFETCH
        LD HL,CF_SAVED
        CALL PUTS
        LD A,(STSTATE)
        CP 2
        JR Z,WB_SBAD
        LD A,(STPEND+8)
        OR A
        JR Z,WB_SOFF
        LD B,A
        LD HL,STPEND+16
WB_SPRINT:
        LD A,(HL)
        CALL PUTC
        INC HL
        DJNZ WB_SPRINT
        CALL CRLF
        JP WB_PSHOW
WB_SOFF:
        LD HL,CF_OFFMSG
        CALL PUTS
        JP WB_PSHOW
WB_SBAD:
        LD HL,CF_UNKNOWN
        CALL PUTS
        JP DONE
WB_PSHOW:
        LD HL,WB_PDSL
        CALL PUTS
        LD HL,STPEND+145
        LD B,3
WB_PCODES:
        LD A,(HL)
        PUSH BC
        PUSH HL
        CALL DECOUT
        LD A,' '
        CALL PUTC
        POP HL
        POP BC
        INC HL
        DJNZ WB_PCODES
        CALL CRLF
        JP DONE
; BWCF v3 at physical sector four owns saved IOBYTE and B's mapping.
WB_IOREAD:
        CALL SGDISKSET
        RET NZ
        LD HL,4
        LD (U_LBA),HL
        LD A,(U_BOOT)
        LD C,A
        LD B,013H
        LD HL,06000H
        CALL U_IO
        RET NZ
        LD HL,06000H
        CALL U_SUM
        RET NZ
        LD HL,(06000H)
        LD DE,05742H
        OR A
        SBC HL,DE
        RET NZ
        LD HL,(06002H)
        LD DE,04643H
        OR A
        SBC HL,DE
        RET NZ
        LD HL,(06004H)
        LD DE,00403H
        OR A
        SBC HL,DE
        LD A,H
        OR L
        RET NZ
        LD A,(06007H)
        LD (IO_OLD),A
        AND 3
        CP 1
        RET
WB_IOSHOW:
        LD HL,IO_LIVE
        CALL PUTS
        LD C,7
        CALL BDOS
        CALL DECOUT
        CALL CRLF
        CALL WB_IOREAD
        LD HL,IO_UNKNOWN
        JP NZ,PUTS
        LD HL,IO_SAVED
        CALL PUTS
        LD A,(IO_OLD)
        CALL DECOUT
        JP CRLF
WB_IOSET:
        CALL WB_IOREAD
        JP NZ,WB_IOERR
        LD A,(IO_NEW)
        CP 095H
        JR Z,WB_IOOK
        LD A,63
        CALL SGBIOS
        LD D,095H
        LD A,(IO_NEW)
        LD E,A
        LD C,4
WB_IOCAP:
        LD A,D
        XOR E
        AND 3
        JR Z,WB_IONXT
        LD A,E
        AND 3
        LD B,A
        INC B
        LD A,1
WB_IOBIT:
        DEC B
        JR Z,WB_IOCHK
        RLCA
        JR WB_IOBIT
WB_IOCHK:
        AND L
        JP Z,WB_IOERR
WB_IONXT:
        LD A,D
        RRCA
        RRCA
        LD D,A
        LD A,E
        RRCA
        RRCA
        LD E,A
        LD B,4
WB_IOSH:
        SRL H
        RR L
        DJNZ WB_IOSH
        DEC C
        JR NZ,WB_IOCAP
WB_IOOK:
        LD HL,IO_ASK
        CALL PUTS
        CALL CC_ASK
        CP 'Y'
        JP NZ,WB_IODONE
        LD HL,06000H
        LD DE,06400H
        LD BC,512
        LDIR
        LD A,(IO_NEW)
        LD (06007H),A
        LD HL,0
        LD (06008H),HL
        LD HL,06000H
        CALL U_SUM
        LD HL,0
        OR A
        SBC HL,DE
        LD (06008H),HL
        LD HL,06000H
        CALL WB_PUTCFG
        JR NZ,WB_IOROLL
        LD HL,IO_OK
        CALL PUTS
        JP WB_IODONE
WB_IOROLL:
        LD HL,06400H
        CALL WB_PUTCFG
        LD HL,WB_IORMSG
        JR Z,WB_IOPR
        LD HL,STDAMAGED
WB_IOPR:
        CALL PUTS
        JP WB_IODONE
WB_PUTCFG:
        LD (WB_CFGPTR),HL
        LD A,(U_BOOT)
        LD C,A
        LD B,014H
        CALL U_IO
        RET NZ
        LD A,(U_BOOT)
        LD C,A
        LD B,013H
        LD HL,06200H
        CALL U_IO
        RET NZ
        LD HL,(WB_CFGPTR)
        LD DE,06200H
        LD BC,512
        JP SGCMP
WB_IOERR:
        LD HL,IO_ERROR
        CALL PUTS
WB_IODONE:
        LD A,(CF_MODE)
        OR A
        JP NZ,DONE
        CALL PAUSE
        JP MAIN
WB_SGIO:
        CALL WB_SGRAW
        RET NZ
        LD A,(SGWRITE)
        OR A
        RET Z
        LD A,(SGINDEX)
        CP 3
        RET NC
        OR A
        RET Z
        LD HL,256
        LD (WB_EXTRA),HL
        LD HL,(SGIOBUF)
        PUSH HL
        LD A,1
        CALL WB_SGRAW
        CALL Z,SGVERIFY
        POP HL
        LD (SGIOBUF),HL
        PUSH AF
        LD HL,0
        LD (WB_EXTRA),HL
        POP AF
        RET
WB_EXTRA: DW 0
WB_QUOTE: DB 0
WB_NUMBER: DB 0
WB_FCB: DB 1,'BLOCKCFGOVL'
        DS 24
WB_LOGOPT: DB '/LOGICAL=',0
WB_UNITOPT: DB '/UNIT=',0
WB_UNBOPT: DB '/UNBIND',0
WB_SAVEOPT: DB '/SAVE',0
WB_SHOWARG: DB '/SHOW',0
WB_SAVEARG: DB '/SAVE',0
WB_UNBARG: DB '/LOGICAL=B /UNBIND',0
WB_BINDARG: DB '/LOGICAL=B /UNIT=',0
WB_BTITLE: DB 'RomWBW block bindings',0
WB_BHELP: DB 'B/C/D select drive; N bind; U unbind; S save all; Ctrl-C back.',13,10,0
WB_LOGICAL: DB 'B'
WB_SELTEXT: DB 'Selected drive: ',0
WB_BPROM: DB 'HBIOS unit (decimal, 0..254): ',0
WB_BADMSG: DB 'Unsupported block operation, or restore BLOCKCFG.OVL.',13,10,0
WB_PDSL: DB 'Saved H/M/V choices: ',0
WB_CFGPTR: DW 0
WB_IORMSG: DB 'IOBYTE save failed; original settings restored.',13,10,0
