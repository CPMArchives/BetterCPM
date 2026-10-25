# NOAH ARK LIST/TEST/EXTRACT integration

Status: NOAH 1.0 revision 14 development increment, 2026-10-26. This follows
[#510's reader foundation](NOAH%20ARK%20Reader%20Foundation.md) and implements
production dispatch, stored-member testing and safe extraction. The
[behavioral specification](NOAH%20Specification.md) remains normative. Native
qualification and the source/evidence receipt are recorded in
[NOAH-ARK-CLI.json](NOAH-ARK-CLI.json).

## Command boundary

Existing files are recognized by content, irrespective of extension. A leading
ARC marker selects the checked ARK reader; other inputs follow the existing LBR
validator. Unknown ARC methods, bad headers and truncated containers fail rather
than falling back to LBR or treating compressed bytes as extracted contents.
Shared filespecs, frozen archive ordering, member filters, destination DU,
protection/overwrite decisions, cancellation and reporting remain in force.

| Operation | Stored methods 1/2 | Recognized compressed methods 3–9 |
| --- | --- | --- |
| LIST | Names and exact declared lengths; no content/CRC test | Names and declared lengths, explicit unsupported-method warning |
| TEST | Whole framing/name audit; selected payload CRCs, including CRC zero | Whole framing/name audit; selected members counted unchecked and identified as unsupported |
| EXTRACT | Audit before output, CRC check, stage/close/reopen/compare, authorized publication | Explicit bounded skip; continue to later safely framed members; warning/partial outcome |

All names are normalized to the existing safe 8+3 metadata form. TEST/EXTRACT
compare each name against all preceding headers, including members excluded by
the filter. A duplicate prevents any extraction output. Sequential header/payload
boundaries are validated by the reader; no damaged-header resynchronization is
attempted. The duplicate scan uses constant workspace and quadratic header reads,
matching the bounded-memory approach already used for LBR audit.

ARK has no directory checksum: coverage counts selected members, without the LBR
directory-region increment. Unsupported selected methods contribute to the
existing unchecked count; their method-specific warning explains why. A failed
member is never counted verified. LIST continues to state that contents were not
tested. Filtered-out members contribute only to the not-selected counter.

Extraction uses the existing NO_AUTHORIZE/NO_PUBLISH machinery, temporary/backup
naming, input exclusions, recovery diagnostics and safe Retry/Skip boundaries.
The reader is rewound only while still selected; sticky read/CRC failures cannot
be cleared as an output retry. Declared member length governs bytes, including
embedded zero and 1Ah; the last CP/M output record receives existing 1Ah padding.
`/X /EXPAND` retains its LBR meaning: it does not recursively decode an inner CP/M
compressed stream inside an ARK stored member.

Raw DOS date/time words are never interpreted as LUDEF dates. Nonzero ARK dates
produce an explicit restoration warning; the source archive retains the metadata
unchanged. No timestamp conversion or setter is introduced. End-marker suffixes
containing only 00h/1Ah are tolerated as physical padding. Opaque suffixes produce
an unvalidated-trailer warning on LIST/TEST/EXTRACT; input bytes remain untouched.
ARK ADD/REMOVE/COMPACT remain unsupported, including archives with misleading
extensions. No ARK data is rewritten in this increment.

## Layout and active memory contract

The companion retains ABI 2 and gains a sixth descriptor, NHARK. Its checked load
address is the start of the writer-plan arena. LIST/TEST/EXTRACT do not use that
arena for LBR writes, so ARK code and private secondary iterator fit there while
the controller remains loaded. Reader callbacks, return addresses, resident data,
private stack and the frozen queue remain live. Extraction does not reload the
companion for each output record.

The loader copies to the matching descriptor's load/entry address, rather than
assuming every module replaces the controller window. The compiled expected
header binds that address and required end, alongside offsets, lengths, build ID
and the complete-companion CRC/EOF validation. Every ARK archive reloads and
validates NHARK; failure closes the source through the resident recovery path.
Writes reject ARC inputs before loading the supplemental module, so the live
writer plan cannot be overwritten. ARK extraction never enters an inner codec
phase that would replace the controller or reuse this arena.

Measured layout:

| Region | Value |
| --- | --- |
| Resident image | 18,441 bytes |
| Controller/codec window | 4980h |
| Codec context | 5180h |
| ARK supplemental module | 9200h, 1,973 bytes; rounded load end 9A00h |
| Writer plans | 9200h–AA00h |
| Transformed identities | AA00h–C400h |
| Largest required end | C400h |
| Loaded z80pack ceiling | C501h; 257 bytes spare |
| Loaded Model 4 ceiling | CA01h; 1,537 bytes spare |

The existing conservative controller gate still requires C400h even for reading.
No new TPA is assumed and no provider is unloaded for runtime qualification.
The footprint remains tight, particularly on z80pack; compressed-method work
requires a separate measured workspace design.

## Qualification and remaining work

The focused full-Z80 production harness covers both active ceilings, old/new
stored headers, present-zero CRCs, mixed supported/unsupported members, all
recognized compressed method IDs, duplicate and bad-CRC refusal before output,
opaque trailers, empty archives, source/destination users, signature dispatch,
mixed LBR/ARK batches, inner-expansion exclusion, DOS-date reporting, staged-save
faults, ARK-write refusal, cancellation, companion tampering and low memory.
Existing LBR read/adapter, writer, codec and coverage suites are retained.
Three pinned historical archives also pass production LIST/TEST/EXTRACT checks
on the full Z80 core with explicit unsupported-member outcomes and unchanged inputs.

The native campaign assembles and links the resident, controller, four codec
modules and ARK supplemental module with the unchanged ZSM4/LINK tools on both
platforms. It checks byte parity, reconstructs the companion from native products,
runs LIST/TEST/EXTRACT with terminal providers loaded, compares output and input
bytes, and checks the disposable filesystem. Runtime includes mixed methods,
CRC/duplicate refusal, opaque tails, empty input and unchanged LBR extraction.
The receipt and portable evidence distinguish these native checks from host
fault injection. The reader's existing historical/oracle qualification remains
in the foundation receipt; this increment does not claim compressed decoding.

Still open: native ARC decompression (methods 3–9 and their historical variants),
compatible encoding, staged ARK creation/updates with metadata/trailer
preservation, broader interoperability/release acceptance, Utilities Disk
packaging, and the separately deferred interactive browser. ZIP and `/LZ` remain
future scope. This increment adds no browser or archive-writing feature.
