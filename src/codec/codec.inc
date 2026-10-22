; BetterCP/M codec ABI version 1 -- definitions only, no storage or code.
; Z80; all words are little endian; all offsets and sizes are decimal.
; Assemble with 32 significant symbol characters (z80pack z80asm: -e32).
;
; Public codec entries and callbacks receive IX = context. Preserve IX, IY,
; AF', BC', DE', HL' and stack balance. AF/BC/DE/HL are caller-saved.
; No alternate-register instructions are used by the codec library.
; NC = success; C = status in A. GET alone returns C/CS_END at normal end.
; RUN/END return NC at normal end. See codec.mac for helper contracts.
;
; Caller initializes configuration fields, including CX_SIZE, before INIT.
; Caller guarantees an accessible, non-wrapping 16-byte prefix even when
; CX_SIZE is invalid. A declared size cannot prove physical RAM ownership.
; For a valid allocation, its entire CX_SIZE-byte range must be accessible
; and must not wrap the 16-bit address space.
; Codec owns PHASE/STATUS/DETAIL; all other prefix fields are configuration.
; Configuration remains unchanged during an operation. Contexts are not
; reentrant; distinct contexts may share the same emitted code.

CX_ABI          EQU     0
CX_OPTIONS      EQU     1
CX_PHASE        EQU     2
CX_STATUS       EQU     3
CX_DETAIL       EQU     4
CX_RESERVED     EQU     5
CX_READ         EQU     6
CX_WRITE        EQU     8
CX_REWIND       EQU     10
CX_USER         EQU     12
CX_SIZE         EQU     14
CX_PREFIX_SIZE  EQU     16
CX_ABI_VERSION  EQU     1

CP_RESET        EQU     0
CP_READY        EQU     1
CP_DATA         EQU     2
CP_DONE         EQU     3
CP_FAILED       EQU     4

CS_OK           EQU     00H
CS_END          EQU     01H
CS_FORMAT       EQU     02H
CS_VARIANT      EQU     03H
CS_TRUNC        EQU     04H
CS_CORRUPT      EQU     05H
CS_CHECK        EQU     06H
CS_READ         EQU     07H
CS_WRITE        EQU     08H
CS_NOREWIND     EQU     09H
CS_REWIND       EQU     0AH
CS_SPACE        EQU     0BH
CS_STATE        EQU     0CH
CS_CONFIG       EQU     0DH

; Configuration diagnostics (CX_DETAIL when status is CS_CONFIG).
CD_ABI          EQU     1
CD_OPTIONS      EQU     2
CD_RESERVED     EQU     3
CD_READ         EQU     4
CD_WRITE        EQU     5

; Callback ABI:
; READ:   NC/A=byte; C/A=0 physical EOF; C/A=1..255 input error.
; WRITE:  A=byte on entry; NC accepted; C/A=0..255 output error.
; REWIND: NC restored stream start (including buffers); C/A=0..255 error.
; IX is passed unchanged. CX_USER is an opaque caller-owned pointer.
; Callback failures map to CS_READ/WRITE/REWIND with reason in CX_DETAIL.
; Physical EOF is interpreted by the algorithm, not by common dispatch.
