; ********************************************************************************
; *                    BetterCP/M Stage-One Bring-Up Diagnostic                  *
; *                                                                              *
; * Hardware-independent diagnostic used during stage-one bring-up. Initializes  *
; * the platform, verifies a raw disk sector signature, exercises console input, *
; * and reports success or failure through the HAL.                              *
; ********************************************************************************

; ================================================================================
; =                              Bring-Up Test                                   =
; =                                                                              =
; = Initializes the HAL, verifies the configured raw disk sector, and confirms   =
; = basic console input/output before stopping in the diagnostic loop.           =
; ================================================================================

CORE_START:                             ; run stage-one bring-up diagnostic
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

CCOMPARE:                               ; compare verification signature
        LD      A,(DE)
        CP      (HL)
        JR      NZ,CDISKERR
        INC     DE
        INC     HL
        DJNZ    CCOMPARE
        LD      HL,CDISKOK
        CALL    CORE_PRINTLN
        LD      HL,CKEYPROM
        CALL    CPRINT

CKEYWAIT:                               ; wait for console key
        CALL    HAL_CONST
        JR      Z,CKEYWAIT
        CALL    HAL_CONIN
        LD      C,A
        CALL    HAL_CONOUT
        LD      C,13
        CALL    HAL_CONOUT
        LD      C,10
        CALL    HAL_CONOUT
        JR      CSTOP

CDISKERR:                               ; report disk verification failure
        LD      HL,CDISKER
        CALL    CORE_PRINTLN

CSTOP:                                  ; halt in diagnostic loop
        JR      CSTOP

  ; Input: HL = zero-terminated string.  Clobbers AF, C, HL.

; -------------------------------------------------------------------------------
; Diagnostic Output
; -------------------------------------------------------------------------------

CORE_PRINTLN:                           ; print zero-terminated line
        CALL    CPRINT
        LD      C,13
        CALL    HAL_CONOUT
        LD      C,10
        JP      HAL_CONOUT

CPRINT:                                 ; print zero-terminated string
        LD      A,(HL)
        OR      A
        RET     Z
        LD      C,A
        PUSH    HL
        CALL    HAL_CONOUT
        POP     HL
        INC     HL
        JR      CPRINT

; -------------------------------------------------------------------------------
; Diagnostic Strings and Signature
; -------------------------------------------------------------------------------

CORE_TITLE:                             ; diagnostic title
        DB      'BetterCP/M',0

CORE_PLATFORM:                          ; platform-initialized message
        DB      'TRS-80 Model 4 platform initialized',0

CDISKOK:                                ; disk verification success message
        DB      'raw disk read verified',0

CDISKER:                                ; disk verification failure message
        DB      'raw disk read failed',0

CKEYPROM:                               ; key prompt
        DB      'key: ',0

CSIGNAT:                                ; disk verification signature
        DB      'BetterCP/M verify'
CSIGLEN EQU     $-CSIGNAT
