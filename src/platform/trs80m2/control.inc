; Engineering target: only BCM2SS. Admit changes of physical assignment for
; B-D, or disconnect them. Reject changes to the format/drive geometry until
; the requested physical contract is implemented. Never partially commit.
CF_PHYS:
CF_FORMAT:
        JP DC_UNSUPPORTED
CF_FAST:
        PUSH IX
        JP DC_UNSUPPORTED
CF_LOG: LD A,(IX+0)
        OR A
        JP Z,DC_UNSUPPORTED
        CALL DC_LOG
        JP NC,DC_INVALID
        LD DE,16
        ADD HL,DE
        PUSH HL
        LD A,(IX+1)
        CP 0FFH
        JR Z,M2_BIND
        CP 4
        JR NC,M2_NO_BIND
        PUSH IX
        POP DE
        INC DE
        INC DE
        LD HL,LY_TAB+17                 ; format bytes from immutable boot binding
        LD B,63
M2_SAME_FMT:
        LD A,(DE)
        CP (HL)
        JR NZ,M2_NO_BIND
        INC HL
        INC DE
        DJNZ M2_SAME_FMT
M2_BIND:POP HL
        LD A,(IX+1)
        LD (HL),A
        CALL DC_RESET
        JP DC_OK
M2_NO_BIND:
        POP HL
        JP DC_UNSUPPORTED
