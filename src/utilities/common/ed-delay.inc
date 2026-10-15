; Z uses DRI's CPU-timed half-second unit (nominally about 2 MHz).
; Reference TIME at 1A11H: B=12; C=B; DEC C/JNZ; DEC A/JNZ, called with
; A=250 twenty times by WAIT. Preserve those loops and polling boundaries.
; Actual elapsed time follows CPU speed, as on the historical editor.
GZ_RUN:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,GZ_KEY
        LD A,(EC_NEG)
        OR A
        JP NZ,EC_BAD
GZ_REPEAT:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        RET Z
        DEC HL
        LD (EC_COUNT),HL
        CALL GZ_WAIT
        RET C
        JP GZ_REPEAT
GZ_KEY:
        LD C,1
        CALL 5
        CP 26
        JP Z,GZ_BREAK
        XOR A
        RET
GZ_WAIT:
        LD A,20
        LD (GZ_TODO),A
GZ_SLICE:
        LD C,11
        CALL 5
        OR A
        JP Z,GZ_SLEEP
        LD C,1
        CALL 5
        JP GZ_BREAK
GZ_SLEEP:
        LD A,250
        CALL GZ_TICK
        LD A,(GZ_TODO)
        DEC A
        LD (GZ_TODO),A
        JP NZ,GZ_SLICE
        XOR A
        RET
GZ_BREAK:
        ; DRI leaves FLAG uninitialized before the first error. EC_INIT makes
        ; that initial state deterministic (zero) instead of exposing TPA junk.
        LD A,(EC_FLAG)            ; DRI WAIT/0Z reuse the previous break flag
        SCF
        RET
GZ_TICK:
        LD B,12
GZ_OUTER:
        LD C,B
GZ_INNER:
        DEC C
        JP NZ,GZ_INNER
        DEC A
        JP NZ,GZ_OUTER
        RET
GZ_TODO: DB 0
