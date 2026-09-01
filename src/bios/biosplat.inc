; Build fixture for the independently assembled BIOS scaffold.
;
; A platform integration supplies these three physical console operations.
; The fixture reports no input, EOF for a forced input call, and discards
; output; it exists to make the compatibility BIOS reproducibly buildable
; before a resident TRS-80 platform module is linked.

PL_CONST:
        XOR     A
        RET
PL_CONIN:
        LD      A,01AH
        RET
PL_CONOT:
        RET
