; Standard text prompt prefix. Bind UF_LABEL, UF_WIDTH, UF_BUF (256 bytes).
; Call after UP_RUN validates configuration; label is NUL printable ASCII.
; UT_TEXT returns HL=UF_BUF, B=prefix length, A=0/carry clear, NUL appended.
; Empty UP_DEF fields show "label[DEFAULT] "; default is never edit-buffer data.
; Nonempty/non-default fields show label only. Always reserves one caret cell.
; Failure A=7/carry set leaves buffer untouched. Clobbers AF/BC/DE/HL.
UT_TEXT:
        LD HL,(UF_LABEL)
        LD B,0
UT_SCAN:
        LD A,(HL)
        OR A
        JR Z,UT_SIZE
        CP 32
        JP C,UT_BAD
        CP 127
        JP NC,UT_BAD
        INC B
        JP Z,UT_BAD
        INC HL
        JR UT_SCAN
UT_SIZE:
        LD D,0
        LD A,(EDITLEN)
        OR A
        JR NZ,UT_FITS
        LD A,(UP_MODE)
        CP UP_DEF
        JR NZ,UT_FITS
        LD A,(UP_DLEN)
        OR A
        JP Z,UT_BAD
        ADD A,3
        JP C,UT_BAD
        LD D,A
UT_FITS:
        LD A,B
        ADD A,D
        JP C,UT_BAD
        LD B,A
        LD A,(UF_WIDTH)
        CP B
        JP C,UT_BAD
        JP Z,UT_BAD
        PUSH BC
        PUSH DE
        LD HL,(UF_LABEL)
        LD DE,UF_BUF
UT_COPY:
        LD A,(HL)
        OR A
        JR Z,UT_DFLT
        LD (DE),A
        INC DE
        INC HL
        JR UT_COPY
UT_DFLT:
        POP BC
        LD A,B
        OR A
        JR Z,UT_DONE
        LD A,'['
        LD (DE),A
        INC DE
        LD HL,(UP_DPTR)
        LD A,(UP_DLEN)
        LD B,A
UT_VALUE:
        LD A,(HL)
        LD (DE),A
        INC HL
        INC DE
        DJNZ UT_VALUE
        LD A,']'
        LD (DE),A
        INC DE
        LD A,' '
        LD (DE),A
        INC DE
UT_DONE:
        XOR A
        LD (DE),A
        POP BC
        LD HL,UF_BUF
        RET
UT_BAD:
        LD A,7
        SCF
        RET
