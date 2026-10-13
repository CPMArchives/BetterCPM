; Logical character sinks. Validate the entire source list before output.
; Physical aliases and formatting parameters remain separately qualified.
PD_START:
        LD A,(OP_DATA+1)
        CP 6                       ; OUT patch
        JR Z,PD_OUT
        CP 10                      ; LST
        JR Z,PD_LIST
        CP 14                      ; PUN
        JR Z,PD_PUNCH
        CP 18                      ; CON
        JP NZ,PT_UNSUP
        LD A,2
        JR PD_SELECTED
PD_LIST:
        LD A,5
        JR PD_SELECTED
PD_PUNCH:
        LD A,4
        JR PD_SELECTED
PD_OUT:
        XOR A
PD_SELECTED:
        LD (PD_FUNCTION),A
        LD A,1
        LD (PD_ACTIVE),A
        ; Destination qualifiers are not silently ignored.
        LD HL,OP_DATA+44
        LD B,26
PD_DOPTIONS:
        LD A,(HL)
        OR A
        JP NZ,PT_UNSUP
        INC HL
        DJNZ PD_DOPTIONS
        CALL PC_CHECK
        OR A
        JP NZ,PT_UNSUP
        LD HL,OP_DATA+88
        LD DE,PT_SFCB
        LD BC,36
        LDIR
        JP PC_OPEN
PD_PUT:
        LD E,A
        LD A,(PD_FUNCTION)
        OR A
        JR Z,PD_PATCH
        LD C,A
        JP 5
PD_PATCH:
        ; DRI OUT receives its character in C.
        LD C,E
        JP 0106H
PD_ACTIVE: DB 0
PD_FUNCTION: DB 0

; Text-device sources in the common source list. Staging/verification and
; replacement remain the same transaction as disk copies.
PI_START:
        LD A,(OP_DATA)
        CP 2
        JP NZ,PT_UNSUP
        LD A,(OP_DATA+2)
        CP 4
        JP NC,PT_DRIVEERR
        LD HL,OP_DATA+44
        LD B,26
PI_DOPTIONS:
        LD A,(HL)
        OR A
        JP NZ,PT_UNSUP
        INC HL
        DJNZ PI_DOPTIONS
        LD A,1
        LD (PI_ACTIVE),A
        JP PT_INPUTSET
; Carry set for an unavailable or output-only source.
PI_VALID:
        OR A
        RET Z
        CP 5
        RET Z
        CP 18
        RET Z
        CP 19
        RET Z
        CP 20
        RET Z
        SCF
        RET
PI_BEGIN:
        CALL PE_INIT
        LD A,1
        LD (PI_ACTIVE),A
        LD A,40
        LD (PI_LEFT),A
PI_READ:
        LD A,(OP_DATA+81)
        CP 19
        JR Z,PI_NULL
        CP 20
        JR Z,PI_EOFCHAR
        OR A
        JR Z,PI_PATCH
        CP 5
        LD C,3
        JR Z,PI_READER
        LD C,1
        CALL 5
        JR PI_CHAR
PI_READER:
        CALL 5
        AND 7FH                    ; DRI reader strips parity
        JR PI_CHAR
PI_PATCH:
        CALL 0103H
        LD A,(0109H)
PI_CHAR:
        CALL PX_CHAR
        CP 01AH
        JP Z,PC_NEXT
        CALL PE_FEED
        OR A
        JP NZ,PT_WFAIL
        LD A,(PE_DONE)
        OR A
        JP NZ,PC_NEXT
        JP PI_READ
PI_NULL:
        XOR A
        CALL PF_PUT
        OR A
        JP NZ,PT_WFAIL
        LD HL,PI_LEFT
        DEC (HL)
        JP NZ,PI_READ
        JP PC_NEXT
PI_EOFCHAR:
        LD A,01AH
        CALL PF_PUT
        OR A
        JP NZ,PT_WFAIL
        JP PC_NEXT
PI_PUT:
        LD E,A
        LD A,(PX_EFLAG)
        OR A
        JR Z,PI_NORMAL
        LD C,2
        CALL 5
        XOR A
        RET
PI_NORMAL:
        LD A,(PD_ACTIVE)
        OR A
        LD A,E
        JR Z,PI_DISK
        CALL PD_PUT
        XOR A
        RET
PI_DISK:
        PUSH AF
        LD A,(PC_OPOS)
        LD E,A
        LD D,0
        LD HL,PT_DATA
        ADD HL,DE
        POP AF
        LD (HL),A
        LD HL,PC_OPOS
        INC (HL)
        LD A,(HL)
        CP 128
        JR Z,PI_FLUSH
        XOR A
        RET
PI_FLUSH:
        XOR A
        LD (HL),A
        JP PT_FLUSH
PI_ACTIVE: DB 0
PI_LEFT: DB 0

; DRI GETSOURCEC order: strip parity, then upper case (takes precedence
; over lower case). Transform before testing text EOF, including parity EOF.
PX_CHAR:
        LD (PX_RAW),A
        LD A,(OP_DATA+128)
        OR A
        JR Z,PX_INPUT
        LD A,1
        LD (PX_EFLAG),A
        LD A,(PX_RAW)
        CALL PF_PUT
        XOR A
        LD (PX_EFLAG),A
PX_INPUT:
        LD A,(PX_RAW)
        LD E,A
        LD A,(OP_DATA+149)
        OR A
        LD A,E
        JR Z,PX_CASE
        AND 7FH
PX_CASE:
        LD E,A
        LD A,(OP_DATA+144)
        OR A
        JR Z,PX_LOWER
        LD A,E
        CP 'a'
        RET C
        CP 'z'+1
        RET NC
        AND 0DFH
        RET
PX_LOWER:
        LD A,(OP_DATA+135)
        OR A
        LD A,E
        RET Z
        CP 'A'
        RET C
        CP 'Z'+1
        RET NC
        OR 20H
        RET

PX_RAW: DB 0
PX_EFLAG: DB 0
