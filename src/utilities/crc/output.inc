; Two independent staged destinations. Descriptor offsets deliberately <128.
; 0 final FCB,36 temporary FCB,72 backup FCB;108 drive,109 user,
; 110 status (0 absent/1 pending/2 invalid),111 buffered bytes,
; 112 sections,113 old-final moved,114 buffer pointer.
WMASTER:
        LD HL,WDMASTER
        LD BC,116
        CALL ZERO
        LD HL,WDLOCAL
        LD BC,116
        CALL ZERO
        LD A,(MASTSET)
        OR A
        RET Z
        LD HL,MASTER
        LD DE,WDMASTER
        LD BC,36
        LDIR
        LD A,(MASTER+36)
        LD (WDMASTER+108),A
        LD A,(MASTER+37)
        LD (WDMASTER+109),A
        LD HL,WMBUFFER
        LD (WDMASTER+114),HL
        LD IX,WDMASTER
        JP WOPEN
WLOCAL:
        LD HL,WDLOCAL
        LD BC,116
        CALL ZERO
        LD A,(LOCALSET)
        OR A
        RET Z
        LD A,(MASTSET)
        OR A
        JR Z,WLOCALNE
        LD A,(MASTER+36)
        LD B,A
        LD A,(DRIVE)
        CP B
        JR NZ,WLOCALNE
        LD A,(MASTER+37)
        LD B,A
        LD A,(USER)
        CP B
        JR NZ,WLOCALNE
        LD HL,MASTER+1
        LD DE,LOCAL+1
        CALL CMPNAME
        RET Z
WLOCALNE:
        LD HL,LOCAL
        LD DE,WDLOCAL
        LD BC,36
        LDIR
        LD A,(DRIVE)
        LD (WDLOCAL+108),A
        LD A,(USER)
        LD (WDLOCAL+109),A
        LD HL,WLBUFFER
        LD (WDLOCAL+114),HL
        LD IX,WDLOCAL
        JP WOPEN
WSELECT:
        LD E,(IX+108)
        LD C,14
        CALL BDOS
        LD E,(IX+109)
        LD C,32
        JP BDOS
WSOURCE:
        LD A,(DRIVE)
        LD E,A
        LD C,14
        CALL BDOS
        LD A,(USER)
        LD E,A
        LD C,32
        JP BDOS
WOPEN:
        LD A,(CANCEL)
        OR A
        RET NZ
        CALL WSELECT
        LD A,(IX+108)
        INC A
        LD (IX+0),A
        PUSH IX
        POP DE
        LD C,15
        CALL BDOS
        CP 255
        JR Z,WCREATE
        LD C,16
        CALL BDOS
        LD A,(ALLYES)
        OR A
        JR NZ,WCREATE
        CALL WPROMPT
        LD A,(CANCEL)
        OR A
        JP NZ,WSOURCE
        LD A,(WRESPONS)
        CP 'N'
        JR NZ,WCREATE
        LD HL,OUTDECLI
        CALL INC32
        JP WSOURCE
WCREATE:
        ; BDOS open may have changed final extent state; rename needs clean FCB.
        PUSH IX
        POP HL
        LD DE,12
        ADD HL,DE
        LD BC,24
        CALL ZERO
        CALL WUNIQUET
        JR C,WOPENFAI
        CALL WTRESET
        PUSH IX
        POP DE
        LD HL,36
        ADD HL,DE
        EX DE,HL
        LD C,22
        CALL BDOS
        CP 255
        JR Z,WOPENFAI
        LD (IX+110),1
        JP WSOURCE
WOPENFAI:
        CALL WERROR
        JP WSOURCE
WPROMPT:
        LD A,(IX+108)
        ADD A,'A'
        CALL CHAR
        LD A,(IX+109)
        LD HL,WPUSER
        LD (HL),A
        INC HL
        LD (HL),0
        INC HL
        LD (HL),0
        INC HL
        LD (HL),0
        LD HL,WPUSER
        CALL DECIMAL
        LD HL,(NUMPTR)
        CALL TEXT
        LD A,':'
        CALL CHAR
        PUSH IX
        POP HL
        INC HL
        LD B,8
WPNAME:
        LD A,(HL)
        CP ' '
        CALL NZ,CHAR
        INC HL
        DJNZ WPNAME
        LD A,(HL)
        CP ' '
        JR Z,WPTEXT
        LD A,'.'
        CALL CHAR
        LD B,3
WPEXT:
        LD A,(HL)
        CP ' '
        CALL NZ,CHAR
        INC HL
        DJNZ WPEXT
WPTEXT:
        LD HL,MSGPROMP
        CALL TEXT
WPKEY:
        LD C,1
        CALL BDOS
        CP 3
        JR Z,WPCANCEL
        CP '?'
        JR Z,WPHELP
        CP 13
        JR Z,WPYES
        AND 0DFH
        CP 'Y'
        JR Z,WPYES
        CP 'N'
        JR Z,WPANSWER
        CP 'A'
        JR NZ,WPKEY
        LD (ALLYES),A
WPYES:
        LD A,'Y'
WPANSWER:
        LD (WRESPONS),A
        JP NL
WPHELP:
        CALL NL
        LD HL,MSGPHELP
        CALL TEXT
        JP WPROMPT
WPCANCEL:
        LD A,1
        LD (CANCEL),A
        LD (INCOMPLE),A
        JP NL
; Find a fresh temporary/backup pair, preserving files from earlier sessions.
WUNIQUET:
        PUSH IX
        POP DE
        LD HL,36
        ADD HL,DE
        LD (WTPTR),HL
        LD BC,36
        CALL ZERO
        LD HL,(WTPTR)
        LD A,(IX+0)
        LD (HL),A
        INC HL
        LD DE,WTEMPLAT
        EX DE,HL
        LD BC,11
        LDIR
WTRYNAME:
        LD HL,(WTNUMBER)
        INC HL
        LD (WTNUMBER),HL
        LD A,H
        OR L
        SCF
        RET Z
        CALL WTRESET
        CALL NEWLINE
        LD HL,WTNUMBER
        LD B,2
        CALL HEXVALUE
        LD HL,LINE
        LD DE,(WTPTR)
        PUSH DE
        LD BC,5
        EX DE,HL
        ADD HL,BC
        EX DE,HL
        LD BC,4
        LDIR
        POP DE
        PUSH DE
        CALL WRESERVE
        POP DE
        JP Z,WTRYNAME
        LD C,15
        CALL BDOS
        CP 255
        JR NZ,WTRYEXIS
        ; Build and probe the recovery name as well.
        PUSH IX
        POP DE
        LD HL,72
        ADD HL,DE
        EX DE,HL
        LD HL,(WTPTR)
        LD BC,36
        LDIR
        LD (IX+81),'B'
        LD (IX+82),'A'
        LD (IX+83),'K'
        PUSH IX
        POP DE
        LD HL,72
        ADD HL,DE
        EX DE,HL
        PUSH DE
        CALL WRESERVE
        POP DE
        JP Z,WTRYNAME
        LD C,15
        CALL BDOS
        CP 255
        JR NZ,WTRYEXIS
        OR A
        RET
WTRYEXIS:
        LD C,16
        CALL BDOS
        JR WTRYNAME
; A transaction name must not equal either requested final destination, even
; when that final does not yet exist. DE is the candidate FCB in this DU.
WRESERVE:
        LD HL,1
        ADD HL,DE
        LD (WCNAME),HL
        PUSH IX
        POP DE
        INC DE
        CALL CMPNAME
        RET Z
        LD A,(LOCALSET)
        OR A
        JR Z,WRESMAST
        LD HL,(WCNAME)
        LD DE,LOCAL+1
        CALL CMPNAME
        RET Z
WRESMAST:
        LD A,(MASTSET)
        OR A
        JR Z,WRESNO
        LD A,(MASTER+36)
        CP (IX+108)
        JR NZ,WRESNO
        LD A,(MASTER+37)
        CP (IX+109)
        JR NZ,WRESNO
        LD HL,(WCNAME)
        LD DE,MASTER+1
        CALL CMPNAME
        RET Z
WRESNO:
        LD A,1
        OR A
        RET
WTRESET:
        LD HL,(WTPTR)
        LD BC,12
        ADD HL,BC
        LD BC,24
        JP ZERO
WSECTION:
        LD IX,WDMASTER
        CALL WSECTI01
        LD IX,WDLOCAL
        JP WSECTI01
WSECTI01:
        LD A,(IX+110)
        CP 1
        RET NZ
        CALL WSELECT
        LD A,(IX+112)
        OR A
        JR Z,WSECFIRST
        LD A,(LEGACY)
        OR A
        JR NZ,WSECTI03
        JR WSECTI02
WSECFIRST:
        LD A,(LEGACY)
        OR A
        JR Z,WSECTI03
WSECTI02:
        LD A,13
        CALL WPUT
        LD A,10
        CALL WPUT
WSECTI03:
        LD (IX+112),1
        JP WSOURCE
WLINE:
        LD IX,WDMASTER
        CALL WLINEONE
        LD IX,WDLOCAL
WLINEONE:
        LD A,(IX+110)
        CP 1
        RET NZ
        CALL WSELECT
        LD HL,LINE
WLCHAR:
        LD A,(HL)
        OR A
        JR Z,WLEND
        CALL WPUT
        INC HL
        JR WLCHAR
WLEND:
        LD A,13
        CALL WPUT
        LD A,10
        CALL WPUT
        JP WSOURCE
WPUT:
        PUSH HL
        PUSH DE
        PUSH BC
        LD B,A
        LD A,(IX+110)
        CP 1
        JR NZ,WPUTEND
        LD L,(IX+114)
        LD H,(IX+115)
        LD E,(IX+111)
        LD D,0
        ADD HL,DE
        LD (HL),B
        INC (IX+111)
        LD A,(IX+111)
        CP 128
        CALL Z,WFLUSH
WPUTEND:
        POP BC
        POP DE
        POP HL
        RET
WFLUSH:
        LD E,(IX+114)
        LD D,(IX+115)
        LD C,26
        CALL BDOS
        PUSH IX
        POP DE
        LD HL,36
        ADD HL,DE
        EX DE,HL
        LD C,21
        CALL BDOS
        OR A
        CALL NZ,WERROR
        LD (IX+111),0
        RET
WINVALID:
        LD IX,WDMASTER
        CALL WINVAL01
        LD IX,WDLOCAL
WINVAL01:
        LD A,(IX+110)
        CP 1
        RET NZ
        LD (IX+110),2
        LD HL,OUTERROR
        CALL INC32
        RET
WERROR:
        LD (IX+110),2
        LD HL,OUTERROR
        CALL INC32
        LD A,1
        LD (INCOMPLE),A
        LD HL,MSGOUTPU
        JP TEXT
WLOCALEN:
        LD IX,WDLOCAL
        JP WFINAL
WEND:
        CALL WLOCALEN
        LD IX,WDMASTER
WFINAL:
        CALL POLL
        LD A,(IX+110)
        OR A
        RET Z
        CALL WSELECT
        LD A,(CANCEL)
        OR A
        JR NZ,WDISCARD
        LD A,(IX+110)
        CP 1
        JR NZ,WDISCARD
        ; Ensure a text EOF even if the last CRLF ended at a record boundary.
WPAD:
        LD A,26
        CALL WPUT
        LD A,(IX+110)
        CP 1
        JR NZ,WDISCARD
        LD A,(IX+111)
        OR A
        JR NZ,WPAD
        CALL WCLOSETE
        CP 255
        JR Z,WDISCA01
        CALL WPROMOTE
        JR C,WDISCA01
        LD HL,OUTDONE
        CALL INC32
        LD (IX+110),0
        JP WSOURCE
WDISCA01:
        CALL WERROR
WDISCARD:
        CALL WCLOSETE
        PUSH IX
        POP DE
        LD HL,36
        ADD HL,DE
        EX DE,HL
        LD C,19
        CALL BDOS
        LD (IX+110),0
        JP WSOURCE
WCLOSETE:
        PUSH IX
        POP DE
        LD HL,36
        ADD HL,DE
        EX DE,HL
        LD C,16
        JP BDOS
; Rename old final to unused recovery name, then temp to final. If second
; rename fails restore old final; never erase the sole surviving old copy.
WPROMOTE:
        PUSH IX
        POP HL
        LD DE,WRENAME
        LD BC,12
        LDIR
        PUSH IX
        POP HL
        LD DE,72
        ADD HL,DE
        LD DE,WRENAME+16
        LD BC,12
        LDIR
        LD DE,WRENAME
        LD C,23
        CALL BDOS
        CP 255
        JR Z,WRENAMEN
        LD (IX+113),1
WRENAMEN:
        PUSH IX
        POP HL
        LD DE,36
        ADD HL,DE
        LD DE,WRENAME
        LD BC,12
        LDIR
        PUSH IX
        POP HL
        LD DE,WRENAME+16
        LD BC,12
        LDIR
        LD DE,WRENAME
        LD C,23
        CALL BDOS
        CP 255
        JR Z,WRECOVER
        LD A,(IX+113)
        OR A
        RET Z
        PUSH IX
        POP DE
        LD HL,72
        ADD HL,DE
        EX DE,HL
        LD C,19
        CALL BDOS
        CP 255
        JR Z,WRECOV01
        OR A
        RET
WRECOVER:
        LD A,(IX+113)
        OR A
        SCF
        RET Z
        PUSH IX
        POP HL
        LD DE,72
        ADD HL,DE
        LD DE,WRENAME
        LD BC,12
        LDIR
        PUSH IX
        POP HL
        LD DE,WRENAME+16
        LD BC,12
        LDIR
        LD DE,WRENAME
        LD C,23
        CALL BDOS
        CP 255
        JR Z,WRECOV01
        SCF
        RET
WRECOV01:
        LD HL,MSGRECOV
        CALL TEXT
        ; Print both surviving identities from the transaction descriptor.
        CALL WPROMPTN
        SCF
        RET
WPROMPTN:
        LD A,(IX+108)
        ADD A,'A'
        CALL CHAR
        LD A,(IX+109)
        LD (WPUSER),A
        LD HL,WPUSER
        CALL DECIMAL
        LD HL,(NUMPTR)
        CALL TEXT
        LD A,':'
        CALL CHAR
        PUSH IX
        POP HL
        LD DE,37
        ADD HL,DE
        CALL PRINTNAM
        LD A,' '
        CALL CHAR
        PUSH IX
        POP HL
        LD DE,73
        ADD HL,DE
        CALL PRINTNAM
        JP NL
; Z means include, NZ means an output/transaction or wildcard reference.
EXCLUDED:
        LD A,(MASTSET)
        OR A
        JR Z,EXLOCAL
        LD A,(MASTER+36)
        LD B,A
        LD A,(DRIVE)
        CP B
        JR NZ,EXLOCAL
        LD A,(MASTER+37)
        LD B,A
        LD A,(USER)
        CP B
        JR NZ,EXLOCAL
        LD HL,CANDNAME
        LD DE,MASTER+1
        CALL CMPNAME
        JR Z,EXYES
EXLOCAL:
        LD A,(LOCALSET)
        OR A
        JR Z,EXTRANSA
        LD HL,CANDNAME
        LD DE,LOCAL+1
        CALL CMPNAME
        JR Z,EXYES
EXTRANSA:
        LD IX,WDMASTER
        CALL EXTRAN01
        JR Z,EXYES
        LD IX,WDLOCAL
        CALL EXTRAN01
        JR Z,EXYES
        JP EXREFERE
EXTRAN01:
        LD A,(IX+110)
        OR A
        JR Z,EXNO
        LD A,(DRIVE)
        CP (IX+108)
        JR NZ,EXNO
        LD A,(USER)
        CP (IX+109)
        JR NZ,EXNO
        PUSH IX
        POP DE
        LD HL,37
        ADD HL,DE
        EX DE,HL
        LD HL,CANDNAME
        CALL CMPNAME
        RET Z
        PUSH IX
        POP DE
        LD HL,73
        ADD HL,DE
        EX DE,HL
        LD HL,CANDNAME
        CALL CMPNAME
        RET
EXNO:
        LD A,1
        OR A
        RET
EXYES:
        LD A,1
        OR A
        RET
WDMASTER: DS 116
WDLOCAL: DS 116
WMBUFFER: DS 128
WLBUFFER: DS 128
WRENAME: DS 36
WTPTR: DW 0
WCNAME: DW 0
WTNUMBER: DW 0
WPUSER: DS 4
WRESPONS: DB 0
WTEMPLAT: DB 'CRC00000$$$'
MSGPHELP: DB 'Y Yes, N No, A All, ? Help',13,10,0
MSGPROMP: DB ' exists.',13,10,'Overwrite? (Y/n/a/?) ',0
MSGOUTPU: DB 'CRCKSUM: output transaction failed',13,10,0
MSGRECOV: DB 'CRCKSUM: recovery incomplete; retain CRC*.BAK',13,10,0
