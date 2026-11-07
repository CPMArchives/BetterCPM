M2_FMMAP:
        LD (B_PSide),A
        LD (BIO_PCYL),A
        LD (BIO_QUART),A
        LD A,(BIO_SECTOR)
        CP 26
        JP NC,DC_MAPBAD
        INC A
        LD (BIO_PSEC),A
        XOR A
        JP DC_SETSIZE
; Data transfers are admitted only for the selected physical release medium.
DC_READ:LD C,080H
        JR M2_PHYS
DC_WRITE:LD C,0A0H
M2_PHYS:
        LD A,(B_PSide)
        OR A
        JP NZ,M2_RAW_BAD
        LD A,(BIO_PCYL)
        LD D,A
        OR A
        LD A,(DC_SIZE)
        JR NZ,M2_DATA_SIZE
        OR A
        JR M2_SIZE_OK
M2_DATA_SIZE:
        CP 2
M2_SIZE_OK:
        JP NZ,M2_RAW_BAD
        LD A,(BIO_PSEC)
        LD E,A
        LD A,(B_PDrive)
        LD B,0
M2_DRNO:RRCA
        JR C,M2_DRSET
        INC B
        BIT 2,B
        JP NZ,M2_RAW_BAD
        JR M2_DRNO
M2_DRSET:
        LD A,B
        JP M2_XFER
        INCLUDE transfer.inc
