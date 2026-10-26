; ARC writer API additions. Include archive.inc and ark.inc first.
; ARK_BUILD_HEADER consumes the caller-owned AS_MEMBER record and writes a
; canonical ARC 2.x/5.x 29-byte member header to AS_ENTRY. It emits only the
; new stored (2), squeezed (4), or dynamic-LZW (8) representations. The caller
; owns payload encoding, verification and publication. ARK_WRITE_MEMBER then
; streams that prepared member header and its exact stored byte count through
; the context READ callback and an output callback stored in the unused tail
; of the caller-owned member record. ARK_WRITE_END emits ARC's 1Ah/00h marker.
; The caller owns physical-record padding, archive verification and publication.
; AF/BC/DE/HL scratch; IX/IY/SP/alternate banks preserved. The macro owns
; static scratch and is not reentrant.
; Input AM_NAME is canonical space-padded 8+3; AM_STORED, AM_LENGTH, AM_CRC,
; AM_DATES and AM_METHOD are authoritative. Zero dates mean unavailable.
; On success A=29, carry clear. Invalid names return AS_FORMAT; methods outside
; 2/4/8 return AS_UNSUPPORTED. Configuration-error calls do not alter context.
;
; ARK_WRITE_MEMBER input: AS_READ is a callback reading bytes at AS_OFFSET into
; AS_BUFFER, AS_COUNT, returning exact AS_ACTUAL; AM_WRITE_CB is an address of
; a callback with the same transfer convention for output. AM_OFFSET is the
; first payload byte and AM_OUTPUT_OFFSET the first output byte. AM_REMAIN and
; AM_SOURCE_OFFSET are initialized internally from AM_STORED and AM_OFFSET.
; AS_BUFFER must point to 128 writable bytes.
; It writes the 29-byte header then exactly AM_STORED payload bytes, no pad.
; Source short reads return AS_TRUNC; output short writes/errors return
; AS_OUTPUT (detail in A on callback error is not retained). Offsets are
; checked for 32-bit overflow. ARK_WRITE_END appends 1Ah/00h at output offset.
; ARK_COPY_MEMBER copies the current selected member's original header and
; stored payload unchanged via ARK_RAW, preserving opaque but bounded methods.
; Writer entries advance AM_OUTPUT_OFFSET only after successful transfers.
ARW_ENTRY_SIZE   EQU 29
ARW_HEADER_SIZE  EQU 29
AM_WRITE_CB      EQU 36
AM_SOURCE_OFFSET EQU 38
AM_OUTPUT_OFFSET EQU 42
AM_REMAIN        EQU 46
