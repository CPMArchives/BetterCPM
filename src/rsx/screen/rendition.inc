; Shared portable SGR interpreter. Parameters and canonical record: see ABI.
AP_ENTRY:
        LD A,C
        CP 17
        JP NC,AP_BAD
        LD (AP_LEFT),A
        LD (AP_PTR),HL
        LD HL,AP_VALUE
        LD DE,AP_WORK
        LD BC,9
        LDIR
        XOR A
        LD (AP_STATE),A
        LD A,(AP_LEFT)
        OR A
        JP NZ,AP_LOOP
        CALL AP_ZERO
        JP AP_DONE
AP_LOOP:
        LD HL,(AP_PTR)
        LD E,(HL)
        INC HL
        LD D,(HL)
        INC HL
        LD (AP_PTR),HL
        LD A,(AP_STATE)
        OR A
        JP NZ,AP_COLOR
        LD A,D
        OR A
        JP NZ,AP_NEXT               ; unknown word value, never truncate
        LD A,E
        OR A
        JP Z,AP_RESET
        CP 10
        JR NC,AP_OTHER
        CP 6
        LD A,16                    ; both slow and rapid blink -> blink
        JR Z,AP_SET
        LD A,E
        CP 7
        JR C,AP_BIT
        DEC A                      ; SGR 6 aliases 5, so 7..9 use bits 5..7
AP_BIT:
        DEC A
        LD B,A
        LD A,1
        JR Z,AP_SET
AP_SHIFT:
        ADD A,A
        DJNZ AP_SHIFT
AP_SET:
        LD HL,AP_WORK
        OR (HL)
        LD (HL),A
        JP AP_NEXT
AP_OTHER:
        CP 22
        LD A,252                   ; normal intensity clears bold + faint
        JP Z,AP_CLEAR
        LD A,E
        CP 23
        LD A,251
        JP Z,AP_CLEAR
        LD A,E
        CP 24
        LD A,247
        JP Z,AP_CLEAR
        LD A,E
        CP 25
        LD A,239
        JP Z,AP_CLEAR
        LD A,E
        CP 27
        LD A,223
        JP Z,AP_CLEAR
        LD A,E
        CP 28
        LD A,191
        JP Z,AP_CLEAR
        LD A,E
        CP 29
        LD A,127
        JP Z,AP_CLEAR
        LD A,E
        CP 38
        LD B,1
        JP Z,AP_BEGIN
        CP 48
        LD B,5
        JP Z,AP_BEGIN
        LD HL,AP_WORK+1
        CP 39
        JR Z,AP_DEFAULT
        CP 49
        JR NZ,AP_RANGE
        LD HL,AP_WORK+5
AP_DEFAULT:
        XOR A
        LD (HL),A
        INC HL
        LD (HL),A
        INC HL
        LD (HL),A
        INC HL
        LD (HL),A
        JP AP_NEXT
AP_RANGE:
        CP 30
        JP C,AP_NEXT
        CP 38
        JR C,AP_FG
        CP 40
        JP C,AP_NEXT
        CP 48
        JR C,AP_BG
        CP 90
        JP C,AP_NEXT
        CP 98
        JR C,AP_BFG
        CP 100
        JP C,AP_NEXT
        CP 108
        JP NC,AP_NEXT
        SUB 60                     ; 100..107 -> 40..47 then bright
        LD E,8
        JR AP_BGC
AP_BFG:
        SUB 60                     ; 90..97 -> 30..37 then bright
        SUB 30
        ADD A,8
        JR AP_FGC
AP_FG:
        SUB 30
AP_FGC:
        LD HL,AP_WORK+1
        JR AP_INDEX
AP_BG:
        LD E,0
AP_BGC:
        SUB 40
        ADD A,E
        LD HL,AP_WORK+5
AP_INDEX:
        LD (HL),1
        INC HL
        LD (HL),A
        INC HL
        LD (HL),0
        INC HL
        LD (HL),0
        JP AP_NEXT
AP_CLEAR:
        LD HL,AP_WORK
        AND (HL)
        LD (HL),A
        JP AP_NEXT
AP_BEGIN:
        LD A,B
        LD (AP_SLOT),A
        LD A,1
        LD (AP_STATE),A
        JP AP_NEXT
AP_COLOR:
        LD A,D
        OR A
        JP NZ,AP_BAD
        LD A,(AP_STATE)
        CP 1
        JR NZ,AP_PART
        LD A,E
        CP 5
        LD A,2
        JR Z,AP_MODE
        LD A,E
        CP 2
        JP NZ,AP_BAD
        LD A,3
AP_MODE:
        LD (AP_STATE),A
        JP AP_NEXT
AP_PART:
        LD A,(AP_SLOT)
        LD C,A
        LD B,0
        LD HL,AP_WORK
        ADD HL,BC
        LD A,(AP_STATE)
        CP 2
        JR Z,AP_IDX
        LD (HL),2
        SUB 2                      ; states 3/4/5 -> record component 1/2/3
        LD C,A
        ADD HL,BC
        LD (HL),E
        LD A,(AP_STATE)
        INC A
        CP 6
        JR Z,AP_ENDC
        LD (AP_STATE),A
        JP AP_NEXT
AP_IDX:
        XOR A
        LD (AP_STATE),A
        LD A,E
        JR AP_INDEX                ; also clears unused color components
AP_ENDC:
        XOR A
        LD (AP_STATE),A
        JP AP_NEXT
AP_RESET:
        CALL AP_ZERO
AP_NEXT:
        LD A,(AP_LEFT)
        DEC A
        LD (AP_LEFT),A
        JP NZ,AP_LOOP
AP_DONE:
        LD A,(AP_STATE)
        OR A
        JP NZ,AP_BAD
        LD HL,AP_WORK
        LD DE,AP_VALUE
        LD BC,9
        LDIR
        LD HL,0
        LD (AP_PTR),HL
        LD HL,AP_VALUE
        XOR A
        RET
AP_BAD:
        LD HL,0
        LD (AP_PTR),HL
        LD A,255
        RET
AP_ZERO:
        LD HL,AP_WORK
        LD B,9
        XOR A
AP_ZLOOP:
        LD (HL),A
        INC HL
        DJNZ AP_ZLOOP
        RET
AP_VALUE: DB 0,0,0,0,0,0,0,0,0
AP_WORK: DB 0,0,0,0,0,0,0,0,0
AP_PTR: DW 0
AP_LEFT: DB 0
AP_STATE: DB 0
AP_SLOT: DB 0
