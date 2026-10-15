; R: exact library filename with simple DU, defaulting to the current source DU.
; No name means the historical transfer library (X adds its buffered tail later).
; Numeric prefixes are illegal. DRI READFILE treats any nonzero read as EOF.
GR_RUN:
        LD A,(EC_PREFIX)
        OR A
        JP NZ,EC_BAD
        LD A,(EC_RAW)
        CP 'R'
        LD A,1
        JP Z,GR_CASE
        LD A,(EC_UPPER)
GR_CASE:
        LD (GR_UPPER),A
        XOR A
        LD (GR_LEN),A
        LD (GR_DOT),A
GR_COLLECT:
        CALL EC_GET
        LD (EC_WHERE),A
        CP 13
        JP Z,GR_PARSE
        CP 26
        JP Z,GR_PARSE
        LD C,A
        LD A,(GR_LEN)
        CP 16
        JP NC,GR_LONG
        LD E,A
        LD D,0
        LD HL,EI_TOKEN
        ADD HL,DE
        LD (HL),C
        INC A
        LD (GR_LEN),A
        LD A,C
        CP '.'
        JP NZ,GR_COLLECT
        LD A,1
        LD (GR_DOT),A
        JP GR_COLLECT
GR_PARSE:
        LD A,(GR_LEN)
        LD E,A
        LD D,0
        LD HL,EI_TOKEN
        ADD HL,DE
        LD (HL),0
        LD A,(GR_LEN)
        OR A
        JP NZ,GR_LOCATION
        LD HL,GR_XNAME
        LD DE,EI_TOKEN
        LD BC,13
        LDIR
        LD A,1
        LD (GR_DOT),A
GR_LOCATION:
        LD A,(EI_SDRV)
        LD (EI_DRV),A
        LD A,(EI_SUSR)
        LD (EI_USR),A
        CALL EI_LOCREST
        JP C,EC_BAD
        LD A,(EI_QUAL)
        OR A
        JP Z,GR_BOUND
        CALL EI_LOC               ; qualified operands inherit captured caller
        JP C,EC_BAD
GR_BOUND:
        LD A,(EI_DRV)
        LD (GR_DRIVE),A
        LD A,(EI_USR)
        LD (GR_USER),A
        LD HL,EI_FCB
        LD DE,GR_SAVED
        LD BC,36
        LDIR
        CALL EI_FILE
        PUSH AF
        LD HL,EI_FCB
        LD DE,GR_FCB
        LD BC,36
        LDIR
        LD HL,GR_SAVED
        LD DE,EI_FCB
        LD BC,36
        LDIR
        POP AF
        JP C,EC_BAD
        LD A,(GR_DRIVE)
        INC A
        LD (GR_FCB),A
        LD A,(GR_DOT)
        OR A
        JP NZ,GR_OPEN
        LD HL,GR_LIB
        LD DE,GR_FCB+9
        LD BC,3
        LDIR
GR_OPEN:
        LD A,(GR_DRIVE)
        LD E,A
        LD C,14
        CALL 5
        LD A,(GR_USER)
        LD E,A
        LD C,32
        CALL 5
        LD DE,GR_DATA
        LD C,26
        CALL 5
        LD DE,GR_FCB
        LD C,15
        CALL 5
        CP 255
        JP Z,GR_MISSING
GR_RECORD:
        LD DE,GR_DATA
        LD C,26
        CALL 5
        LD DE,GR_FCB
        LD C,20
        CALL 5
        OR A
        RET NZ
        XOR A
        LD (GR_POS),A
GR_BYTE:
        LD A,(GR_POS)
        LD E,A
        LD D,0
        LD HL,GR_DATA
        ADD HL,DE
        LD A,(HL)
        CP 26
        JP Z,GR_DONE
        LD C,A
        LD A,(GR_UPPER)
        OR A
        LD A,C
        CALL NZ,EI_UP
        LD C,A
        LD (EC_WHERE),A
        CALL EB_PUT
        JP C,EC_FULL
        LD A,(GR_POS)
        INC A
        LD (GR_POS),A
        CP 128
        JP Z,GR_RECORD
        JP GR_BYTE
GR_DONE:
        XOR A
        RET
GR_LONG:
        LD A,'#'
        SCF
        RET
GR_MISSING:
        LD A,'O'
        SCF
        RET
GR_XNAME: DB 'X$$$$$$$.LIB',0
GR_LIB: DB 'LIB'
GR_LEN: DB 0
GR_DOT: DB 0
GR_UPPER: DB 0
GR_DRIVE: DB 0
GR_USER: DB 0
GR_POS: DB 0
GR_SAVED: DS 36
GR_FCB: DS 36
GR_DATA: DS 128
