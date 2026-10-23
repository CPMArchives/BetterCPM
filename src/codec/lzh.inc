; BetterCP/M CrLZH encoder ABI v1. Include codec.inc first; definitions only.
; Z80, decimal offsets, little-endian words, arbitrary context alignment.
LZH_LEN         EQU 16              ; live lookahead bytes, 0..60
LZH_EOF         EQU 17              ; physical EOF observed
LZH_BEST        EQU 18
LZH_TAKE        EQU 19
LZH_SUM         EQU 20              ; physical input checksum modulo 65536
LZH_DISTANCE    EQU 22              ; candidate distance, 1..2048
LZH_COUNT       EQU 24              ; 32-bit physical input byte count
LZH_WRITEPOS    EQU 28
LZH_SCANPOS     EQU 30
LZH_POSLOW      EQU 32              ; low five position bits
LZH_BYTE        EQU 33              ; packed output accumulator
LZH_BITS        EQU 34              ; accumulated bits, 0..7
LZH_NAMLEN      EQU 35
LZH_PATHLEN     EQU 36
LZH_SYMBOL      EQU 38
LZH_CUR         EQU 40
LZH_I           EQU 42
LZH_J           EQU 44
LZH_K           EQU 46
LZH_F           EQU 48
LZH_LEFT        EQU 50
LZH_RIGHT       EQU 52
LZH_TEMP        EQU 54
LZH_HOPS        EQU 56
LZH_REBUILDS    EQU 58              ; diagnostic count modulo 65536
LZH_BESTDIST    EQU 60
LZH_LASTDIST    EQU 62              ; monotonic chain distance bound
LZH_NAME        EQU 64              ; caller sets before INIT; preserved
LZH_NAME_SIZE   EQU 128             ; raw name/metadata, 127 bytes + NUL
LZH_RING        EQU 192             ; 2048 bytes, initially spaces
LZH_FREQ        EQU 2240            ; 630 words, including FFFFh sentinel
LZH_SON         EQU 3500            ; 629 words
LZH_PARENT      EQU 4758            ; 944 words
LZH_LOOK        EQU 6646            ; 60 bytes of lookahead
LZH_PATH        EQU 6706            ; 629 bytes, bounded reversed tree path
LZH_HEADS       EQU 7335            ; 256 first-byte chain heads, words
LZH_NEXT        EQU 7847            ; 2048 ring-node links, words
LZH_CONTEXT_SIZE EQU 11943
LZH_NCHAR       EQU 315
LZH_T           EQU 629
LZH_ROOT        EQU 628
LHD_NAME        EQU 080H            ; CS_CONFIG: name has no bounded NUL
LHD_COUNT       EQU 081H            ; CS_SPACE: input counter overflow
LHD_TREE        EQU 1               ; CS_CORRUPT: internal tree/path bound
; LZH_INIT: validate ABI/size/READ/WRITE/name; reset -> READY, no callbacks.
; LZH_RUN: READY -> DATA -> DONE; one input pass, NC on verified completion.
; Repeated RUN in DONE returns NC without callbacks. Failures latch until INIT.
; Emits 76 FD, raw NAME + NUL, reference/significant 20h, checking 0, spare 5,
; adaptive-Huffman symbols, encoded stop 256, zero padding, LE additive sum.
; Greedy longest match, nearest-distance tie break, matches 3..60, ring 2048.
; First-byte chains use monotone distances to reject overwritten links; no
; hash collisions or unbounded probe loops. Worst case searches 2048 nodes.
; Overlap and seeded spaces supported. Emits 20h only; UNLZH reads 10h/20h.
; NAME/prefix configuration stable through RUN. READ EOF is normal; REWIND
; unused, OPTIONS=0. No RLE, record padding, flush/close, OS calls, allocation,
; recursion, stack switching, alternate-register instructions or IY use.
; All mutable storage is in context. Code/tables immutable. Primary registers
; scratch; IX/IY/alternate banks/SP preserved, including across callbacks.
; Output is compatible, not required byte-identical to historical encoders.
; Include codec.inc/mac and lzh.inc/mac; emit CODEC_CODE + LZH_CODE once.
; z80pack z80asm -e32; native ZSM4 assembly not yet qualified.
