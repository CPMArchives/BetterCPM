; Command environment is a pending cold-boot domain of the existing BCST save.
PD_MENU:
        LD A,(STSTATE)
        OR A
        CALL Z,STFETCH
        LD A,(STSTATE)
        CP 2
        JP Z,STSAVEINVALID
        LD HL,PD_TITLE
        CALL HEADER
        CALL PH_VALIDATE
        JP NZ,STSAVEINVALID
        LD HL,PD_ACTIVE
        CALL PUTS
        LD IX,LY_PD2+4
        CALL PD_WORDS
        LD HL,PD_SAVED
        CALL PUTS
        LD IX,PD_SAVE
        CALL PD_CODES
        LD HL,PD_PENDING
        CALL PUTS
        LD IX,STPEND+145
        CALL PD_CODES
        LD A,(STPEND+145)
        LD HL,PD_HSIZE
        CALL PD_SIZE
        LD (PD_TOTAL),HL
        LD A,(STPEND+146)
        LD HL,PD_MSIZE
        CALL PD_SIZE
        LD DE,(PD_TOTAL)
        ADD HL,DE
        LD (PD_TOTAL),HL
        LD A,(STPEND+147)
        LD HL,PD_VSIZE
        CALL PD_SIZE
        LD DE,(PD_TOTAL)
        ADD HL,DE
        LD DE,12
        ADD HL,DE
        LD (PD_TOTAL),HL
        LD HL,PD_BYTES
        CALL PUTS
        LD HL,(PD_TOTAL)
        CALL PD_NUMBER
        LD HL,PD_MAX
        CALL PUTS
        LD HL,LY_SYS-259
        LD DE,(PD_TOTAL)
        OR A
        SBC HL,DE
        LD A,L
        AND 128
        LD L,A
        CALL PD_NUMBER
        LD HL,PD_HELP
        CALL PUTS
        CALL CHOICE
        CP 3
        JP Z,MAIN
        LD HL,STPEND+145
        LD B,3
        CP 'A'
        JR Z,PD_CYCLE
        INC HL
        LD B,1
        CP 'B'
        JR Z,PD_CYCLE
        INC HL
        LD B,3
        CP 'C'
        JP NZ,PD_MENU
PD_CYCLE:
        INC (HL)
        LD A,(HL)
        AND B
        LD (HL),A
        CALL STCHECKSUM
        LD A,1
        LD (STDIRTY),A
        JP PD_MENU
PD_WORDS:
        LD B,3
PD_WLOOP:
        LD L,(IX+0)
        LD H,(IX+1)
        PUSH BC
        CALL PD_DEC
        POP BC
        LD A,' '
        CALL PUTC
        INC IX
        INC IX
        DJNZ PD_WLOOP
        JP CRLF
PD_CODES:
        LD B,3
PD_CLOOP:
        LD L,(IX+0)
        LD H,0
        PUSH BC
        CALL PD_DEC
        POP BC
        LD A,' '
        CALL PUTC
        INC IX
        DJNZ PD_CLOOP
        JP CRLF
PD_NUMBER:
        CALL PD_DEC
        JP CRLF
PD_SIZE:
        ADD A,A
        LD E,A
        LD D,0
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        RET
PD_UPGRADE:
        LD A,(STPEND+4)
        CP 2
        RET Z
        LD HL,PD_DEF
        LD DE,STPEND+145
        LD BC,3
        LDIR
        LD A,2
        LD (STPEND+4),A
        LD HL,PD_DEF
        LD DE,PD_HOLD
        LD BC,3
        LDIR
        CALL PD_RESTORE
        JP STCHECKSUM
PD_KEEP:
        LD HL,PD_DEF
        LD A,(STSTATE)
        CP 1
        JR NZ,PD_KCOPY
        LD HL,STPEND+145
PD_KCOPY:
        LD DE,PD_HOLD
        LD BC,3
        LDIR
        RET
PD_RESTORE:
        LD HL,PD_CE
        LD DE,STPEND+142
        LD BC,3
        LDIR
        LD HL,PD_HOLD
        LD BC,3
        LDIR
        RET
PD_SNAPSHOT:
        LD HL,STPEND+145
        LD DE,PD_SAVE
        LD BC,3
        LDIR
        RET
PD_DEF: DB 2,0,0
PD_CE: DB 'CE',1
PD_HSIZE: DW 0,128,192,384
PD_MSIZE: DW 0,128
PD_VSIZE: DW 0,128,256,512
PD_TITLE: DB 'Command Environment / PDS',0
PD_ACTIVE: DB 'Active H/M/V bytes: ',0
PD_SAVED: DB 'Saved choices H/M/V: ',0
PD_PENDING: DB 'Pending choices H/M/V: ',0
PD_BYTES: DB 'Pending PDS bytes (includes 12 metadata): ',0
PD_MAX: DB 'Next cold boot maximum COM (no RSXs): ',0
PD_HELP: DB 13,10,'Changes apply next cold boot. Save from main menu.',13,10
        DB 'A History: 0 Off, 1 128, 2 192, 3 384 bytes',13,10
        DB 'B MCL storage: 0 Off, 1 128 bytes',13,10
        DB 'C VAR storage: 0 Off, 1 128, 2 256, 3 512 bytes',13,10
        DB 'MCL/VAR command support follows in later 1.3 stages.',13,10
        DB '^C Return',13,10,0

STDEFAULT:                             ; reset startup while preserving PDS choices
        CALL PD_KEEP
        LD HL,STPEND
        LD DE,STPEND+1
        LD BC,255
        LD (HL),0
        LDIR
        LD HL,STHEADER
        LD DE,STPEND
        LD BC,16
        LDIR
        CALL PD_RESTORE
STCHECKSUM:
        LD HL,0                        ; set negative 16-bit word sum
        LD (STPEND+12),HL
        LD IX,STPEND
        LD B,128
STCKLOOP:LD E,(IX+0)
        LD D,(IX+1)
        ADD HL,DE
        INC IX
        INC IX
        DJNZ STCKLOOP
        EX DE,HL
        LD HL,0
        OR A
        SBC HL,DE
        LD (STPEND+12),HL
        RET


STHEADER:DB 'BCST',2,0,16,0,0,126,0,1,0,0
         DW LY_SYS
STFCBRESET:                            ; restore reusable A0:$$$.SUB FCB
        LD HL,STSUBFCB+12
        LD DE,STSUBFCB+13
        LD BC,23
        LD (HL),0
        LDIR
        RET

; Unsigned HL decimal, suppress leading zeros; output callbacks preserve HL.
PD_DEC:
        LD C,0
        LD DE,10000
        CALL PD_DIGIT
        LD DE,1000
        CALL PD_DIGIT
        LD DE,100
        CALL PD_DIGIT
        LD DE,10
        CALL PD_DIGIT
        LD A,L
        ADD A,'0'
        JP PUTC
PD_DIGIT:
        LD A,'0'-1
PD_SUB:
        INC A
        OR A
        SBC HL,DE
        JR NC,PD_SUB
        ADD HL,DE
        CP '0'
        JR NZ,PD_PRINT
        BIT 0,C
        RET Z
PD_PRINT:
        LD C,1
        JP PUTC
; Mutable overlay session fields are outside the immutable CRC range.
        DS 09700H-$
PD_HOLD: DB 2,0,0
PD_SAVE: DB 2,0,0
PD_TOTAL: DW 0
