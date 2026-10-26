; ARC writer API additions. Include archive.inc and ark.inc first.
; ARK_BUILD_HEADER consumes the caller-owned AS_MEMBER record and writes a
; canonical ARC 2.x/5.x 29-byte member header to AS_ENTRY. It emits only the
; new stored (2), squeezed (4), or dynamic-LZW (8) representations. The caller
; owns payload encoding, stream I/O, archive terminator, verification and
; publication. AF/BC/DE/HL scratch; IX/IY/SP/alternate banks preserved. The
; macro owns five bytes of static validation scratch and is not reentrant.
; Input AM_NAME is canonical space-padded 8+3; AM_STORED, AM_LENGTH, AM_CRC,
; AM_DATES and AM_METHOD are authoritative. Zero dates mean unavailable.
; On success A=29, carry clear. Invalid names return AS_FORMAT; methods outside
; 2/4/8 return AS_UNSUPPORTED. Configuration-error calls do not alter context.
ARW_ENTRY_SIZE   EQU 29
ARW_HEADER_SIZE  EQU 29
