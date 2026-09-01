; TRS-80 Model 4 binding for the compatibility BIOS console entries.

        INCLUDE hardware.inc
        INCLUDE m4cons.inc

PL_CONST       EQU     M4_STAT
PL_CONIN       EQU     M4_IN
PL_CONOT       EQU     M4_OUT

        INCLUDE m4disk.inc

PL_READ        EQU     M4_READ
