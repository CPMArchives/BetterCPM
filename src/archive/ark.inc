; ARC 5.x-family container reader on archive.inc ABI 1 (138-byte context).
; New original implementation; external ARC/Deark code is not linked/copied.
; ARK_OPEN/NEXT/RAW/CLOSE follow LBR register/config/error conventions.
; RAW returns stored bytes, not decoded bytes. NEXT abandons unread stored data.
; ARK_TEST_STORED rewinds/tests methods 1/2, including a present CRC of zero.
; Methods 3..9 can be enumerated/read raw but are not decoded or tested here.
; Unknown methods/extended headers/encryption/prefix resync are unsupported.
; Names normalize to exact CP/M 8+3; malformed/unsafe names reject the member.
; AM_LENGTH is declared decoded length; AS_LEFT is remaining STORED bytes.
; AM_FLAGS bit1 means CRC present even when zero, not CRC verified.
; AM_DATES starts with raw DOS date,time words; byte 41 tags their encoding.
; Date conversion, duplicate-name audit, writes and CLI integration are separate.
; On archive EOF, AS_DIR_END = byte immediately after the 1Ah/00h marker.
; AS_UNUSED_SEEN: 0 exact EOF, 1 all trailing bytes 00h/1Ah padding,
; 2 opaque trailing bytes (unvalidated; never silently claim clean coverage).
; Structural/CRC/I/O/unsupported errors are sticky until OPEN/CLOSE.
; Config-error calls don't write context. RAW zero-length does no callback.
ARK_DATE_KIND EQU 41
ARK_DOS_DATE EQU 1
