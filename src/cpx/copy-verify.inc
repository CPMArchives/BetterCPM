; Transient /V verification core. Preserve transfer FCBs
; and their attributes. CF clear means identical records and simultaneous EOF;
; CF set means open/read failure, unequal length or unequal record contents.
CTVERIFY:
        XOR A
        LD (CT_CANCEL),A
        LD HL,BC_FCB
        LD DE,CTV_SRC
        CALL CTVFCB
        LD HL,BC_NEWFCB
        LD DE,CTV_DST
        CALL CTVFCB
        CALL BC_CSELS
        LD DE,CTV_SRC
        LD C,15
        CALL BDOS
        CP 0FFH
        JP Z,CTVFAIL
        CALL BC_CSELD
        LD DE,CTV_DST
        LD C,15
        CALL BDOS
        CP 0FFH
        JP Z,CTVFAIL
CTVLOOP:
        CALL CTCHECK
        JR C,CTVABORT
        CALL BC_CSELS
        LD DE,BC_DMA
        LD C,26
        CALL BDOS
        LD DE,CTV_SRC
        LD C,20
        CALL BDOS
        LD (CTVSTAT),A
        CP 2
        JP NC,CTVFAIL
        CALL BC_CSELD
        LD DE,CTV_BUF
        LD C,26
        CALL BDOS
        LD DE,CTV_DST
        LD C,20
        CALL BDOS
        LD B,A
        LD A,(CTVSTAT)
        CP B
        JP NZ,CTVFAIL
        CP 1
        JR Z,CTVGOOD
        LD HL,BC_DMA
        LD DE,CTV_BUF
        LD B,128
CVVBYTE:
        LD A,(DE)
        CP (HL)
        JP NZ,CTVFAIL
        INC DE
        INC HL
        DJNZ CVVBYTE
        JR CTVLOOP
CTVABORT:
        LD A,1
        LD (CT_CANCEL),A
        JR CTVFAIL
CTVGOOD:
        LD A,0
        JR CTVEXIT
CTVFAIL:
        LD A,1
CTVEXIT:
        PUSH AF
        LD DE,BC_DMA
        LD C,26
        CALL BDOS
        POP AF
        OR A
        RET Z
        SCF
        RET
; Fresh FCBs keep names only, discarding old extent/maps/cursors.
CTVFCB:
        LD BC,12
        LDIR
        LD B,24
        XOR A
CTVZERO:
        LD (DE),A
        INC DE
        DJNZ CTVZERO
        RET
CTVSTAT: DB 0
CTV_SRC: DS 36
CTV_DST: DS 36
CTV_BUF: DS 128

; Only a closed destination can be verified; attributes follow success.
CTVPOST:
        LD A,(CTV_ON)
        OR A
        JP Z,CTVATTR
        CALL CTVERIFY
        PUSH AF
        LD A,(CT_CANCEL)
        OR A
        JR Z,CTVRESULT
        POP AF
        JP CTCANCEL
CTVRESULT:
        POP AF
        JP NC,CTVATTR
        CALL CTPAIR
        LD A,(CT_BATCH)
        OR A
        JR Z,CVVASK
        LD DE,CVVERROR
        CALL BC_PRINT
        CALL CVVDEL
        RET C
        LD HL,CT_FAILS
        INC (HL)
        RET
CVVASK:
        LD DE,CVVASKM
        CALL BC_PRINT
CVVREAD:
        LD E,0FFH
        LD C,6
        CALL BDOS
        OR A
        JR Z,CVVREAD
        CP 3
        JR Z,CVVABORT
        CP 13
        JR Z,CVVREAD
        CP 10
        JR Z,CVVREAD
        CP 'a'
        JR C,CVVANS
        CP 'z'+1
        JR NC,CVVANS
        SUB 32
CVVANS:
        LD (CT_CHOICE),A
        CALL BC_PCHAR
        LD DE,BC_NL
        CALL BC_PRINT
        LD A,(CT_CHOICE)
        CP 'R'
        JR Z,CVVRETRY
        CP 'S'
        JR Z,CVVSKIP
        LD DE,CVVHELP
        CALL BC_PRINT
        CALL CTPAIR                    ; retain item context when repeating the prompt
        JR CVVASK
CVVABORT:
        CALL CVVDEL
        RET C
        JP CTABORT
CVVSKIP:
        CALL CVVDEL
        RET C
        JP CTSKIP
CVVRETRY:
        CALL CVVDEL
        RET C
        LD HL,BC_FCB
        LD DE,CTV_SRC
        CALL CTVFCB
        LD HL,CTV_SRC
        LD DE,BC_FCB
        LD BC,36
        LDIR
        LD HL,BC_NEWFCB
        LD DE,CTV_DST
        CALL CTVFCB
        LD HL,CTV_DST
        LD DE,BC_NEWFCB
        LD BC,36
        LDIR
        JP BC_COPEN
; A cleanup failure stops the batch rather than claiming removal succeeded.
CVVDEL:
        CALL BC_CSELD
        LD DE,BC_NEWFCB
        LD C,19
        CALL BDOS
        CP 0FFH
        JR Z,CVVDELNO
        XOR A
        LD (BC_CMADE),A
        RET
CVVDELNO:
        LD A,1
        LD (BC_WERROR),A
        LD DE,CTE_CLEAN
        CALL BC_PRINT
        SCF
        RET
CTV_ON: DB 0
CVVERROR: DB ' [VERIFY ERROR]',13,10,'$'
CVVASKM: DB ' [VERIFY ERROR] R/S/? $'
CVVHELP: DB 'R - Retry  S - Skip',13,10,'$'

; Poll only at record boundaries. No input waits; ordinary keys are ignored.
CTCHECK:
        LD E,0FFH
        LD C,6
        CALL BDOS
        CP 3
        JR Z,CTKEYC
        OR A
        RET
CTKEYC:
        SCF
        RET
; Enter by JP with only the copy driver's return address on the stack.
CTCANCEL:
        LD A,(BC_CMADE)
        OR A
        JR Z,CTCSTOP
        CALL BC_CSELD
        LD DE,BC_NEWFCB
        LD C,16
        CALL BDOS
        CALL CVVDEL
        RET C
CTCSTOP:
        JP CTABORT
CT_CANCEL: DB 0
