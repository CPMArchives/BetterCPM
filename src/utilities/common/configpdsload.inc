; One concrete utility overlay; existing CONFIG code/stack/buffer limits stay put.
PD_MENU: LD HL,0900FH
        JR PD_CALL
PD_UPGRADE: LD HL,09003H
        JR PD_CALL
PD_KEEP: LD HL,09006H
        JR PD_CALL
PD_RESTORE: LD HL,09009H
        JR PD_CALL
PD_SNAPSHOT: LD HL,0900CH
PD_CALL:
        PUSH HL
        PUSH BC
        PUSH DE
        PUSH IX
        CALL PD_LOAD
        POP IX
        POP DE
        POP BC
        POP HL
        JP (HL)
PD_CHECK:
        LD HL,09000H
        LD BC,1792
        CALL SGCRC32
        LD HL,SGCRC
        LD DE,PD_EXPECT
        LD BC,4
        JP SGCMP
PD_LOAD:
        CALL PD_CHECK
        RET Z
        LD HL,PD_FCB+12
        LD B,24
        XOR A
PD_ZERO: LD (HL),A
        INC HL
        DJNZ PD_ZERO
        LD DE,PD_FCB
        LD C,15
        CALL STA0CALL
        INC A
        JR Z,PD_MISSING
        LD HL,09000H
PD_READ:
        PUSH HL
        EX DE,HL
        LD C,26
        CALL BDOS
        LD DE,PD_FCB
        LD C,20
        CALL STA0CALL
        POP HL
        OR A
        JR NZ,PD_MISSING
        LD DE,128
        ADD HL,DE
        LD A,H
        CP 098H
        JR NZ,PD_READ
        LD DE,PD_FCB
        LD C,16
        CALL STA0CALL
        LD DE,0080H
        LD C,26
        CALL BDOS
        CALL PD_CHECK
        RET Z
PD_MISSING:
        LD DE,0080H
        LD C,26
        CALL BDOS
        LD HL,PD_BAD
        CALL PUTS
        JP DONE
PD_BAD: DB 'Restore PDSCONF.OVL',13,10,0
PD_EXPECT:
; @pds-overlay-crc@
PD_FCB: DB 1,'PDSCONF OVL'
        DS 24
