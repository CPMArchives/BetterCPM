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
        CALL PT_SOURCE
        LD DE,PT_SFCB
        LD C,15
        CALL 5
        CP 0FFH
        JP Z,PT_NOFILE
        LD A,1
        LD (PT_SRCOPEN),A
        LD A,(PT_SFCB+10)
        AND 80H
        JP Z,PC_BEGIN
        LD A,(OP_DATA+141)
        OR A
        JP Z,PT_NOFILE
        JP PC_BEGIN
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
