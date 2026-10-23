; BetterCP/M UNCR ABI v1. Include codec.inc first. Definitions only.
; Z80, decimal offsets, little-endian words. Context need not be aligned.
; CRUNCH significant revision 20h only; checking selector must be zero.
UCN_REF         EQU 16
UCN_SIG         EQU 17
UCN_CHECK       EQU 18
UCN_SPARE       EQU 19
UCN_SUM         EQU 20
UCN_EXPECT      EQU 22
UCN_NEXT        EQU 24
UCN_PREV        EQU 26
UCN_CODE        EQU 28
UCN_USED        EQU 30              ; bytes remaining in reversed phrase
UCN_DEPTH       EQU 32
UCN_PROBES      EQU 34
UCN_HASH        EQU 36
UCN_DISP        EQU 38
UCN_COUNT       EQU 40              ; 32-bit decoded-byte count
UCN_WIDTH       EQU 44
UCN_BITS        EQU 45
UCN_BYTE        EQU 46
UCN_FIRST       EQU 47              ; first byte of most recent phrase
UCN_LAST        EQU 48              ; historical RLE history byte
UCN_REPEAT      EQU 49              ; pending physical repeat bytes
UCN_FLAGS       EQU 50
UCN_HDRLEN      EQU 51
UCN_INSERT      EQU 52              ; candidate predecessor
UCN_CHAR        EQU 54              ; candidate suffix
UCN_NEWFLAG     EQU 55              ; reference bit for new entry
UCN_TARGET      EQU 56              ; dictionary index being inserted
UCN_LIMIT       EQU 58              ; next width transition (511/1023/2047)
UCN_WALK        EQU 60
UCN_HEADER      EQU 64              ; raw name/metadata, 127 bytes + NUL
UCN_HEADER_SIZE EQU 128
UCN_PREFIX      EQU 192             ; 4096 LE words, flags in high bits
UCN_SUFFIX      EQU 8384            ; 4096 bytes
UCN_XLAT        EQU 12480           ; 5003 LE words, physical hash -> code
UCN_PHRASE      EQU 22486           ; 4096-byte reversed expansion buffer
UCN_CONTEXT_SIZE EQU 26582
UCN_REFERENCED  EQU 02000H
UCNF_HISTORY    EQU 1
UCNF_ESCAPE     EQU 2
UCNF_PREV       EQU 4
UCNF_SPECIAL    EQU 8
; Algorithm diagnostics: CX_DETAIL with CS_CORRUPT (or CS_SPACE for HEADER).
UND_CODE        EQU 1
UND_CHAIN       EQU 2
UND_HASH        EQU 3
UND_REPEAT      EQU 4
UND_HEADER      EQU 5
; Public entries, IX=context; common codec ABI and failure latching apply.
; INIT validates prefix/size and clears state -> READY, no input/output.
; HEAD validates header, initializes dictionary -> DATA, no output.
; GET returns NC/A=byte, C/CS_END only after encoded EOF + verified checksum.
; RUN writes via callback; END discards/verifies, both NC/DONE at normal end.
; DONE entries are repeatable, failed entries return original status/detail.
; READ required; WRITE required only for RUN; REWIND unused. OPTIONS=0.
; Preserve IX/IY/alternate banks/SP. AF/BC/DE/HL scratch; no OS operations.
; All storage is caller-owned, code immutable. Contexts are independent.
; No recursion or alignment requirement; no read-ahead past checksum,
; CP/M padding handling, filename policy, flush or close. Physical EOF
; before verified completion is CS_TRUNC.
; Raw header may contain historical metadata after filename extension;
; caller validates/extracts a destination. Over 127 bytes -> CS_SPACE/detail5.
; COUNT counts decoded bytes, not successfully committed WRITE callbacks.
