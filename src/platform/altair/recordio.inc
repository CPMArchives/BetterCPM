; One physical sector is exactly one CP/M record; do not overwrite LY_BUF
; while the command loader is accumulating its carrier there.
BIOREAD:
        CALL LY_DISK+3
        RET NZ
        LD HL,(BIO_DMA)
        JP LY_DISK+9
BIOWRITE:
        CALL LY_DISK+3
        RET NZ
        LD HL,(BIO_DMA)
        JP LY_DISK+12
BIO_ZERO:
        XOR A
        RET
