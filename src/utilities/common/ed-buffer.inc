; ED text gap. [EB_FIRST,EB_FRONT) is before cursor; [EB_BACK,EB_LIMIT)
; is after it. The caller supplies writable [HL,DE), separate from program/stack.
; No disk or console calls. Character primitives return carry at a boundary.
EB_INIT:
        PUSH HL
        OR A
        SBC HL,DE
        POP HL
        JP NC,EB_FAIL
        LD (EB_FIRST),HL
        LD (EB_FRONT),HL
        LD (EB_BACK),DE
        LD (EB_LIMIT),DE
        LD HL,1
        LD (EB_BASE),HL
        OR A
        RET
EB_PUT:
        LD HL,(EB_FRONT)
        LD DE,(EB_BACK)
        OR A
        SBC HL,DE
        JP Z,EB_FAIL
        LD HL,(EB_FRONT)
        LD (HL),C
        INC HL
        LD (EB_FRONT),HL
        OR A
        RET
EB_RIGHT:
        LD HL,(EB_BACK)
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        JP Z,EB_FAIL
        LD HL,(EB_BACK)
        LD A,(HL)
        INC HL
        LD (EB_BACK),HL
        LD HL,(EB_FRONT)
        LD (HL),A
        INC HL
        LD (EB_FRONT),HL
        OR A
        RET
EB_LEFT:
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        JP Z,EB_FAIL
        LD HL,(EB_FRONT)
        DEC HL
        LD A,(HL)
        LD (EB_FRONT),HL
        LD HL,(EB_BACK)
        DEC HL
        LD (HL),A
        LD (EB_BACK),HL
        OR A
        RET
EB_DEL:
        LD HL,(EB_BACK)
        LD DE,(EB_LIMIT)
        OR A
        SBC HL,DE
        JP Z,EB_FAIL
        LD HL,(EB_BACK)
        INC HL
        LD (EB_BACK),HL
        OR A
        RET
EB_ERASE:
        LD HL,(EB_FRONT)
        LD DE,(EB_FIRST)
        OR A
        SBC HL,DE
        JP Z,EB_FAIL
        LD HL,(EB_FRONT)
        DEC HL
        LD (EB_FRONT),HL
        OR A
        RET
EB_TOP:
        CALL EB_LEFT
        JP NC,EB_TOP
        OR A
        RET
EB_END:
        CALL EB_RIGHT
        JP NC,EB_END
        OR A
        RET
EB_FAIL:
        SCF
        RET
EB_FIRST: DW 0
EB_FRONT: DW 0
EB_BACK: DW 0
EB_LIMIT: DW 0

EB_BASE: DW 1
