; The disk adapter stages physical sectors in HBIOS-managed banked memory.
; Keep LY_BUF intact while checked loaders accumulate carriers there.
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
