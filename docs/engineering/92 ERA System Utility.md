# Engineering Specification 92: ERA System Utility

## Decision

BetterCP/M supplies `ERA.COM` as an ordinary portable system utility. It uses
the public default FCB and BDOS Delete File interface, expands CP/M `*`
wildcards through the current 8.3 field, preserves `?`, and asks for explicit
confirmation before deleting `*.*`.

The initial resident CCP has only 22 bytes free before the fixed `ED00h`
physical-sector buffer. A safe wildcard-capable resident ERA would require a
deliberate memory-map change. The transient utility therefore provides the
needed command without concealing that architectural decision or crowding the
resident boundary.

## Build and verification

`tools/build_era.py` creates `build/utilities/ERA.COM`. The source remains
assemblable and linkable with ZSM4 and LINK under native CP/M;
`tools/build_native_era.py` requires its native result to be byte-identical to
the cross build.

The generated conformance disk includes ERA.COM. A physical `trs80gp` test
created `BTBOOT.DAT`, ran `ERA BTBOOT.DAT`, and then ran resident `DIR` on the
same writable image. The directory contained `HELLO.COM` and `ERA.COM` but no
`BTBOOT.DAT`, proving deletion through BetterCP/M's public filesystem path.

`tools/add_cpm_file_to_dmk.py` supports the complementary development case:
adding one file to an existing MM Extended 790K image without rebuilding or
discarding its current filesystem state. It decodes and verifies the DMK,
finds free directory entries and allocation blocks, rebuilds valid track CRCs,
and can retain the original image as a backup. It was used to add `ERA.COM` to
the manually exercised conformance disk while preserving its retained
`BTBOOT.DAT` evidence.
