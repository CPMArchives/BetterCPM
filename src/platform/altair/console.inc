; Poll the 88-2SIO transmitter; input returns all eight bits.
AL_CONST:
        IN A,(AL_SSTAT)
        AND 1
        RET
AL_CONIN:
        CALL AL_CONST
        JR Z,AL_CONIN
        IN A,(AL_SDATA)
        RET
AL_CONOUT:
        IN A,(AL_SSTAT)
        AND 2
        JR Z,AL_CONOUT
        LD A,C
        OUT (AL_SDATA),A
        RET
AL_STRING:
        LD A,(HL)
        INC HL
        OR A
        RET Z
        LD C,A
        CALL AL_CONOUT
        JR AL_STRING

