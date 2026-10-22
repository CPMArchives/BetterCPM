; Bounded choice prompt formatter, separate from terminal transport.
; Call after UC_RUN's configuration validation (e.g. from UC_PAINT).
; UF_LABEL: NUL printable ASCII label, including desired trailing spacing.
; UF_WIDTH: available columns (1..255); reserve the terminal's wrap column.
; UF_BUF: caller-owned 256 bytes. UC_LIST/UC_COUNT/UC_DEF as in choice.inc.
; UF_PICK returns carry clear, HL=UF_BUF, B=length, A=UI_MORE; NUL appended.
; On invalid label or insufficient width: carry set, A=UI_BAD, buffer untouched.
; Does not emit output, truncate, change choice/editor state, or allocate state.
; Clobbers AF/BC/DE/HL. Caller positions/clears row and writes returned B bytes
; with direct output; this is formatting, not a screen backend or error renderer.
UF_PICK:
        LD HL,(UF_LABEL)
        LD B,0
UF_SCAN:
        LD A,(HL)
        OR A
        JR Z,UF_SIZE
        CP 32
        JP C,UF_BAD
        CP 127
        JP NC,UF_BAD
        INC B
        JP Z,UF_BAD
        INC HL
        JR UF_SCAN
UF_SIZE:
        LD A,(UC_COUNT)
        OR A
        JP Z,UF_BAD
        ADD A,A
        JP C,UF_BAD
        ADD A,B
        JP C,UF_BAD
        INC A
        JP Z,UF_BAD
        LD B,A
        LD A,(UC_DEF)
        OR A
        LD A,B
        JR Z,UF_FITS
        ADD A,4
        JP C,UF_BAD
UF_FITS:
        LD B,A
        LD A,(UF_WIDTH)
        CP B
        JP C,UF_BAD
        PUSH BC
        LD DE,UF_BUF
        LD HL,(UF_LABEL)
UF_COPY:
        LD A,(HL)
        OR A
        JR Z,UF_OPEN
        LD (DE),A
        INC DE
        INC HL
        JR UF_COPY
UF_OPEN:
        LD A,'('
        LD (DE),A
        INC DE
        LD HL,(UC_LIST)
        LD A,(UC_COUNT)
        LD B,A
UF_ITEM:
        LD A,(HL)
        CALL UC_UPPER
        LD (DE),A
        INC DE
        INC HL
        DJNZ UF_SLASH
        LD A,')'
        LD (DE),A
        INC DE
        LD A,(UC_DEF)
        OR A
        JR Z,UF_DONE
        PUSH AF
        LD A,' '
        LD (DE),A
        INC DE
        LD A,'['
        LD (DE),A
        INC DE
        POP AF
        CALL UC_UPPER
        LD (DE),A
        INC DE
        LD A,']'
        LD (DE),A
        INC DE
UF_DONE:
        XOR A
        LD (DE),A
        POP BC
        LD HL,UF_BUF
        RET
UF_SLASH:
        LD A,'/'
        LD (DE),A
        INC DE
        JR UF_ITEM
UF_BAD:
        LD A,UI_BAD
        SCF
        RET
