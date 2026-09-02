# Engineering Specification 92: ERA System Utility

## Compatibility baseline

BetterCP/M supplies ERA both as a resident `BASIC.CPX` command and as the
ordinary portable `ERA.COM` fallback. Both forms follow the CP/M 2.2 CCP
contract:

- `ERA filename.ext` deletes an exact file;
- `ERA` and an unmatched filespec report `NO FILE`;
- `*` expands through the remainder of its current 8.3 field and `?` matches
  one character;
- drive-qualified operands operate on that drive without changing the current
  drive/user;
- a filespec whose complete 8.3 name is wildcarded prompts exactly
  `ALL (Y/N)? ` before deletion; and
- confirmation must contain exactly one character, `Y` or `y`. Any other
  reply, an empty reply, or extra characters cancel silently.

The confirmation rule is based on the parsed eleven-byte FCB rather than the
literal source spelling. Consequently `*.*` and `????????.???` receive the
same protection. This detail, the single-character reply rule, and the
`NO FILE` behavior were established from the original CP/M 2.2 CCP source,
not inferred from the shorter user-manual synopsis.

Deletion itself uses BDOS Function 19. BDOS therefore owns the filesystem
semantics: every extent of each matching file is removed, its allocation is
released, and a read-only member of a wildcard set prevents the mutation from
being partially applied.

## Build and verification

`tools/build_era.py` creates `build/utilities/ERA.COM`. The source remains
assemblable and linkable with ZSM4 and LINK under native CP/M;
`tools/build_native_era.py` requires its native result to be byte-identical to
the cross build.

The normal boot image includes `ERA.COM`, so unloading `BASIC.CPX` leaves a
compatible transient fallback. `tools/test_era_compatibility.py` exercises the
resident command on disposable physical DMKs for exact deletion, multi-extent
deletion, drive qualification, unmatched names, and a blank operand. It also
unloads `BASIC.CPX` and repeats deletion through `ERA.COM`.

The BDOS conformance suite separately verifies wildcard deletion, allocation
release, multi-extent handling, and atomic read-only preflight. Native and
cross builds of `ERA.COM` are required to be byte-identical.

`tools/add_cpm_file_to_dmk.py` supports the complementary development case:
adding one file to an existing MM Extended 790K image without rebuilding or
discarding its current filesystem state. It decodes and verifies the DMK,
finds free directory entries and allocation blocks, rebuilds valid track CRCs,
and can retain the original image as a backup. It was used to add `ERA.COM` to
the manually exercised conformance disk while preserving its retained
`BTBOOT.DAT` evidence.
