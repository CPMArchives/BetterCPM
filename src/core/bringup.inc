; BetterCP/M hardware-independent stage-one bring-up diagnostic

CORE_START:
        CALL    HAL_INIT
        LD      HL,CORE_TITLE
        CALL    CORE_PRINTLN
        LD      HL,CORE_PLATFORM
        CALL    CORE_PRINTLN

        LD      C,VERIFYSECTOR
        LD      HL,DISKBUFFER
        CALL    HAL_READ0
        JR      NZ,CDISKERR
        LD      HL,DISKBUFFER
        LD      DE,CSIGNAT
        LD      B,CSIGLEN
CCOMPARE:
        LD      A,(DE)
        CP      (HL)
        JR      NZ,CDISKERR
        INC     DE
        INC     HL
        DJNZ    CCOMPARE
        LD      HL,CDISKOK
        CALL    CORE_PRINTLN
        JR      CSTOP
CDISKERR:
        LD      HL,CDISKER
        CALL    CORE_PRINTLN
CSTOP:
        JR      CSTOP

; Input: HL = zero-terminated string.  Clobbers AF, C, HL.
CORE_PRINTLN:
        LD      A,(HL)
        OR      A
        JR      Z,CPRNL
        LD      C,A
        PUSH    HL
        CALL    HAL_CONOUT
        POP     HL
        INC     HL
        JR      CORE_PRINTLN
CPRNL:
        LD      C,13
        CALL    HAL_CONOUT
        LD      C,10
        JP      HAL_CONOUT

CORE_TITLE:
        DB      'BetterCP/M',0
CORE_PLATFORM:
        DB      'TRS-80 Model 4 platform initialized',0
CDISKOK:
        DB      'raw disk read verified',0
CDISKER:
        DB      'raw disk read failed',0
CSIGNAT:
        DB      'BetterCP/M verify'
CSIGLEN EQU     $-CSIGNAT
