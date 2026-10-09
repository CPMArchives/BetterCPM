; Internal verification core, not yet exposed as /V. Preserve transfer FCBs
; and their attributes. CF clear means identical records and simultaneous EOF;
; CF set means open/read failure, unequal length or unequal record contents.
CTVERIFY:
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
