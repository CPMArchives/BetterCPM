; Unsigned decimal HL, preserving all caller registers. PN_CHAR consumes A
; and preserves BC/DE/HL. No mutable workspace or recursive division.
PN_U16:
 PUSH AF
 PUSH BC
 PUSH DE
 PUSH HL
 LD BC,PN_POWERS
 XOR A
 LD (PN_STARTED),A
PN_PLACE:
 LD A,(BC)
 LD E,A
 INC BC
 LD A,(BC)
 LD D,A
 INC BC
 LD A,D
 OR E
 JR Z,PN_DONE
 PUSH BC
 LD B,'0'-1
PN_SUBTRACT:
 INC B
 OR A
 SBC HL,DE
 JR NC,PN_SUBTRACT
 ADD HL,DE
 LD A,B
 CP '0'
 JR NZ,PN_DIGIT
 LD A,D
 OR A
 JR NZ,PN_LEADING
 LD A,E
 CP 1
 JR Z,PN_LAST
PN_LEADING:
 LD A,(PN_STARTED)
 OR A
 JR Z,PN_ADVANCE
PN_LAST:
 LD A,B
PN_DIGIT:
 CALL PN_CHAR
 LD A,1
 LD (PN_STARTED),A
PN_ADVANCE:
 POP BC
 JR PN_PLACE
PN_DONE:
 POP HL
 POP DE
 POP BC
 POP AF
 RET
PN_POWERS: DW 10000,1000,100,10,1,0
; Caller supplies PN_STARTED (one byte of mutable diagnostic state).
