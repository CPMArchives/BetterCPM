
; ******************************************************************************
; * BetterCP/M 104/105 Clock Frontend                                          *
; ******************************************************************************
; * Optional 104/105 clock frontend. Resolves the native TIME service for each *
; * request. No provider address is retained; profiles are explicit.           *
; ******************************************************************************


RSXBASE         EQU     08000H
BDOS            EQU     00005H

        CSEG
        .PHASE  RSXBASE

; ==============================================================================
; = 104/105 Frontend Dispatch                                                  =
; ==============================================================================
; = Maps historical clock calls onto TIME ABI 1.0 and chains other requests.   =
; = Failed GET never publishes the private native request buffer.              =
; ==============================================================================

C4_NEXT:        DW      BDOS            ; next RSX descriptor pointer
C4_ENTRY:       DW      C4_DISPATCH     ; RSX entry pointer
C4_SVCOUNT:     DB      0               ; callable-service count
C4_RESERVED:    DB      0               ; reserved service metadata
C4_SVOFF:       DW      0               ; resident-service entry offset

C4_DISPATCH:                            ; dispatch historical clock request
        LD      A,C
        CP      105
        JR      Z,C4_GET
        CP      104
        JR      Z,C4_SET

C4_CHAIN:                               ; chain unhandled request
        LD      HL,(C4_NEXT)
        JP      (HL)

; -------------------------------------------------------------------------------
; Historical GET and SET
; -------------------------------------------------------------------------------

C4_GET:                                 ; get historical clock record
        PUSH    DE                      ; public buffer address must survive
        XOR     A
        CALL    C4_CALL
        OR      A
        JR      NZ,C4_FAILED
        POP     DE
        PUSH    DE
        LD      HL,C4_REQUEST+4
        IF      CP3PROFILE
        LD      BC,4
        ELSE
        LD      BC,5
        ENDIF
        LDIR                            ; publish only a validated native sample
        POP     DE
        IF      CP3PROFILE
        LD      A,(C4_REQUEST+8)      ; four-byte GET returns BCD seconds in A
        LD      HL,0
        RET
        ELSE
        JR      C4_SUCCESS
        ENDIF

C4_SET:                                 ; set historical clock record
        PUSH    DE                      ; preserve caller address across copying
        LD      HL,0
        ADD     HL,DE
        LD      DE,C4_REQUEST+4
        IF      CP3PROFILE
        LD      BC,4
        ELSE
        LD      BC,5
        ENDIF
        LDIR
        IF      CP3PROFILE
        XOR     A                      ; four-byte SET resets seconds to zero
        LD      (C4_REQUEST+8),A
        ENDIF
        LD      A,1
        CALL    C4_CALL
        OR      A
        JR      NZ,C4_FAILED
        POP     DE

C4_SUCCESS:                             ; return historical success
        XOR     A
        LD      HL,0
        RET

C4_FAILED:                              ; map every claimed failure to FEh
        POP     DE
        LD      A,0FEH
        LD      HL,000FEH
        RET

; -------------------------------------------------------------------------------
; Per-Call Native TIME Resolution
; -------------------------------------------------------------------------------

C4_CALL:                                ; resolve and invoke native TIME service
        LD      (C4_REQUEST+2),A
        LD      HL,C4_LKRET
        PUSH    HL
        LD      C,182
        LD      DE,C4_LKREQ
        LD      HL,(C4_NEXT)
        JP      (HL)                    ; bypass this frontend during discovery

C4_LKRET:                               ; validate resident-service lookup
        OR      A
        RET     NZ
        LD      A,H
        OR      L
        JR      Z,C4_NO_SERVICE
        LD      BC,C4_TIME_RETURN
        PUSH    BC
        LD      DE,C4_REQUEST
        JP      (HL)                    ; consume address only for this call

C4_TIME_RETURN:                         ; return native TIME status
        RET

C4_NO_SERVICE:                          ; report unavailable native service
        LD      A,1
        RET

; -------------------------------------------------------------------------------
; Private Request Storage
; -------------------------------------------------------------------------------

C4_LKREQ:       DB      1,20,0,0,'TIME',1,0,0,0 ; Function-182 lookup request
                DB      0,0,0,0,0,0,0,0         ; resolver output fields
C4_REQUEST:     DB      1,10,0,0,0,0,0,0,0,0    ; native TIME request

        .DEPHASE
        END
