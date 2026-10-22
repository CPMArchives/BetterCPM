; Choice-error layout: complete question/choices/default, then bounded message.
; UE_ERROR: HL=NUL printable ASCII diagnostic. Calls UF_PICK; UC config must
; already be validated. UF_WIDTH is available cells, UF_BUF has 256 bytes.
; Success A=0/carry clear, HL=buffer B=length. Truncation is marked by '~'.
; Needs two spare cells beyond question for a space and diagnostic character.
; Failure A=7/carry set: caller must use another layout, not draw stale text.
; Buffer may contain the plain question on failure; no terminal output occurs.
; Editor/choice state and configuration remain unchanged. Clobbers registers.
UE_ERROR:
        PUSH HL
        CALL UF_PICK
        POP DE
        RET C
        LD A,(UF_WIDTH)
        SUB B
        CP 2
        JP C,UF_BAD
        LD C,A
        LD A,B
        PUSH BC
        LD B,0
        LD C,A
        ADD HL,BC
        POP BC
        LD A,' '
        LD (HL),A
        INC HL
        INC B
        DEC C
UE_ECHAR:
        LD A,(DE)
        OR A
        JR Z,UE_EDONE
        CP 32
        JP C,UF_BAD
        CP 127
        JP NC,UF_BAD
        LD (HL),A
        INC HL
        INC DE
        INC B
        DEC C
        JR NZ,UE_ECHAR
        LD A,(DE)
        OR A
        JR Z,UE_EDONE
        DEC HL
        LD (HL),'~'
        INC HL
UE_EDONE:
        XOR A
        LD (HL),A
        LD HL,UF_BUF
        RET
