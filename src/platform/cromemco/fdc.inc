; A=drive 0..3, D=track 0..76, E=sector 1..26, HL=128-byte buffer.
; Returns A=0/Z success, A=1/NZ failure. Preserves DE, clobbers BC/HL.
; Fixed 8-inch SSSD, side zero. Restore and seek each request.
CM_READ:
        LD C,080H
        JR CM_TRANSFER
CM_WRITE:
        LD C,0A0H
CM_TRANSFER:
        CP 4
        JP NC,CM_IOBAD
        LD (CM_UNIT),A
        LD A,D
        CP 77
        JP NC,CM_IOBAD
        LD A,E
        DEC A
        CP 26
        JP NC,CM_IOBAD
        LD A,C
        LD (CM_COMMAND),A
        LD A,(CM_UNIT)
        LD B,A
        LD A,1
        INC B
CM_SELECT:
        DEC B
        JR Z,CM_SELON
        ADD A,A
        JR CM_SELECT
CM_SELON:
        OR 030H
        OUT (CM_FSEL),A
        LD A,0FFH
        OUT (004H),A
        LD A,0D0H
        OUT (CM_FCMD),A
        XOR A
        OUT (CM_FCMD),A
        CALL CM_IDLE
        JP NZ,CM_IOBAD
        IN A,(CM_FCMD)
        AND 004H
        JP Z,CM_IOBAD
        LD A,D
        OUT (CM_FDATA),A
        LD A,01CH
        OUT (CM_FCMD),A
        CALL CM_IDLE
        JP NZ,CM_IOBAD
        IN A,(CM_FCMD)
        AND 090H
        JP NZ,CM_IOBAD
        LD A,E
        OUT (CM_FSEC),A
        LD A,(CM_COMMAND)
        OUT (CM_FCMD),A
        LD B,128
CM_BYTE:
        LD C,0
CM_DRQ:
        IN A,(CM_FCMD)
        BIT 0,A
        JP Z,CM_IOBAD
        BIT 1,A
        JR NZ,CM_DATA
        DEC C
        JR NZ,CM_DRQ
        JP CM_IOBAD
CM_DATA:
        LD A,(CM_COMMAND)
        CP 080H
        JR NZ,CM_PUT
        IN A,(CM_FDATA)
        LD (HL),A
        JR CM_NEXT
CM_PUT:
        LD A,(HL)
        OUT (CM_FDATA),A
CM_NEXT:
        INC HL
        DJNZ CM_BYTE
        CALL CM_IDLE
        JP NZ,CM_IOBAD
        IN A,(CM_FCMD)
        AND 0FCH
        RET Z
CM_IOBAD:
        LD A,0D0H
        OUT (CM_FCMD),A
        LD A,1
        OR A
        RET
CM_IDLE:
        PUSH BC
        LD BC,0
CM_WAIT:
        IN A,(CM_FCMD)
        AND 1
        JR Z,CM_FINISHED
        DEC BC
        LD A,B
        OR C
        JR NZ,CM_WAIT
        INC A
CM_FINISHED:
        POP BC
        RET
CM_COMMAND: DB 0
CM_UNIT: DB 0
