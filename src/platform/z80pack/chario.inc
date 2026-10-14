; CP/M IOBYTE dispatch for qualified cpmsim character endpoints.
BIOCONST:
        LD A,(0003H)
        LD HL,IO_CS
        JP IO_JUMP

BIOCONIN:
        LD A,(0003H)
        LD HL,IO_CI
        JP IO_JUMP

BIOCONOT:
        LD A,(0003H)
        LD HL,IO_CO
        JP IO_JUMP

BIOREADR:
        LD A,(0003H)
        RRCA
        RRCA
        LD HL,IO_RI
        JP IO_JUMP

BIOPUNCH:
        LD A,(0003H)
        RRCA
        RRCA
        RRCA
        RRCA
        LD HL,IO_PO
        JP IO_JUMP

BIOLIST:
        LD A,(0003H)
        RRCA
        RRCA
        RRCA
        RRCA
        RRCA
        RRCA
        LD HL,IO_LO
        JP IO_JUMP

IO_JUMP:
        AND 3
        ADD A,A
        LD E,A
        LD D,0
        ADD HL,DE
        LD E,(HL)
        INC HL
        LD D,(HL)
        EX DE,HL
        JP (HL)
IO_NONE:
        XOR A
        RET
IO_EOF:
        LD A,01AH
        RET
IO_READY:
        LD A,0FFH
        RET
IO_STAT:
        LD A,1
        CALL MC_CALL
        OR A
        RET Z
        JP IO_READY
IO_INPUT:
        LD A,2
        CALL MC_CALL
        AND 07FH
        RET

IO_CS: DW IO_STAT,IO_STAT,IO_BSTAT,IO_NONE

IO_CI: DW IO_INPUT,IO_INPUT,BIOREADR,IO_EOF

IO_CO: DW MH_OUT,MH_OUT,BIOLIST,IO_NONE

IO_RI: DW IO_INPUT,IO_AUXIN,IO_EOF,IO_EOF

IO_PO: DW MH_OUT,IO_AUXOT,IO_NONE,IO_NONE

IO_LO: DW MH_OUT,MH_OUT,IO_PRINT,IO_NONE

IO_LS: DW IO_READY,IO_READY,IO_LSTAT,IO_NONE

IO_AUXIN:
        IN A,(5)
        RET
IO_AUXOT:
        LD A,C
        OUT (5),A
        RET
IO_PRINT:
        LD A,C
        OUT (3),A
        RET
IO_LSTAT:
        IN A,(2)
        RET
; BAT has no portable reader-ready vector. TTY polls the console; PTR is a
; synchronous read/EOF source, so status permits the next read. Port 4 is EOF,
; not readiness. Unsupported reader selections are not ready.
IO_BSTAT:
        LD A,(0003H)
        AND 0CH
        JP Z,IO_STAT
        CP 4
        JP Z,IO_READY
        JP IO_NONE
