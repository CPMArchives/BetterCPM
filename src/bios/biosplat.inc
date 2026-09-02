; TRS-80 Model 4 binding for the compatibility BIOS console entries.

        INCLUDE hardware.inc
M4_EDITOR_KEYS EQU     1
        INCLUDE m4cons.inc
        INCLUDE m4scroll.inc

PL_CONST       EQU     M4_STAT
PL_CONIN       EQU     M4_IN
PL_CONOT       EQU     M4_SCROLL_OUT
PL_CURSOR      EQU     M4_CUROUT

M4_READ_ONLY   EQU     0
M4_MULTI_DRIVE EQU     1
        INCLUDE m4disk.inc

PL_READ        EQU     M4_READ
PL_WRITE       EQU     M4_WRITE
