; Part 8 candidate ABI-1 binding: HL -> schema, class, 16-byte identity.
; Returns A=0/Z on acceptance. AF,BC,DE,HL clobbered. No state writes.
; Public is class 0 + zero ID; private is class 1 + exact resident ID.
PB_CHECK:
        LD A,(HL)
        CP 1
        JR NZ,PB_BAD
        INC HL
        LD A,(HL)
        INC HL
        OR A
        JR Z,PB_PUBLIC
        DEC A
        JR NZ,PB_BAD
        LD DE,LY_CID
        JP LY_CCMP
PB_PUBLIC:
        LD B,16
PB_ZERO:
        OR (HL)
        INC HL
        DJNZ PB_ZERO
        RET
PB_BAD:
        LD A,0FFH
        OR A
        RET
