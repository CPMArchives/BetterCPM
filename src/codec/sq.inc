; BetterCP/M SQ ABI v1. Include codec.inc first; definitions only.
; Z80, little endian, decimal offsets. Context includes common 16 bytes.
SQ_SUM          EQU     16              ; current pass sum modulo 65536
SQ_EXPECT       EQU     18              ; first-pass original-byte checksum
SQ_TOTAL        EQU     20              ; scaled symbol-frequency total
SQ_ROOT         EQU     22              ; full node index (leaf=0..256)
SQ_NEXT         EQU     24              ; next internal index (257..513)
SQ_NAMLEN       EQU     26
SQ_RLE_STATE    EQU     27
SQ_LAST         EQU     28
SQ_RUNLEN       EQU     29
SQ_PENDING      EQU     30
SQ_RLE_FLAGS    EQU     31
SQ_COUNT        EQU     32              ; current pass original-byte count
SQ_EXPECT_COUNT EQU     36              ; first pass count, 32-bit LE
SQ_OUTBYTE      EQU     40
SQ_OUTMASK      EQU     41
SQ_PATHLEN      EQU     42              ; word, up to 256 bits
SQ_MIN_INDEX    EQU     44
SQ_MIN_WEIGHT   EQU     46
SQ_FIRST_INDEX  EQU     48
SQ_FIRST_WEIGHT EQU     50
SQ_RESERVED     EQU     52              ; twelve private bytes
SQ_TREE_NODES   EQU     60
SQ_NAME         EQU     64              ; caller fills before INIT; preserved
SQ_NAME_SIZE    EQU     128             ; NUL-terminated, at most 127 bytes
SQ_WEIGHTS      EQU     192             ; 513 unsigned 16-bit node weights
SQ_PARENTS      EQU     1218            ; 513 parent words, bit15=right edge
SQ_CHILDREN     EQU     2244            ; 256 pairs of full child indices
SQ_PATH         EQU     3268            ; reverse path: 256 one-byte bits
SQ_CONTEXT_SIZE EQU     3524

SQ_DLE          EQU     090H
SQ_SPEOF        EQU     256
SQF_PENDING     EQU     1
SQF_INPUT_END   EQU     2

SD_NAME         EQU     080H            ; CS_CONFIG: name lacks bounded NUL
SD_CHANGED      EQU     2               ; CS_CHECK: input changed after rewind
SD_COUNT        EQU     3               ; CS_SPACE: 32-bit byte count overflow

; Public entries, all using the common register/result/callback ABI:
; SQ_INIT: configure common prefix + SQ_NAME first. Checks READ/WRITE/REWIND,
;          size and bounded name; clears working storage, enters READY.
; SQ_SCAN: READY -> DATA. First input pass, RLE counts, tree construction,
;          then one REWIND. No output; no whole-file buffer or recursion.
; SQ_RUN:  DATA -> DONE. Emits standard SQ header and second-pass Huffman
;          stream. Repeated RUN in DONE returns NC without callbacks.
; Failures latch until INIT. No GET/END interface in this encoder revision.
; SQ_NAME and callback configuration must remain stable during operation.
; READ must already be at the stream start when SCAN is called. REWIND must
; restore that same start and reset caller-side buffering for pass two.
; READ physical EOF is expected in both passes; other errors map to CS_READ.
; RUN verifies second-pass count/sum before emitting SPEOF, and rejects any
; symbol absent in pass one. This is not a cryptographic change detector:
; callers MUST provide a stable input snapshot until RUN finishes.
; Frequency rescaling preserves every used symbol, limits weights to 16 bits,
; and may choose a different valid tree from historical SQ implementations.
; Parent paths support up to 256 bits; no 16-bit code-length restriction.
; Output includes no disk-record padding; caller flushes/closes/publishes.
