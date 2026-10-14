; Transient TYPE page replay. 32-bit display-row anchors, no bounded history.
; Current platforms expose an 80-column, 24-row console; one row is for MORE.
TP_INIT:
        XOR A
        LD (TP_MODE),A
        LD (TP_NOSEP),A
        INC A
        LD (TP_CLEAR),A
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
        CALL TP_EQUAL
        LD A,(TP_MODE)
        OR A
        RET Z
        JP TP_HIDDEN
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
        XOR A
        LD (TP_ROWS),A
        LD (TP_FULL),A
        INC A
        LD (TP_NEW),A
        JP TP_EQUAL
TP_VISIBLE:
        XOR A
        LD (TP_ROWS),A
        LD (TP_FULL),A
        INC A
        LD (TP_NEW),A
        LD (TP_SHOW),A
        RET
; A=one rendered byte. Caller preserves all registers.
TP_PUT:
        LD (TP_BYTE),A
        LD A,(TP_ACT)
        OR A
        RET NZ
        LD A,(TP_SHOW)
        OR A
        JR NZ,TP_BOUNDARY
        LD A,(TP_MODE)
        OR A
        JR NZ,TP_OUTPUT
        CALL TP_EQUAL
        LD A,(TP_SHOW)
        OR A
        CALL NZ,TP_VISIBLE
TP_BOUNDARY:
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
        ; Other bytes follow the cooked BDOS single-cell column model.
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
TP_GLOBAL:
        LD HL,TP_CUR
        LD B,4
TP_RINC:
        INC (HL)
        JR NZ,TP_RDONE
        INC HL
        DJNZ TP_RINC
TP_RDONE:
        RET
TP_ROW:
        CALL TP_GLOBAL
        LD A,(TP_SHOW)
        OR A
        RET Z
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
        CP '<'
        JP Z,TP_LEFT
        CP '>'
        JP Z,TP_RIGHT
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
        LD A,1
        LD (TP_CLEAR),A
        LD HL,TP_CUR
        LD DE,TP_TARG
        LD BC,4
        LDIR
        RET
TP_PREV:
        LD HL,TP_TOP
        LD B,4
        XOR A
TP_NONZERO:
        OR (HL)
        INC HL
        DJNZ TP_NONZERO
        JP Z,TP_BELL
        CALL TP_ERASE
        LD HL,TP_TOP
        LD DE,TP_TARG
        LD BC,4
        LDIR
        CALL TP_SUB23
        XOR A
        LD (TP_MODE),A
TP_REDO:
        LD A,1
        LD (TP_CLEAR),A
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
        LD A,(TP_CLEAR)
        OR A
        JR Z,TP_CLEAN
        XOR A
        LD (TP_CLEAR),A
        CALL UI_CLEAR               ; explicit clear/home, not a terminal control byte
        ; Clear/home is not CR to cooked BDOS: synchronize its tab column.
        LD E,13
        LD C,2
        CALL BDOS
TP_CLEAN:
        XOR A
        LD (TP_NEW),A
        LD A,(T_FFIRST)
        LD (TP_BEGIN),A
        OR A
        JR NZ,TP_BIND
        LD A,(TP_COL)
        OR A
        JR NZ,TP_BIND
        LD HL,TP_CUR
        LD DE,T_HROW
        LD B,4
TP_HCHECK:
        LD A,(DE)
        CP (HL)
        JR NZ,TP_BIND
        INC HL
        INC DE
        DJNZ TP_HCHECK
        LD A,1
        LD (TP_BEGIN),A
TP_BIND:
        LD HL,(T_FIDX)
        LD (TP_AIDX),HL
        LD HL,TP_CUR
        LD DE,TP_TOP
        LD BC,4
        LDIR
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
        LD A,(TP_MODE)
        OR A
        JR Z,TP_CLAMP
        ; A selected file vanished before replay reached its ordinal.
        LD HL,(T_FIDX)
        LD (TP_WANT),HL
        JP TP_REDO
TP_CLAMP:
        ; The files changed and now end before the requested page: clamp/replay.
        LD HL,TP_CUR
        LD DE,TP_TARG
        LD BC,4
        LDIR
        CALL TP_SUB23
        JP TP_REDO
TP_LAST:
        LD A,1
        LD (TP_EOF),A
        JP TP_WAIT
 ; Subtract one screenful from a row anchor, clamping underflow to zero.
TP_SUB23:
        LD HL,TP_TARG
        LD B,23
        LD C,4
        OR A
TP_SUB:
        LD A,(HL)
        SBC A,B
        LD (HL),A
        LD B,0
        INC HL
        DEC C
        JR NZ,TP_SUB
        RET NC
        XOR A
        LD HL,TP_TARG
        LD B,4
TP_SZERO:
        LD (HL),A
        INC HL
        DJNZ TP_SZERO
        RET
TP_LEFT:
        LD HL,(TP_AIDX)
        LD A,(TP_BEGIN)
        OR A
        JR Z,TP_JUMP
        DEC HL
        LD A,H
        OR L
        JP Z,TP_BELL
        JR TP_JUMP
TP_RIGHT:
        LD HL,(TP_AIDX)
        LD DE,(T_TOTAL)
        OR A
        SBC HL,DE
        JP NC,TP_BELL
        LD HL,(TP_AIDX)
        INC HL
TP_JUMP:
        LD (TP_WANT),HL
        CALL TP_ERASE
        LD A,1
        LD (TP_MODE),A
        JP TP_REDO
TP_GFILE:
        LD A,(TP_MODE)
        OR A
        RET Z
        LD HL,(T_FIDX)
        LD DE,(TP_WANT)
        OR A
        SBC HL,DE
        RET NZ
        XOR A
        LD (TP_MODE),A
        LD (TP_COL),A
        INC A
        LD (TP_NOSEP),A
        CALL TP_GLOBAL
        LD HL,TP_CUR
        LD DE,TP_TARG
        LD BC,4
        LDIR
        JP TP_VISIBLE
TP_MORE: DB 'MORE -- ,/^R back; ./Space/^C next; </> files; ^Q quit.$'
TP_TARG: DS 4
TP_CUR: DS 4
TP_TOP: DS 4
TP_AIDX: DW 0
TP_WANT: DW 0
TP_MODE: DB 0
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
TP_CLEAR: DB 0
TP_NOSEP: DB 0

; @monitor-console@
