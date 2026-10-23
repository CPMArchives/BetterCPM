; BetterCP/M CrLZH decoder ABI v1. Include codec.inc first. Definitions only.
; Z80, decimal offsets, little-endian words. Arbitrary context alignment.
ULZ_REF         EQU 16
ULZ_SIG         EQU 17
ULZ_CHECK       EQU 18
ULZ_SPARE       EQU 19
ULZ_SUM         EQU 20
ULZ_EXPECT      EQU 22
ULZ_COUNT       EQU 24              ; 32-bit decoded-byte count
ULZ_WRITEPOS    EQU 28
ULZ_COPYPOS     EQU 30
ULZ_COPYLEFT    EQU 32
ULZ_BYTE        EQU 33
ULZ_BITS        EQU 34
ULZ_HDRLEN      EQU 35
ULZ_POSBITS     EQU 36              ; 6 for 10h, 5 for 20h
ULZ_VALUE       EQU 37              ; pending output byte
ULZ_SYMBOL      EQU 38
ULZ_CUR         EQU 40
ULZ_I           EQU 42
ULZ_J           EQU 44
ULZ_K           EQU 46
ULZ_F           EQU 48
ULZ_LEFT        EQU 50
ULZ_RIGHT       EQU 52
ULZ_TEMP        EQU 54
ULZ_HOPS        EQU 56
ULZ_REBUILDS    EQU 58              ; diagnostic count, modulo 65536
ULZ_HEADER      EQU 64              ; raw filename/metadata, 127 bytes + NUL
ULZ_HEADER_SIZE EQU 128
ULZ_RING        EQU 192             ; 2048 bytes, initially spaces
ULZ_FREQ        EQU 2240            ; 630 words, including FFFFh sentinel
ULZ_SON         EQU 3500            ; 629 words; sibling at SON index + 1
ULZ_PARENT      EQU 4758            ; 944 words, including leaf locations
ULZ_CONTEXT_SIZE EQU 6646
ULZ_NCHAR       EQU 315
ULZ_T           EQU 629
ULZ_ROOT        EQU 628
ULD_TREE        EQU 1               ; CS_CORRUPT: invalid/bounded tree walk
ULD_SYMBOL      EQU 2               ; CS_CORRUPT: invalid symbol
ULD_HEADER      EQU 3               ; CS_SPACE: header exceeds 127 bytes
; UNLZH_INIT: validate common prefix/size, clear state -> READY; no I/O.
; UNLZH_HEAD: validate 76 FD header, sig 10h/20h, checking zero; init -> DATA.
; UNLZH_GET: NC/A=byte; C/CS_END only after stop symbol and verified checksum.
; UNLZH_RUN: WRITE decoded bytes to verified completion, NC/DONE.
; UNLZH_END: discard remaining decoded bytes, verify checksum, NC/DONE.
; DONE processing entries repeat without I/O. Failures latch until INIT.
; READ required, WRITE required only for RUN; REWIND unused, OPTIONS=0.
; Common ABI: preserve IX/IY/alternate banks/SP; ordinary registers scratch.
; Header exposes raw name/metadata; caller validates any destination name.
; Whole prefix/configuration and allocation follow codec.inc's contract.
; No OS calls, text/1Ah interpretation, recursion, stack switching or RLE.
; Overlapping copies and old-format distance wrapping use a 2048-byte ring.
; COUNT includes discarded GET/END bytes, not successfully committed writes.
; Tree rebuilt at frequency 8000h, with in-place reconstruction scratch.
; No input read-ahead beyond the current byte or the two-byte checksum.
