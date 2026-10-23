; BetterCP/M CR ABI v1. Include codec.inc first; definitions only.
; Z80, decimal offsets, little-endian words, arbitrary context alignment.
CR_SUM          EQU 16              ; physical input checksum, modulo 65536
CR_COUNT        EQU 18              ; 32-bit physical input byte count
CR_NEXT         EQU 22              ; next encoder dictionary code
CR_CURRENT      EQU 24
CR_HASH         EQU 26
CR_DISP         EQU 28
CR_PROBES       EQU 30
CR_OUT_NEXT     EQU 32              ; decoder's next code, one insertion behind
CR_LIMIT        EQU 34              ; decoder width threshold: 511/1023/2047
CR_WIDTH        EQU 36
CR_OUTBYTE      EQU 37
CR_OUTBITS      EQU 38
CR_HAVE         EQU 39
CR_HAVE_OUT     EQU 40
CR_NAMLEN       EQU 41
CR_TOKEN        EQU 42
CR_RLE_STATE    EQU 43
CR_LAST         EQU 44
CR_RUNLEN       EQU 45
CR_PENDING      EQU 46
CR_RLE_FLAGS    EQU 47
CR_WIRE         EQU 48
CR_BITSLEFT     EQU 50
CR_NAME         EQU 64              ; caller sets before INIT; preserved
CR_NAME_SIZE    EQU 128             ; raw filename/metadata, 127 bytes + NUL
CR_KEYS         EQU 192             ; 5003 prefix words, FFFFh = vacant
CR_SUFFIX       EQU 10198           ; 5003 suffix bytes
CR_CODES        EQU 15201           ; 5003 dictionary code words
CR_CONTEXT_SIZE EQU 25207
CR_DLE          EQU 090H
CR_SPEOF        EQU 256
CRF_PENDING     EQU 1
CRF_INPUT_END   EQU 2
CRD_NAME        EQU 080H            ; CS_CONFIG: no bounded name terminator
CRD_COUNT       EQU 081H            ; CS_SPACE: input byte counter overflow
CRD_HASH        EQU 1               ; CS_CORRUPT: internal probe exhaustion
; CR_INIT: validates ABI/size/READ/WRITE/name, clears working state -> READY.
; CR_RUN: READY -> DATA -> DONE, one input pass; writes CRUNCH 20h stream.
; Repeated RUN in DONE returns NC without callbacks. Failures latch until INIT.
; CR_NAME and prefix configuration must remain stable through RUN.
; READ physical EOF is normal; REWIND unused. No GET/END entries in encoder.
; Emits 76 FE, raw CR_NAME + NUL, reference 24h/significant 20h/checking 0/
; spare 5, MSB-first codes, encoded EOF, zero bit padding, LE additive sum.
; RLE precedes LZW. Dictionary resets at capacity, without bit realignment;
; no reassignment or compression-ratio reset heuristics in this encoder.
; Hash slots are private, containing only compound phrases. This is valid
; because RESET is emitted before decoder full-table reassignment can start.
; Output need not match a historical encoder byte for byte. No disk padding,
; flush, close, filename policy, OS calls, allocation or whole-input buffer.
; Common register/callback ABI: IX/IY/alternate banks/SP preserved; ordinary
; registers scratch. All mutable state in context, code immutable, no recursion.
