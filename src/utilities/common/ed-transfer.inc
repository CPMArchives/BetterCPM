; X copies a nonmoving forward line range to X$$$$$$$.LIB. Zero X clears it.
; Full records are written only when the next byte arrives. Bare R appends
; pending bytes verbatim, unlike its translated disk-record input (DRI quirk).
; Intentional DRI bug fix: retain the creation DU across O/H. The pinned DRI
; binary corrupts pending text/orphans the file after split O and cannot find
; it after split H. Separate buffers and explicit binding preserve the data;
; exit cleanup deletes the bound file regardless of the final output DU.
GX_INIT:
        XOR A
        LD (GX_ACTIVE),A
        LD (GX_POS),A
        LD (GX_BAD),A
        LD HL,GX_FCB
        LD DE,GX_FCB+1
        LD BC,35
        LD (HL),0
        LDIR
        LD HL,GX_NAME
        LD DE,GX_FCB+1
        LD BC,11
        LDIR
        RET
GX_RUN:
        LD HL,(EC_COUNT)
        LD A,H
        OR L
        JP Z,GX_CLEAR
        LD A,(EC_NEG)
        OR A
        JP NZ,EC_BAD
        LD A,(GX_ACTIVE)
        OR A
        JP NZ,GX_RANGE
        CALL GX_INIT
        CALL GX_BIND
        LD A,1
        LD (GX_ACTIVE),A
        CALL GX_SELECT
        LD DE,GX_FCB
        LD C,19
        CALL 5
        LD DE,GX_FCB
        LD C,22
        CALL 5
        CP 255
        JP Z,GX_FAIL
GX_RANGE:
        CALL ET_SELECT
GX_LOOP:
        LD HL,(ET_PTR)
        LD DE,(ET_LAST)
        OR A
        SBC HL,DE
        JP Z,GX_OK
        LD HL,(ET_PTR)
        CALL ET_GET
        LD C,A
        CALL GX_PUT
        RET C
        LD HL,(ET_PTR)
        INC HL
        LD (ET_PTR),HL
        JP GX_LOOP
GX_CLEAR:
        LD A,(GX_ACTIVE)
        OR A
        JP Z,GX_CLRNEW
        CALL GX_CLEAN
        CALL GX_INIT
        JP GX_OK
GX_CLRNEW:
        CALL GX_INIT
        CALL GX_BIND
        CALL GX_SELECT
        LD DE,GX_FCB
        LD C,19
        CALL 5
GX_OK:
        XOR A
        RET
GX_BIND:
        LD A,(EI_SDRV)
        LD (GX_DRIVE),A
        INC A
        LD (GX_FCB),A
        LD A,(EI_SUSR)
        LD (GX_USER),A
        RET
GX_SELECT:
        LD A,(GX_DRIVE)
        LD E,A
        LD C,14
        CALL 5
        LD A,(GX_USER)
        LD E,A
        LD C,32
        CALL 5
        LD DE,GX_DATA
        LD C,26
        JP 5
GX_PUT:
        LD A,(GX_BAD)
        OR A
        JP NZ,GX_FAIL
        PUSH BC
        LD A,(GX_POS)
        CP 128
        JP NZ,GX_ROOM
        CALL GX_SELECT
        LD DE,GX_FCB
        LD C,21
        CALL 5
        OR A
        JP NZ,GX_WRITEFAIL
        LD (GX_POS),A
GX_ROOM:
        POP BC
        LD A,(GX_POS)
        LD E,A
        LD D,0
        LD HL,GX_DATA
        ADD HL,DE
        LD (HL),C
        INC A
        LD (GX_POS),A
        XOR A
        RET
GX_WRITEFAIL:
        POP BC
GX_FAIL:
        LD (GX_BAD),A
        LD (EC_IOERR),A
        LD A,'?'
        SCF
        RET
GX_CLEAN:
        LD A,(GX_ACTIVE)
        OR A
        RET Z
        CALL GX_SELECT
        LD DE,GX_FCB
        LD C,19
        CALL 5
        XOR A
        LD (GX_ACTIVE),A
        RET
GX_CLOSE:
        LD A,(GX_ACTIVE)
        OR A
        RET Z
        CALL GX_SELECT
        LD DE,GX_FCB
        LD C,16
        JP 5
GX_TAIL:
        LD A,(GX_ACTIVE)
        OR A
        JP Z,GX_OK
        XOR A
        LD (GX_READ),A
GX_TREAD:
        LD A,(GX_READ)
        LD B,A
        LD A,(GX_POS)
        CP B
        JP Z,GX_OK
        LD E,B
        LD D,0
        LD HL,GX_DATA
        ADD HL,DE
        LD C,(HL)
        LD A,C
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD A,(GX_READ)
        INC A
        LD (GX_READ),A
        JP GX_TREAD
GX_NAME: DB 'X$$$$$$$LIB'
GX_ACTIVE: DB 0
GX_POS: DB 0
GX_BAD: DB 0
GX_DRIVE: DB 0
GX_USER: DB 0
GX_READ: DB 0
GX_FCB: DS 36
GX_DATA: DS 128
