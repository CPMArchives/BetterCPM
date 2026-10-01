# Engineering Specification 189: Native FDB Object and Extension Validation

## Result

CONFIG's native reader now validates the complete version-1 object and
extension envelope before the catalogue can be used. It claims each sector-ID
list and extension list in a bit-per-byte transient ownership map placed above
the loaded catalogue in the existing `4000h`–`7F7Fh` workspace. It rejects
catalogues that leave insufficient validation room, rejects object overlap,
requires distinct sector IDs, rejects nonzero unowned pool bytes, and requires
the file to end at the first record boundary after the highest owned object.
Arbitrary additional records are therefore invalid even when their CRC is
internally consistent.

Extension parsing requires a bounded `type,length,payload` sequence ending in
`0,0`. Type zero with a payload, required kind zero, duplicate kinds,
out-of-bounds payloads, and unterminated lists are rejected. Known semantic
extensions must use their required encodings:

- `81h` has one valid size code per physical sector and its maximum agrees with
  the descriptor's sector-size code; and
- `82h` has the sole version-1 cylinder-track payload value `1`.

Unknown optional extensions are skipped safely. An unknown required extension
does not invalidate the database: the reader marks only that descriptor
unsupported, and indexed status lookup exposes the result to the forthcoming
selection and binding layer. Descriptor support and encountered extension kinds
use 32-byte and 16-byte bitmaps respectively.

The ownership map and extension scratch data are transient CONFIG storage.
They were deliberately kept out of the executable image once their lifetimes
were measured. CONFIG is 11,174 bytes, leaving 4,442 bytes below its
15,616-byte ceiling; no resident memory is allocated and the 53 KiB TPA
contract is unchanged.

## Focused evidence

`tools/test_native_fdb_reader.py` executes the full native reader in the Z80
test machine. In addition to the framing and fixed-prefix cases, CRC-repaired
fixtures prove rejection of duplicate sector IDs, overlapping ID lists,
overlapping extension lists, nonzero unowned padding, extra records, malformed
terminators, duplicate TLVs, optional encodings of assigned semantic kinds,
bad mixed-sector lengths/codes/maxima, and bad cylinder-track payloads. Separate
fixtures prove that unknown optional and required kinds both preserve the
database while only the latter marks its descriptor unsupported.

A newly built z80pack release image passes
`tools/test_config_fdb_runtime.py`, demonstrating that the actual packaged
107-descriptor catalogue passes the complete native object/extension gate and
CONFIG reaches its menu under cpmsim.

## Remaining Step 4 boundary

The native reader now has enough structural information to decode a selected
supported descriptor. The next increment constructs the self-contained
normalized 64-byte BIOS binding, validates the descriptor's DPB/geometry and
topology relationships, and proves byte equivalence with the existing binding
for the admitted catalogue. CONFIG's menus remain on `DISK.FDF` until that
replacement is complete.
