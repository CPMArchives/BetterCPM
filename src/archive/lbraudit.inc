; LBR_AUDIT: IX=open LBR context, IY=caller-owned LA_SIZE workspace.
; Call after AC_OPEN/LBR_OPEN. Reopens library state, not adapter handle.
; NC=structure and all advertised nonzero CRCs accepted; C/A=AS_* error.
; LA_CHECKED / LA_UNCHECKED count directory+active members, NOT all-pass status.
; CRC=0 is ambiguous (absent or mathematically zero), always counted unchecked.
; LBR_AUDIT_SELECTED: same contract, HL=predicate callback (0 means all).
; Callback receives IX/IY and selected metadata; A=0 excludes member CRC/data
; reads, nonzero includes them. Preserve IX/IY/alternate bank/SP. The directory
; and ALL active metadata/overlaps are always checked. LA_NOT_SELECTED is a
; separate 32-bit count, not a verified or failed checksum.
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
LA_FILTER       EQU 88
LA_NOT_SELECTED EQU 90
LA_BUFFER       EQU 96
LA_SIZE         EQU 224
