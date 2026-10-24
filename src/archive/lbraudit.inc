; LBR_AUDIT: IX=open LBR context, IY=caller-owned LA_SIZE workspace.
; Call after AC_OPEN/LBR_OPEN. Reopens library state, not adapter handle.
; NC=structure and all advertised nonzero CRCs accepted; C/A=AS_* error.
; LA_CHECKED / LA_UNCHECKED count directory+active members, NOT all-pass status.
; CRC=0 is ambiguous (absent or mathematically zero), always counted unchecked.
; Includes physical member padding in CRC. No inner codec is decoded.
; Duplicate/overlap audit uses bounded memory and quadratic directory reads.
; Workspace, context and stream are not reentrant or allowed to overlap.
; Preserves IX/IY/alternate banks/SP. Scratch registers otherwise destroyed.
LA_MEMBER       EQU 0
LA_EXPECTED     EQU 64
LA_CRC          EQU 66
LA_RECORDS      EQU 68
LA_CHECKED      EQU 70
LA_UNCHECKED    EQU 74
LA_FIRST        EQU 78
LA_SCAN         EQU 80
LA_START        EQU 84
LA_LENGTH       EQU 86
LA_BUFFER       EQU 96
LA_SIZE         EQU 224
