; DUP menu/drive presentation before migration.
; Source commit 25fbf0b73dbc0143825a656d42e34a7703ef298f.
CHOICE: LD HL,CHMSG
        CALL PUTS
        LD A,' '
        CALL INVERSE
        LD A,']'
        CALL PUTC
; Leave the visible cursor in the blank field, not after the closing bracket.
        LD A,8
        CALL PUTC
        CALL PUTC
        CALL KEY
        PUSH AF
        LD A,13
        CALL PUTC
        LD HL,CHMSG
        CALL PUTS
        POP AF
        PUSH AF
        CALL PUTC
        LD A,']'
        CALL PUTC
        CALL CRLF
        POP AF
        RET
