; BetterCP/M USQ ABI v1. Include codec.inc first. Definitions only.
; Context offsets are decimal; words are little endian.
UQ_EXPECT       EQU     16
UQ_SUM          EQU     18
UQ_NODES        EQU     20
UQ_BITBYTE      EQU     22
UQ_BITSLEFT     EQU     23
UQ_LAST         EQU     24
UQ_REPEAT       EQU     25
UQ_FLAGS        EQU     26
UQ_NAMLEN       EQU     27
UQ_COUNT        EQU     28              ; 32-bit original-byte count, LE
UQ_NAME         EQU     32              ; 127 bytes plus NUL; bytes preserved
UQ_NAME_SIZE    EQU     128
UQ_TREE         EQU     160             ; 256 pairs of signed child words
UQ_MARKS        EQU     1184            ; 256 validation marks: 0/1/2
UQ_CONTEXT_SIZE EQU     1440

UQF_HAVE_LAST   EQU     01H
UQF_SAW_END     EQU     02H
UQF_TREE_END    EQU     04H             ; EOF leaf found during validation
UQ_DLE          EQU     090H
UQ_SPEOF        EQU     256
UQ_SIGNATURE    EQU     0FF76H

; CS_CORRUPT diagnostics (CX_DETAIL).
UD_NODES        EQU     1               ; count outside 0..256
UD_CHILD        EQU     2               ; child outside nodes or -257..-1
UD_TREE         EQU     3               ; cycle/shared/unreachable/no EOF
UD_REPEAT       EQU     4               ; count 1, missing history, EOF count
UD_NAME         EQU     5               ; name exceeds 127 bytes

; Public entries (IX = initialized caller configuration):
; USQ_INIT: validates configuration/allocation, clears USQ state -> READY.
; USQ_HEAD: READY -> DATA; bounded name and fully validated decoding tree.
; USQ_GET:  DATA -> NC/A=original byte, or C/CS_END after checksum matches.
; USQ_RUN:  DATA -> WRITE callbacks until verified end, then NC/DONE.
; USQ_END:  DATA -> discard remaining output until verified end, NC/DONE.
; GET/RUN/END are repeatable in DONE without further callbacks. Failed
; contexts retain status/detail until INIT. HEAD/INIT never write output.
; RUN checks WRITE before consuming data. GET/END need no WRITE callback.
; Preserves IX/IY/alternate registers/SP; AF/BC/DE/HL may change.
; No recursion, OS calls, read-ahead beyond current compressed byte, flush,
; close, newline conversion, parity stripping or CP/M EOF interpretation.
; UQ_COUNT counts decoded bytes, not bytes committed by a WRITE callback.
