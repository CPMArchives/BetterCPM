; TRS-80 Model 4 binding for the compatibility BIOS console entries.

        INCLUDE hardware.inc
M4_EDITOR_KEYS EQU     1
        INCLUDE m4cons.inc
        INCLUDE m4scroll.inc

PL_CONST       EQU     M4_STAT
PL_CONIN       EQU     M4_IN
PL_CONOT       EQU     M4_SCROLL_OUT
PL_CURSOR      EQU     M4_CUROUT

PL_INIT        EQU     M4_INIT
        INCLUDE reload.inc
PL_RELOAD      EQU     M4_RELOAD
PL_OVLOAD      EQU     M4_OVLOAD
PL_RSXLOAD     EQU     M4_RSLOAD
