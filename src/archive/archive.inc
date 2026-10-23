; BetterCP/M archive read ABI 1. Definitions only; no emitted code/storage.
; IX=context, initialized config AS_ABI..AS_SIZE before LBR_OPEN.
; Public entries/callback preserve IX/IY, alternate banks and balanced SP.
; AF/BC/DE/HL caller-saved. NC=success, C/A=AS_* error/end result.
; Caller owns AS_CONTEXT_SIZE accessible bytes, not wrapping address 0000H.
; Config is immutable until CLOSE; contexts are independent, not reentrant.
;
; READ callback uses AS_OFFSET (absolute 32-bit byte offset), AS_BUFFER,
; AS_COUNT (16-bit requested bytes). Set AS_ACTUAL; NC for transfer,
; C/A=adapter detail on I/O failure. NC short transfer is AS_TRUNC.
; Callback must not change other context bytes or preserve scratch registers.
; Zero-length public reads perform no callback. AS_USER is opaque to library.
; This first reader requires a known physical AS_FILE_SIZE in bytes.
; No writer/CRC/content-test capability is advertised by this increment.
AS_ABI          EQU 0
AS_RESERVED     EQU 1
AS_READ         EQU 2
AS_USER         EQU 4
AS_FILE_SIZE    EQU 6
AS_SIZE         EQU 10
AS_PHASE        EQU 12
AS_STATUS       EQU 13
AS_DETAIL       EQU 14
AS_UNUSED_SEEN  EQU 15
AS_OFFSET       EQU 16
AS_BUFFER       EQU 20
AS_COUNT        EQU 22
AS_ACTUAL       EQU 24
AS_DIR_END      EQU 26
AS_NEXT         EQU 30
AS_LEFT         EQU 34
AS_POSITION     EQU 38
AS_ENTRY        EQU 42
AS_MEMBER       EQU 74
AS_CONTEXT_SIZE EQU 138
AS_ABI_VERSION  EQU 1
AS_CLOSED       EQU 0
AS_READY        EQU 1
AS_SELECTED     EQU 2
AS_FINISHED     EQU 3
AS_FAILED       EQU 4
AS_END          EQU 1
AS_FORMAT       EQU 2
AS_TRUNC        EQU 3
AS_IO           EQU 4
AS_CONFIG       EQU 5
AS_STATE        EQU 6
AS_RANGE        EQU 7

; Caller-owned copyable member metadata at IX+AS_MEMBER, valid until NEXT,
; OPEN or CLOSE. No pointer into a replaceable overlay is returned.
; LBR stored method=0 means opaque member, NOT an assertion of no inner codec.
; Name is canonical CP/M space-padded 8+3, not an ASCIIZ string.
; ID=directory entry byte offset; OFFSET/STORED/LENGTH are 32-bit bytes.
; Flags: bit0 exact logical length available (LUDEF pad count); bit1 CRC
; nonzero/present but NOT verified. Dates are four raw LUDEF words, zero
; means unavailable as defined by LUDEF; change date may inherit creation.
AM_NAME         EQU 0
AM_FLAGS        EQU 11
AM_ID           EQU 12
AM_OFFSET       EQU 16
AM_STORED       EQU 20
AM_LENGTH       EQU 24
AM_METHOD       EQU 28
AM_CRC          EQU 30
AM_DATES        EQU 32
AM_PAD          EQU 40
AM_SIZE         EQU 64
