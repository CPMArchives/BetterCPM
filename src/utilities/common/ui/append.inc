; Append-only compatibility event engine, extracted from REN's name field.
; Caller owns UA_BUF (capacity bytes), UA_LEN, UA_FULL and UA_MAX bytes.
; No I/O, allocation, case conversion, filename validation or redraw.
; UA_INIT: A=capacity 1..255; clears length/overflow, returns UI_MORE.
; UA_KEY: A=raw byte; returns UI_MORE/SEND/ABORT/LIMIT, carry clear.
; UA_PUT: A=literal byte, bypass controls; returns UI_MORE/LIMIT, carry clear.
; Ctrl-C aborts, CR submits even empty, BS/DEL remove last byte, Ctrl-U clears.
; Other bytes append literally. Overflow remains sticky after backspace and
; submission; only INIT/Ctrl-U resets it. Caller MUST reject overflowed input.
; This is historical compatibility, not the standard editor for new fields.
; Clobbers AF/BC/DE/HL. No terminator is written; buffer tails are unspecified.
UA_INIT:
        OR A
        JR Z,UA_BAD
        LD (UA_MAX),A
UA_CLEAR:
        XOR A
        LD (UA_LEN),A
        LD (UA_FULL),A
        RET
UA_BAD:
        LD A,UI_BAD
        OR A
        RET
UA_KEY:
        CP 3
        JR Z,UA_ABORT
        CP 13
        JR Z,UA_SEND
        CP 8
        JR Z,UA_BACK
        CP 127
        JR Z,UA_BACK
        CP 21
        JR Z,UA_CLEAR
UA_PUT:
        ; Literal append entry for adapters with different control-key policies.
        LD E,A
        LD A,(UA_LEN)
        LD B,A
        LD A,(UA_MAX)
        CP B
        JR Z,UA_OVER
        LD L,B
        LD H,0
        LD BC,UA_BUF
        ADD HL,BC
        LD (HL),E
        LD HL,UA_LEN
        INC (HL)
UA_MORE:
        XOR A
        RET
UA_BACK:
        LD A,(UA_LEN)
        OR A
        JR Z,UA_MORE
        DEC A
        LD (UA_LEN),A
        JR UA_MORE
UA_OVER:
        LD A,1
        LD (UA_FULL),A
        LD A,UI_LIMIT
        OR A
        RET
UA_ABORT:
        LD A,UI_ABORT
        OR A
        RET
UA_SEND:
        LD A,UI_SEND
        OR A
        RET
