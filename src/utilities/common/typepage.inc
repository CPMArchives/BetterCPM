; Transient TYPE page replay. 32-bit logical page indices, no bounded history.
; Current platforms expose an 80-column, 24-row console; one row is for MORE.
TP_INIT:
        XOR A
        LD HL,TP_TARG
        LD B,4
TP_IZERO:
        LD (HL),A
        INC HL
        DJNZ TP_IZERO
        JP TP_RESET
TP_RESET:
        XOR A
        LD (TP_ACT),A
        LD (TP_ROWS),A
        LD (TP_COL),A
        LD (TP_FULL),A
        LD (TP_EOF),A
        LD (TP_ANY),A
        INC A
        LD (TP_NEW),A
        XOR A
        LD HL,TP_CUR
        LD B,4
TP_ZERO:
        LD (HL),A
        INC HL
        DJNZ TP_ZERO
        JP TP_EQUAL
TP_EQUAL:
        LD HL,TP_CUR
        LD DE,TP_TARG
        LD B,4
TP_EQLOOP:
        LD A,(DE)
        CP (HL)
        JR NZ,TP_HIDDEN
        INC HL
        INC DE
        DJNZ TP_EQLOOP
        LD A,1
        LD (TP_SHOW),A
        RET
TP_HIDDEN:
        XOR A
        LD (TP_SHOW),A
        RET
TP_ADV:
        LD HL,TP_CUR
        LD B,4
TP_INC:
        INC (HL)
        JR NZ,TP_INCDONE
        INC HL
        DJNZ TP_INC
TP_INCDONE:
        XOR A
        LD (TP_ROWS),A
        LD (TP_FULL),A
        INC A
        LD (TP_NEW),A
        JP TP_EQUAL
; A=one rendered byte. Caller preserves all registers.
TP_PUT:
        LD (TP_BYTE),A
        LD A,(TP_ACT)
        OR A
        RET NZ
        LD A,(TP_FULL)
        OR A
        JR Z,TP_OUTPUT
        LD A,(TP_SHOW)
        OR A
        CALL NZ,TP_WAIT
        LD A,(TP_ACT)
        OR A
        RET NZ
        CALL TP_ADV
TP_OUTPUT:
        LD A,1
        LD (TP_ANY),A
        LD A,(TP_SHOW)
        OR A
        JR Z,TP_COUNT
        LD A,(TP_NEW)
        OR A
        CALL NZ,TP_INDENT
        LD A,(TP_BYTE)
        LD E,A
        LD C,2
        CALL BDOS
TP_COUNT:
        XOR A
        LD (T_FFIRST),A
        LD A,(TP_BYTE)
        CP 13
        JR Z,TP_CZERO
        CP 10
        JR Z,TP_ROW
        CP 9
        JR Z,TP_TAB
        CP 8
        JR Z,TP_BACK
        CP 32
        RET C
        LD HL,TP_COL
        INC (HL)
        LD A,(HL)
        CP 80
        RET C
        XOR A
        LD (HL),A
        JR TP_ROW
TP_CZERO:
        XOR A
        LD (TP_COL),A
        RET
TP_TAB:
        LD A,(TP_COL)
        OR 7
        INC A
        CP 80
        JR NC,TP_WRAP
        LD (TP_COL),A
        RET
TP_WRAP:
        XOR A
        LD (TP_COL),A
        JR TP_ROW
TP_BACK:
        LD A,(TP_COL)
        OR A
        RET Z
        DEC A
        LD (TP_COL),A
        RET
TP_ROW:
        LD HL,TP_ROWS
        INC (HL)
        LD A,(HL)
        CP 23
        RET C
        LD A,1
        LD (TP_FULL),A
        RET
; Poll with Function 6: Ctrl-C belongs to TYPE while reading page commands.
TP_WAIT:
        LD A,(TP_FULL)
        OR A
        JR NZ,TP_PROMPT
        LD A,(TP_COL)
        OR A
        JR Z,TP_PROMPT
        LD E,13
        LD C,2
        CALL BDOS
        LD E,10
        LD C,2
        CALL BDOS
TP_PROMPT:
        LD E,13
        LD C,2
        CALL BDOS
        LD DE,TP_MORE
        LD C,9
        CALL BDOS
TP_KEYS:
        LD E,0FFH
        LD C,6
        CALL BDOS
        CP 17
        JR Z,TP_QUIT
        CP 18
        JR Z,TP_PREV
        CP ','
        JR Z,TP_PREV
        CP 3
        JR Z,TP_NEXT
        CP '.'
        JR Z,TP_NEXT
        CP ' '
        JR NZ,TP_KEYS
TP_NEXT:
        LD A,(TP_EOF)
        OR A
        JR NZ,TP_BELL
        CALL TP_ERASE
        ; Target advances with current page so forward paging stays visible.
        LD HL,TP_TARG
        LD B,4
TP_TINC:
        INC (HL)
        JR NZ,TP_READY
        INC HL
        DJNZ TP_TINC
TP_READY:
        RET
TP_PREV:
        LD HL,TP_TARG
        LD B,4
        XOR A
TP_NONZERO:
        OR (HL)
        INC HL
        DJNZ TP_NONZERO
        JR Z,TP_BELL
        CALL TP_ERASE
        LD HL,TP_TARG
        LD B,4
TP_DEC:
        LD A,(HL)
        DEC (HL)
        OR A
        JR NZ,TP_REDO
        INC HL
        DJNZ TP_DEC
TP_REDO:
        LD A,1
        LD (TP_ACT),A
        RET
TP_QUIT:
        CALL TP_ERASE
        LD A,2
        LD (TP_ACT),A
        RET
TP_BELL:
        LD E,7
        LD C,2
        CALL BDOS
        JR TP_KEYS
TP_ERASE:
        ; Erase the prompt with CR/spaces/CR, outside page accounting.
        LD E,13
        LD C,2
        CALL BDOS
        LD B,61
TP_SPACE:
        PUSH BC
        LD E,' '
        LD C,2
        CALL BDOS
        POP BC
        DJNZ TP_SPACE
        LD E,13
        LD C,2
        JP BDOS
TP_INDENT:
        XOR A
        LD (TP_NEW),A
        LD A,(T_FFIRST)
        LD (TP_BEGIN),A
        LD A,(RF_DRIVE)
        LD (TP_ANCH),A
        LD A,(RF_USER)
        LD (TP_ANCH+1),A
        LD HL,RF_LAST
        LD DE,TP_ANCH+2
        LD BC,11
        LDIR
        LD A,(TP_COL)
        OR A
        RET Z
        LD B,A
TP_PAD:
        PUSH BC
        LD E,' '
        LD C,2
        CALL BDOS
        POP BC
        DJNZ TP_PAD
        RET
TP_FINAL:
        LD A,(TP_ANY)
        OR A
        RET Z
        LD A,(TP_SHOW)
        OR A
        JR NZ,TP_LAST
        ; The files changed and now end before the requested page: clamp/replay.
        LD HL,TP_CUR
        LD DE,TP_TARG
        LD BC,4
        LDIR
        LD A,1
        LD (TP_ACT),A
        RET
TP_LAST:
        LD A,1
        LD (TP_EOF),A
        JP TP_WAIT
TP_MORE: DB 'MORE -- ,/^R back; ./Space/^C next; ^Q quit.$'
TP_TARG: DS 4
TP_CUR: DS 4
TP_ROWS: DB 0
TP_COL: DB 0
TP_FULL: DB 0
TP_SHOW: DB 0
TP_ACT: DB 0
TP_EOF: DB 0
TP_ANY: DB 0
TP_BYTE: DB 0
TP_NEW: DB 0
TP_ANCH: DS 13
TP_BEGIN: DB 0
