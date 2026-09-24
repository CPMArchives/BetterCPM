; ********************************************************************************
; *                      z80pack CPMSIM Platform Binding                         *
; *                                                                              *
; * Binds the portable BetterCP/M BIOS to CPMSIM host console I/O and system     *
; * carriers. Resident addresses come from the shared layout; ANSI terminal      *
; * sequences replace platform video memory and cursor presentation.             *
; ********************************************************************************

; ================================================================================
; =                         CPMSIM Console Services                             =
; =                                                                              =
; = Provides host-backed console status, input, output, ANSI clear-screen, and   =
; = the platform initialization expected by the portable compatibility BIOS.     =
; ================================================================================

PL_INIT:                                ; initialize CPMSIM platform state
        XOR A
        LD (LY_HIST),A
        LD (LY_RSTA),A
        RET

PL_CONST:                               ; return host console status
        IN A,(0)
        AND 1
        RET

PL_CONIN:                               ; read host console character
        CALL PL_CONST
        JR Z,PL_CONIN
        IN A,(1)
        RET

PL_CONOT:                               ; write host console character
        LD A,C
        CP 28
        JR Z,Z_CLEAR
        OUT (1),A
        RET

; -------------------------------------------------------------------------------
; ANSI Terminal Output
; -------------------------------------------------------------------------------

Z_CLEAR:                                ; emit ANSI clear-screen sequence
        LD HL,Z_CLS

Z_STRING:                               ; emit zero-terminated ANSI string
        LD A,(HL)
        INC HL
        OR A
        RET Z
        OUT (1),A
        JR Z_STRING

PL_CURSOR:                              ; report cursor service unsupported
  ; No inverse-character service; the common utilities use plain output.
        XOR A
        RET

Z_CLS:  DB 27,'[2J',27,'[H',0           ; ANSI clear-screen string

; ================================================================================
; =                         System Carrier Loads                                =
; =                                                                              =
; = Loads the command reloader, control overlay, and selected RSX utility from   =
; = their CPMSIM disk carriers through the common resident disk interface.       =
; ================================================================================

PL_RELOAD:                              ; load command-environment reloader
        LD SP,0100H
        LD HL,LY_LOAD
        LD DE,60
        LD B,8
        CALL LY_DISK+15
        JR NZ,Z_HALT
        LD SP,LY_STKT
        JP LY_LOAD

PL_OVLOAD:                              ; load control overlay
        LD HL,LY_CFG
        LD DE,68
        LD B,8
        JP LY_DISK+15

PL_RSXLOAD:                             ; load selected RSX utility
        LD C,A
        LD HL,LY_CFG
        LD DE,60
        LD B,8
        CALL LY_DISK+15
        RET NZ
        LD A,C
        JP LY_CFG+0380H

; -------------------------------------------------------------------------------
; Carrier Load Failure
; -------------------------------------------------------------------------------

Z_HALT:                                 ; report load failure and halt
        LD A,'!'
        OUT (1),A
        HALT
        JR Z_HALT
