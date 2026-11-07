; Transient R3MOVE publisher-slot helper, called by the actual RF_SAFE tail.
; HL=49-byte commit request, DE=33-byte prepared profile context.
; Context +31 is the validated prospective owner-validity destination or zero.
; Request +41 points at its own four-byte reservation at +45; +43 is destination.
; Root issues only into durable transaction scratch. No live owner is changed.
VP_PREP:
        EX DE,HL
        LD BC,31
        ADD HL,BC
        LD C,(HL)
        INC HL
        LD B,(HL)
        EX DE,HL
        LD DE,41
        ADD HL,DE
        PUSH BC
        PUSH HL
        LD DE,4
        ADD HL,DE
        EX DE,HL
        POP HL
        LD (HL),E
        INC HL
        LD (HL),D
        INC HL
        POP BC
        LD (HL),C
        INC HL
        LD (HL),B
        LD A,B
        OR C
        RET Z
        EX DE,HL
        JP VG_ALLOC
