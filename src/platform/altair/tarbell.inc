; Physical sector API: A=drive 0..3, D=track 0..76, E=sector 1..26,
; HL=128-byte buffer. Returns A=0/Z success, A=1/NZ failure.
; BC and HL are clobbered; DE is preserved. No cpmsim DMA ports are used.
; Restore then seek on every request until per-drive head tracking is added.
AL_READ:
        LD C,080H
        JR AL_TRANSFER
AL_WRITE:
        LD C,0A0H
AL_TRANSFER:
        CP 4
        JP NC,AL_IOBAD
        LD (AL_COMMAND),A
        LD A,D
        CP 77
        JP NC,AL_IOBAD
        LD A,E
        DEC A
        CP 26
        JP NC,AL_IOBAD
        LD A,(AL_COMMAND)
        CPL
        RRCA
        RRCA
        RRCA
        RRCA
        AND 030H
        OR 0C2H
        OUT (AL_FSEL),A
        LD A,C
        LD (AL_COMMAND),A
        LD A,0D0H
        OUT (AL_FCMD),A
        XOR A
        OUT (AL_FCMD),A
        CALL AL_IDLE
        JP NZ,AL_IOBAD
        IN A,(AL_FCMD)
        AND 004H
        JP Z,AL_IOBAD
        LD A,D
        OUT (AL_FDATA),A
        LD A,01CH
        OUT (AL_FCMD),A
        CALL AL_IDLE
        JP NZ,AL_IOBAD
        IN A,(AL_FCMD)
        AND 090H
        JP NZ,AL_IOBAD
        LD A,E
        OUT (AL_FSEC),A
        LD A,(AL_COMMAND)
        OUT (AL_FCMD),A
        LD B,128
AL_BYTE:
        IN A,(AL_FWAIT)
        OR A
        JP P,AL_IOBAD                  ; premature completion
        LD A,(AL_COMMAND)
        CP 080H
        JR NZ,AL_PUT
        IN A,(AL_FDATA)
        LD (HL),A
        JR AL_NEXT
AL_PUT:
        LD A,(HL)
        OUT (AL_FDATA),A
AL_NEXT:
        INC HL
        DJNZ AL_BYTE
        CALL AL_IDLE
        JP NZ,AL_IOBAD
        IN A,(AL_FCMD)
        AND 0FCH
        RET Z
AL_IOBAD:
        LD A,0D0H
        OUT (AL_FCMD),A
        LD A,1
        OR A
        RET
AL_IDLE:
        PUSH BC
        LD BC,0
AL_WAIT:
        IN A,(AL_FWAIT)
        OR A
        JP P,AL_FINISHED
        DEC BC
        LD A,B
        OR C
        JR NZ,AL_WAIT
        LD A,1
        OR A
AL_FINISHED:
        POP BC
        RET
AL_COMMAND: DB 0

