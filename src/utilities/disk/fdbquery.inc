; Entry-only query code occupies load-time bytes later reused by IMPORTBUF.
; It must run before any catalogue/editor work or terminal/BDOS setup.
; The shared recognizers accept bounded exact tokens; help wins over version.
; Use the resident private stack without initializing any working state.
FDBQUERY:
        LD (OLDSP),SP
        LD SP,STACKTOP
        PUSH AF
        PUSH BC
        PUSH DE
        PUSH HL
        PUSH IX
        PUSH IY
        LD A,(80H)
        OR A
        JR Z,FDBQNONE
        CP 128
        JR NC,FDBQNONE
        LD B,A
        LD HL,81H
        LD DE,FDBQHELP
        CALL UH_QUERY
        JR C,FDBQRETURN
        LD DE,FDBQVER
        CALL UV_QUERY
        JR C,FDBQRETURN
FDBQNONE:
        POP IY
        POP IX
        POP HL
        POP DE
        POP BC
        POP AF
        LD SP,(OLDSP)
        JP START
FDBQRETURN:
        POP IY
        POP IX
        POP HL
        POP DE
        POP BC
        POP AF
        LD SP,(OLDSP)
        RET
; @fdb-query-text@
; @fdb-query-matchers@
