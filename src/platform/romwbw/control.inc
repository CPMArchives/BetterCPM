        INCLUDE state.inc
; ABI 6 block-device control, executed in the checked 1 KiB CFG overlay.
; IX is the request pointer, with the caller's IX pushed by the resident gate.
WB_CONTROL:
        PUSH IX
        POP DE
        LD A,D
        OR A
        JP Z,WC_INVALID
        LD HL,80
        ADD HL,DE
        JP C,WC_INVALID
        LD DE,(6)
        OR A
        SBC HL,DE
        JR Z,WC_VALID
        JP NC,WC_INVALID
WC_VALID:
        LD A,(IX+0)
        CP 2
        JP NC,WC_INVALID
        CALL WC_DPH
        LD (WC_BIND),HL
        LD A,(WB_OP)
        CP 3
        JR Z,WC_GET
        CP 4
        JP NZ,WC_UNSUPPORTED
        LD A,(IX+0)
        OR A
        JP Z,WC_UNSUPPORTED             ; A is the protected firmware boot binding
        PUSH IX
        POP DE
        INC DE
        INC DE
        INC HL
        LD B,63
WC_COMPARE:
        LD A,(DE)
        CP (HL)
        JP NZ,WC_UNSUPPORTED
        INC DE
        INC HL
        DJNZ WC_COMPARE
        LD A,(IX+1)
        LD (WB_PENDING),A
        CP 0FFH
        JR Z,WC_COMMIT
        LD C,A
        LD A,(LY_TAB+16)
        CP C
        JP Z,WC_UNSUPPORTED
        LD B,01AH
        CALL 0FFF0H
        JP NZ,WC_INVALID
        LD A,B
        CP 2
        JP NZ,WC_UNSUPPORTED
        LD A,C
        OR D
        OR E
        JP NZ,WC_UNSUPPORTED
        LD DE,16640
        OR A
        SBC HL,DE
        JP NZ,WC_UNSUPPORTED
WC_COMMIT:
        LD A,(WB_PENDING)
        LD (LY_TAB+96),A
        PUSH IX
        LD DE,0FFFFH
        LD C,37
        CALL LY_BDOS                    ; invalidate login/cache state after publication
        POP IX
        LD HL,0
        JR WC_RETURN
WC_GET:
        PUSH IX
        POP DE
        INC DE
        LD BC,64
        LDIR
        LD HL,0
        JR WC_RETURN
WC_UNSUPPORTED:
        LD HL,2
        JR WC_RETURN
WC_INVALID:
        LD HL,1
WC_RETURN:
        LD A,L
        POP IX
        OR A
        RET
WC_DPH:
        LD HL,LY_TAB+16
        OR A
        RET Z
        LD DE,80
        ADD HL,DE
        RET
WC_BIND: DW 0
