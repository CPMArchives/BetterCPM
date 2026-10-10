; Transient DIR output and optional paging. All emitted LF characters count,
; including DU headings and summaries. The supported baseline is 24 rows.
; Pause lazily before the next character, never solely because final LF hit 23.
DG_PRINT:
        LD H,D
        LD L,E
DG_TEXT:
        LD A,(HL)
        CP '$'
        RET Z
        PUSH HL
        CALL DG_CHAR
        POP HL
        INC HL
        JR DG_TEXT
DG_CHAR:
        PUSH AF
        PUSH HL
        LD HL,DG_CHARS
        INC (HL)
        LD A,(DG_MEASURE)
        OR A
        POP HL
        JR Z,DG_VISIBLE
        POP AF
        RET
DG_VISIBLE:
        POP AF
        PUSH AF
        PUSH HL
        PUSH BC
        PUSH DE
        LD A,(DG_PAGE)
        OR A
        JR Z,DG_EMIT
        LD A,(DG_LINES)
        CP 23
        CALL NC,DG_PAUSE
DG_EMIT:
        POP DE
        POP BC
        POP HL
        POP AF
        PUSH AF
        LD E,A
        LD C,2
        CALL BDOS
        POP AF
        CP 10
        RET NZ
        LD HL,DG_LINES
        INC (HL)
        RET
DG_PAUSE:
        LD DE,DG_MORE
        LD C,9
        CALL BDOS
DG_WAIT:
        LD E,0FFH
        LD C,6
        CALL BDOS
        CP 3
        JR Z,DG_ABORT
        CP ' '
        JR Z,DG_NEXT
        CP 13
        JR NZ,DG_WAIT
DG_NEXT:
        LD DE,DG_ERASE
        LD C,9
        CALL BDOS
        XOR A
        LD (DG_LINES),A
        RET
DG_ABORT:
        LD DE,DG_CANCEL
        LD C,9
        CALL BDOS
        LD SP,(DG_STACK)             ; unwind output and formatter frames
        JP BC_DURST                  ; restore DU, then return to COM caller
DG_CHARS: DB 0
DG_MEASURE: DB 0
DG_PAGE: DB 0
DG_LINES: DB 0
DG_STACK: DW 0
DG_MORE: DB 'MORE -- Space/ENTER for next page; ^C abort.$'
DG_MEND:
DG_ERASE: DB 13
        REPT DG_MEND-DG_MORE-1
        DB ' '
        ENDM
        DB 13,'$'
DG_CANCEL: DB '^C',13,10,'$'
