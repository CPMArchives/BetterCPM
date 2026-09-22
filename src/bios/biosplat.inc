; ********************************************************************************
; *                    TRS-80 Model 4 BIOS Platform Binding                      *
; *                                                                              *
; * Binds the portable BetterCP/M compatibility BIOS to the Model 4 console,     *
; * scrolling, initialization, command-reload, overlay, and RSX-load services.   *
; ********************************************************************************

        INCLUDE hardware.inc
M4_EDITOR_KEYS EQU     1               ; enable Model 4 editor-key support
        INCLUDE m4cons.inc
        INCLUDE m4scroll.inc

PL_CONST       EQU     M4_STAT         ; console-status service
PL_CONIN       EQU     M4_IN           ; console-input service
PL_CONOT       EQU     M4_SCROLL_OUT   ; scrolling console-output service
PL_CURSOR      EQU     M4_CUROUT       ; cursor-presentation service

PL_INIT        EQU     M4_INIT         ; platform initialization service
        INCLUDE reload.inc
PL_RELOAD      EQU     M4_RELOAD       ; command-environment reload service
PL_OVLOAD      EQU     M4_OVLOAD       ; overlay-load service
PL_RSXLOAD     EQU     M4_RSLOAD       ; RSX-load service
