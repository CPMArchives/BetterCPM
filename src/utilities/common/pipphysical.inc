; BIOS API 1.6 private capability vector is at BIOS+63. Older BIOSes fail
; physical aliases safely; never call that address without checking the API.
DV_CAPS:
        PUSH BC
        PUSH DE
        XOR A
        LD (DV_KNOWN),A
        LD HL,0
        LD (DV_CAP),HL
        LD C,180
        CALL 5
        LD A,(HL)
        CP 'B'
        JP NZ,DV_NOCAP
        INC HL
        LD A,(HL)
        CP 'V'
        JP NZ,DV_NOCAP
        INC HL
        LD A,(HL)
        CP 1
        JP NZ,DV_NOCAP
        INC HL
        LD A,(HL)
        CP 3
        JP C,DV_NOCAP
        LD DE,19
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        LD DE,DV_API
        LD B,2
DV_VLOOP:
        LD A,(DE)
        CP (HL)
        JP NZ,DV_NOCAP
        INC DE
        INC HL
        DJNZ DV_VLOOP
        ; Compatible ABI 1.x, minor >=6; bound parsing to two decimal digits.
        LD A,(HL)
        SUB '0'
        CP 10
        JP NC,DV_NOCAP
        LD C,A
        INC HL
        LD A,(HL)
        CP '$'
        JR Z,DV_MINOR
        SUB '0'
        CP 10
        JP NC,DV_NOCAP
        LD E,A
        LD A,C
        ADD A,A
        LD D,A
        ADD A,A
        ADD A,A
        ADD A,D
        ADD A,E
        LD C,A
        INC HL
        LD A,(HL)
        CP '$'
        JP NZ,DV_NOCAP
DV_MINOR:
        LD A,C
        CP 6
        JP C,DV_NOCAP
        LD A,1
        LD (DV_KNOWN),A
        LD HL,(1)
        LD DE,60
        ADD HL,DE
        CALL DV_JUMP
        LD (DV_CAP),HL
DV_NOCAP:
        POP DE
        POP BC
        RET
DV_LOGOUT:
        LD A,(PD_PHYS)
        CP 0FFH
        JR Z,DV_LOUT
        OR A
        RET                            ; physical destination already checked
DV_LOUT:
        LD A,(PD_FUNCTION)
        OR A
        RET Z                          ; OUT patch is not a BIOS device
        LD B,0
        CP 2
        JR Z,DV_LOGICAL
        LD B,8
        CP 4
        JR Z,DV_LOGICAL
        LD B,12
        JR DV_LOGICAL
DV_LOGIN:
        LD B,0
        CP 18
        JR Z,DV_LOGICAL
        LD B,4
DV_LOGICAL:
        CALL DV_CAPS
        LD A,(DV_KNOWN)
        OR A
        RET Z                          ; old BIOS: retain legacy logical behavior
        LD A,B
        LD C,A
        LD A,B
        RRCA                           ; bit shift of IOBYTE field = nibble / 2
        LD B,A
        LD A,(0003H)
        INC B
DV_LSHIFT:
        DEC B
        JR Z,DV_LSELECT
        RRCA
        JR DV_LSHIFT
DV_LSELECT:
        AND 3
        ADD A,C
        LD B,A
        LD HL,(DV_CAP)
        INC B
DV_LCAP:
        SRL H
        RR L
        DJNZ DV_LCAP
        JR NC,DV_BAD
        OR A
        RET
DV_INOK:
        PUSH AF
        CALL DV_CAPS
        POP AF
        CALL DV_TABLE
        LD DE,3
        ADD HL,DE
        LD A,(HL)
        CP 0FFH
        JR Z,DV_BAD
        JP DV_BIT
DV_OUTOK:
        PUSH AF
        CALL DV_CAPS
        POP AF
        CALL DV_TABLE
        LD DE,4
        ADD HL,DE
        LD A,(HL)
        CP 0FFH
        JR Z,DV_BAD
DV_BIT:
        LD HL,(DV_PTR)
        LD A,(HL)
        CP 16
        JR NC,DV_BAD
        LD B,A
        LD HL,(DV_CAP)
        INC B
DV_SHIFT:
        SRL H
        RR L
        DJNZ DV_SHIFT
        JR NC,DV_BAD
        OR A
        RET
DV_BAD:
        SCF
        RET
DV_TABLE:
        LD E,A
        LD D,0
        LD HL,DV_MAP
        LD B,5
DV_TADD:
        ADD HL,DE
        DJNZ DV_TADD
        LD (DV_PTR),HL
        RET
; A=device, B=0 input / 1 output; C=output character. Change only its
; IOBYTE field around one standard BDOS call, then restore the exact old byte.
; Cooked console Ctrl-C retains DRI fatal-WBOOT semantics: no return from
; that call, hence no ordinary transfer cleanup or per-call IOBYTE restoration.
DV_RAW:
        PUSH BC
        CALL DV_TABLE
        INC HL
        LD A,(0003H)
        LD (DV_OLD),A
        AND (HL)
        INC HL
        OR (HL)
        LD (0003H),A
        INC HL
        POP BC
        LD A,B
        OR A
        JR Z,DV_VECTOR
        INC HL
DV_VECTOR:
        LD A,(HL)                      ; standard BDOS service for this endpoint
        LD E,C                         ; character supplied by output callers
        LD C,A
        CALL 5
        PUSH AF
        LD A,(DV_OLD)
        LD (0003H),A
        POP AF
        RET
DV_JUMP:
        JP (HL)
DV_API: DB '1.6','$'
DV_KNOWN: DB 0
DV_CAP: DW 0
DV_PTR: DW 0
DV_OLD: DB 0
; capability bit, clear mask, selected value, input/output BDOS functions
DV_MAP:
        DB 255,255,0,255,255      ; INP (handled separately)
        DB 255,255,0,255,255      ; IRD Intel/ICOM hardware, not implemented
        DB 5,243,4,3,255         ; PTR
        DB 6,243,8,3,255         ; UR1
        DB 7,243,12,3,255        ; UR2
        DB 255,255,0,255,255      ; RDR logical
        DB 255,255,0,255,255      ; OUT patch
        DB 14,63,128,255,5       ; LPT
        DB 15,63,192,255,5       ; UL1
        DB 14,63,128,255,5       ; PRN
        DB 255,255,0,255,255      ; LST logical
        DB 9,207,16,255,4        ; PTP
        DB 10,207,32,255,4       ; UP1
        DB 11,207,48,255,4       ; UP2
        DB 255,255,0,255,255      ; PUN logical
        DB 0,252,0,1,2           ; TTY
        DB 1,252,1,1,2           ; CRT
        DB 3,252,3,1,2           ; UC1
        DB 255,255,0,255,255      ; CON logical
        DB 255,255,0,255,255      ; NUL
        DB 255,255,0,255,255      ; EOF
