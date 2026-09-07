; DIRECT RECORD DMA -- 07-Sep-2026
; cpmsim records are already CP/M's 128 bytes. Read straight to the user's
; DMA address: staging through LY_BUF would overwrite the first record when
; the module loader builds a four-record header in that same buffer.
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

