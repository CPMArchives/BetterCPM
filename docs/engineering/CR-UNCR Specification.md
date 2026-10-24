# CR/UNCR Engineering Specification

This is an implemented-baseline specification dated 2026-10-23. The
[common engineering specification](Compression%20Utilities%20Common%20Specification.md)
defines the Z80 ABI, callbacks, statuses, file adapter and safe publication.
Offsets below are decimal. Allocation size is public; working fields are private
and must not be changed during processing. The `.inc` files remain the exact
assembly definitions. These documents do not add unimplemented command options.

## Sources and entries

[CR definitions](../../src/codec/cr.inc), [CR code](../../src/codec/cr.mac),
[UNCR definitions](../../src/codec/uncr.inc), [UNCR code](../../src/codec/uncr.mac).
Commands: [cr.mac](../../src/utilities/cr.mac), [uncr.mac](../../src/utilities/uncr.mac).
User pages: [CR](../user/CR.md), [UNCR](../user/UNCR.md).

`CR_INIT` validates READ/WRITE, allocation and the caller's NUL-terminated
`CR_NAME`, initializes state and enters READY without I/O. `CR_RUN` reads once,
emits the stream and enters DONE. REWIND is unused. There is no encoder GET/END.
A missing bounded name terminator is `CS_CONFIG`/80h; 32-bit input-counter overflow
is `CS_SPACE`/81h; exhausted internal hash probes are `CS_CORRUPT`/1.

`UNCR_INIT` requires READ and enters READY without I/O. `UNCR_HEAD` validates
the header and initializes the dictionary, entering DATA without output.
`UNCR_GET` yields a byte or verified C/CS_END; `UNCR_RUN` requires WRITE and
processes to DONE; `UNCR_END` discards/verifies to DONE. Common completion and
failure-latching rules apply. GET can suspend within a reversed phrase or RLE run.

## Supported format and wire layout

Only CRUNCH significant revision `20h` with checking selector zero is supported.
UNCR rejects `10h` and other revisions; it does not guess an algorithm from the
filename. Reference revision and spare bytes are retained, not used as extra
significant-version gates.

| Order | Encoding |
| --- | --- |
| Signature | `76 FE` |
| Name/metadata | Raw NUL-terminated field, at most 127 non-NUL bytes |
| Four fields | Reference, significant revision, checking selector, spare |
| Encoded body | Variable-width LZW codes, MSB-first within bytes |
| Trailer | Zero alignment padding from CR, then little-endian additive sum |

CR emits reference `24h`, significant `20h`, checking 0, spare 5. The checksum is
over original bytes after RLE expansion, including all input record padding.
Literal `90h` is escaped as `90 00`; nonzero RLE counts require history and a
count of at least 2. Historical escaped DLE output does not replace the saved
RLE history byte. No CRC selector is implemented.

Literal codes are 0..255; 256 ends the encoded stream; 257 resets the LZW
dictionary. Reserved codes 258/259 are skipped by UNCR. Compound codes start
at 260; widths progress from 9 to 12 bits with decoder insertion timing and
thresholds 511/1023/2047. Reset does not align bits or clear RLE/checksum state.
The valid undefined-next-code case uses the previous phrase and its first byte;
other undefined codes, cyclic/overlong prefix chains and invalid repeats fail.

## Encoder and historical decoder behavior

CR performs RLE followed by one-pass LZW. Its 5003-slot hash stores compound
prefix/suffix keys and their assigned codes. It emits resets at dictionary
capacity, before historical full-table reassignment is needed. It does not
implement historical compression-ratio resets or reassignment heuristics.
Output is compatible with the supported decoder format; it need not match a
historical encoder byte for byte or achieve its compression ratio.

UNCR supports width changes, resets and historical full-table reassignment.
It simulates the encoder's hash probes and reference-bit selection to reassign
an unreferenced entry. The 5003-entry physical-hash-to-code translation is part
of that compatibility requirement. A 4096-byte reversed phrase buffer avoids
recursive prefix expansion. Dictionary state, RLE state, checksum and pending
output all reside in the context.

UNCR corruption details 1..4 mean code, prefix chain, hash/probe and repeat
failures. A raw header beyond 127 bytes is `CS_SPACE`/5. Wrong significant/checking
bytes yield `CS_VARIANT`, with the rejected byte as detail. Physical EOF before
encoded stop/trailer is `CS_TRUNC`; a differing sum is `CS_CHECK`.

## Command-specific naming

`CR [drive:]file [destination-drive:]` replaces the middle extension slot with
Z. A missing extension or an already-middle-Z extension becomes `.ZZZ`; `.ZZZ`
input is refused even with a different destination drive. This implementation's
fallback is deliberate: it does not implement CrLZH's successive `AYC` -> `AYY`
style fallback using Z.

| Source | CR output |
| --- | --- |
| `REPORT.TXT` | `REPORT.TZT` |
| `SHORT.A` or `SHORT.AB` | `SHORT.AZ` |
| `CODE.AZC` | `CODE.ZZZ` |
| `NOEXT` | `NOEXT.ZZZ` |

CR embeds the original stem, a dot and all three extension slots, including
blanks. UNCR extracts up to three slots after the first dot, removes their
trailing blanks and ignores subsequent historical metadata. It validates the
result before creating output; high-bit or unsafe filename characters fail.
Metadata is not restored as file attributes or timestamps. Input need not have
Z in its extension. Checksums, successful final flush and both closes precede
rename; the shared file adapter prevents replacement and owns cleanup.

## Workspace layout

### CR — 25207 bytes

| Field/block | Decimal offset | Meaning |
| --- | ---: | --- |
| `CR_SUM` | 16 | physical input checksum, modulo 65536 |
| `CR_COUNT` | 18 | 32-bit physical input byte count |
| `CR_NEXT` | 22 | next encoder dictionary code |
| `CR_CURRENT` | 24 | Private working state. |
| `CR_HASH` | 26 | Private working state. |
| `CR_DISP` | 28 | Private working state. |
| `CR_PROBES` | 30 | Private working state. |
| `CR_OUT_NEXT` | 32 | decoder's next code, one insertion behind |
| `CR_LIMIT` | 34 | decoder width threshold: 511/1023/2047 |
| `CR_WIDTH` | 36 | Private working state. |
| `CR_OUTBYTE` | 37 | Private working state. |
| `CR_OUTBITS` | 38 | Private working state. |
| `CR_HAVE` | 39 | Private working state. |
| `CR_HAVE_OUT` | 40 | Private working state. |
| `CR_NAMLEN` | 41 | Private working state. |
| `CR_TOKEN` | 42 | Private working state. |
| `CR_RLE_STATE` | 43 | Private working state. |
| `CR_LAST` | 44 | Private working state. |
| `CR_RUNLEN` | 45 | Private working state. |
| `CR_PENDING` | 46 | Private working state. |
| `CR_RLE_FLAGS` | 47 | Private working state. |
| `CR_WIRE` | 48 | Private working state. |
| `CR_BITSLEFT` | 50 | Private working state. |
| `CR_NAME` | 64 | caller sets before INIT; preserved |
| `CR_KEYS` | 192 | 5003 prefix words, FFFFh = vacant |
| `CR_SUFFIX` | 10198 | 5003 suffix bytes |
| `CR_CODES` | 15201 | 5003 dictionary code words |

### UNCR — 26582 bytes

| Field/block | Decimal offset | Meaning |
| --- | ---: | --- |
| `UCN_REF` | 16 | Private working state. |
| `UCN_SIG` | 17 | Private working state. |
| `UCN_CHECK` | 18 | Private working state. |
| `UCN_SPARE` | 19 | Private working state. |
| `UCN_SUM` | 20 | Private working state. |
| `UCN_EXPECT` | 22 | Private working state. |
| `UCN_NEXT` | 24 | Private working state. |
| `UCN_PREV` | 26 | Private working state. |
| `UCN_CODE` | 28 | Private working state. |
| `UCN_USED` | 30 | bytes remaining in reversed phrase |
| `UCN_DEPTH` | 32 | Private working state. |
| `UCN_PROBES` | 34 | Private working state. |
| `UCN_HASH` | 36 | Private working state. |
| `UCN_DISP` | 38 | Private working state. |
| `UCN_COUNT` | 40 | 32-bit decoded-byte count |
| `UCN_WIDTH` | 44 | Private working state. |
| `UCN_BITS` | 45 | Private working state. |
| `UCN_BYTE` | 46 | Private working state. |
| `UCN_FIRST` | 47 | first byte of most recent phrase |
| `UCN_LAST` | 48 | historical RLE history byte |
| `UCN_REPEAT` | 49 | pending physical repeat bytes |
| `UCN_FLAGS` | 50 | Private working state. |
| `UCN_HDRLEN` | 51 | Private working state. |
| `UCN_INSERT` | 52 | candidate predecessor |
| `UCN_CHAR` | 54 | candidate suffix |
| `UCN_NEWFLAG` | 55 | reference bit for new entry |
| `UCN_TARGET` | 56 | dictionary index being inserted |
| `UCN_LIMIT` | 58 | next width transition (511/1023/2047) |
| `UCN_WALK` | 60 | Private working state. |
| `UCN_HEADER` | 64 | raw name/metadata, 127 bytes + NUL |
| `UCN_PREFIX` | 192 | 4096 LE words, flags in high bits |
| `UCN_SUFFIX` | 8384 | 4096 bytes |
| `UCN_XLAT` | 12480 | 5003 LE words, physical hash -> code |
| `UCN_PHRASE` | 22486 | 4096-byte reversed expansion buffer |

## Reproduction and evidence

```sh
python3 tools/test_cr.py
python3 tools/test_uncr.py
python3 tools/test_cr_com.py
python3 tools/test_uncr_com.py
python3 tools/test_cr_com_cpm.py
python3 tools/test_uncr_com_cpm.py
```

UNCR historical command tests require the compatibility-suite crunched-source
corpus (`--corpus` overrides its documented default); consult each test's help
and docstring. Fixtures are authenticated against their manifests. Library cases
include exact width/reset boundaries, reassignment, next-code handling, malformed
chains/repeats, truncation and checksum errors. An independent host model checks
CR's encoded output. Command tests exercise returned I/O failures, safe output,
metadata, drive/user defaults and collisions. Stock CP/M 2.2 round trips include
extent rollover and files beyond 64 KiB. These establish the supported `20h`
contract, not CRUNCH 1.x support or universal historical-file compatibility.


## Historical executable interoperability qualification

The [historical interoperability campaign](Compression%20Historical%20Interoperability.md)
now qualifies both directions under stock CP/M 2.2 using unmodified historical
executables and preserved input files. Its evidence distinguishes successful
record comparisons, intentional filename refusals, historical empty-file skips
and a confirmed CRUNCH 2.4 producer defect. It supplements the format's library
and native command regressions; it does not broaden supported format variants.

The final 1.0 feature freeze is baseline `00e6785` (merged in `569825d`), with
the standalone commands at version 1.0 Build 004 after the maintainer-directed
forgiving `/HELP` and `/VER` query amendment. The historical matrix has
been rerun against those exact final COM files, checked byte for byte against
fresh builds; see the [qualification index](Compression-1.0-Qualification.json)
for their SHA-256 identities. [Native ZSM4/LINK builds](Compression%20Native%20Build%20Qualification.md)
match those exact bytes. The [pinned emulator rerun](CPMSIM%20Reconstruction%20Qualification.md) also passes.
Remaining Utilities disk gates are tracked in the
[1.0 release checklist](../releases/1.0-ROADMAP.md#compression-utilities--10-feature-freeze-and-release-checklist).

See the [platform qualification record](Compression%20Utilities%20Platform%20Qualification.md):
the corrected cpmsim and Model 4 component matrix passes. The initial Model 4
data-loss report was traced to unpinned host geometry during test media setup;
independent FDF-sector readback now guards that path. Query and historical
results remain separately recorded.
