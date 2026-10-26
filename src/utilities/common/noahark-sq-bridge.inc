; ARC method 4 uses SQ's exact Huffman/RLE tree and bitstream, without the
; standalone magic/checksum/name prefix. NASQ_RUN selects that header for one
; SQ_RUN call; the mode is context-owned and is cleared on success or error.
; SQ_INIT/SCAN, source stability checks, and output error handling are shared.
NASQ_MODE EQU SQ_RESERVED
NASQ_RUN:
        LD      A,(IX+NASQ_MODE)
        OR      A
        JR      NZ,NASQ_BAD_STATE
        INC     A
        LD      (IX+NASQ_MODE),A
        CALL    SQ_RUN
        PUSH    AF
        XOR     A
        LD      (IX+NASQ_MODE),A
        POP     AF
        RET
NASQ_BAD_STATE:
        LD      A,CS_STATE
        SCF
        RET
