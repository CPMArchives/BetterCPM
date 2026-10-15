; DRI M captures the rest of the line, preserving Ctrl-Z command separators.
; Counts 0/1/omitted repeat until failure/interruption; N>1 runs N iterations
; then returns the historical # break. Macro bytes form one continuous stream,
; so string commands can read across iteration boundaries. No nested M.
GM_DEFINE:
        LD A,(GM_ACTIVE)
        OR A
        JP NZ,EC_BAD
        LD A,(EC_NEG)
        OR A
        JP Z,GM_START
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP NZ,EC_BAD
GM_START:
        LD A,(EC_RAW)
        CP 'M'
        LD A,1
        JP Z,GM_CASE
        LD A,(EC_UPPER)
GM_CASE:
        LD (GM_UPPER),A
        XOR A
        LD (GM_LEN),A
        LD (GM_POS),A
        LD HL,(EC_COUNT)
        LD A,H
        OR A
        JP NZ,GM_COUNT
        LD A,L
        CP 1
        JP NZ,GM_COUNT
        LD HL,0
GM_COUNT:
        LD (GM_LEFT),HL
GM_COPY:
        LD A,(EC_LEFT)
        OR A
        JP Z,GM_READY
        CALL EC_GET
        CP 13
        JP Z,GM_READY
        LD C,A
        LD A,(GM_UPPER)
        OR A
        LD A,C
        CALL NZ,EI_UP
        LD C,A
        LD A,(GM_LEN)
        CP 128
        JP NC,EC_FULL
        LD E,A
        LD D,0
        LD HL,GM_TEXT
        ADD HL,DE
        LD (HL),C
        INC A
        LD (GM_LEN),A
        JP GM_COPY
GM_READY:
        LD A,(GM_LEN)
        OR A
        RET Z
        LD A,1
        LD (GM_ACTIVE),A
        XOR A
        RET
GM_GET:
        LD C,11
        CALL 5
        OR A
        JP Z,GM_READ
        LD C,1
        CALL 5
        JP GM_BREAK
GM_READ:
        LD A,(GM_POS)
        LD B,A
        LD A,(GM_LEN)
        CP B
        JP NZ,GM_BYTE
        LD HL,(GM_LEFT)
        LD A,H
        OR L
        JP Z,GM_RESET
        DEC HL
        LD (GM_LEFT),HL
        LD A,H
        OR L
        JP Z,GM_BREAK
GM_RESET:
        LD B,0
GM_BYTE:
        LD E,B
        LD D,0
        LD HL,GM_TEXT
        ADD HL,DE
        LD A,B
        INC A
        LD (GM_POS),A
        LD A,(HL)
        RET
GM_BREAK:
        ; READC in DRI abandons the entire macro evaluation, even when called
        ; inside string collection. Restore only this command-run stack frame.
        XOR A
        LD (GM_ACTIVE),A
        LD SP,(GM_STACK)
        LD A,'#'
        SCF
        RET
GM_ACTIVE: DB 0
GM_UPPER: DB 0
GM_LEN: DB 0
GM_POS: DB 0
GM_LEFT: DW 0
GM_STACK: DW 0
GM_TEXT: DS 128
