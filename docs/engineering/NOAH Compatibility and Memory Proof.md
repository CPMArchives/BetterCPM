# NOAH CLI compatibility checklist and overlay feasibility

Status: increments 1–2, bounded research/prototype record, 2026-10-25.
Baseline: `e98797f95704174cbb77a918ecd1267007124cae`.
The [NOAH Specification](NOAH%20Specification.md) remains authoritative.
This work adds no production commands, archive writer, browser, release-media
entry, utility version change or resident service. It does **not** close full
NOAH qualification or the writer/ARK memory gates.

## 1. Frozen command checklist

“Existing” below describes maintained code, not new whole-spec acceptance.
The current CLI is `src/utilities/noah.mac` and its four common NOAH includes;
`tools/build_noah.py` emits its supported help text. Do not infer NOAH integration
from completion of the separate SQ/USQ/CR/UNCR utilities.

| Spec command or policy | Existing baseline | Remaining CLI increment |
| --- | --- | --- |
| Default LIST, `/LIST`, member pattern | LBR reader/listing | ARK handler; format recognition |
| `/TEST`, `/T` | LBR structural audit and selected-member CRC/readability | ARK method checks; unsupported-content coverage remains explicit |
| `/EXTRACT`, `/X`, destination DU | LBR staged extraction | ARK decoder integration |
| `/X /EXPAND` | Unsupported | One recognized inner layer, then ordinary output publication |
| `/ADD`, create, replacement | Unsupported | Staged writer; duplicates, accepted versions and retained deleted material |
| `/REMOVE` | Unsupported | Named preflight, approval and preservation rules |
| `/COMPACT`, with ADD or REMOVE | Unsupported | Explicit recovery-loss approval; active-only rebuild |
| Standalone `/SQ`, `/CR`, `/EXPAND` | Unsupported in NOAH | Bind existing codec libraries and naming policy |
| `/ADD /SQ`, `/ADD /CR` | Unsupported | LBR standalone representation; ARK native methods per table below |
| `/CAPACITY=n`, `/FORMAT=LBR\|ARK` | Unsupported | Full-tail validation and layout/format rules before mutation |
| `/VER`, `/HELP` | Existing forgiving exact-token queries | Keep precedence and absence of overlay/file activity |
| Frozen selectors, DU/attribute grammar, member filters | Existing; 512 archive identities × 13 bytes | Reuse for source plans; exclusions and duplicate ADD identities |
| `/Y`, `/R`, `/SYS`, overwrite choices | Existing extraction policy | Extend to specified writes without weakening protected-file authorization |
| `/Q`, Retry/Skip/Abort, all cancellation/summary paths | Partial/unsupported | Reuse shared input, retain mandatory prompts/warnings and exact recovery paths |
| Checked TMP/BAK replacement | Existing extraction machinery | Archive/codec writers must independently verify intended content before publication |
| Timestamp capabilities, binary lengths and source stability | Partial | Distinguish unavailable from error; no invented timestamp or Ctrl-Z trimming |
| Native build, overlays, final media acceptance | Not complete | This prototype provides scoped evidence only |

The remaining feature increments are unchanged: LBR writes; codec integration;
ARK; remaining CLI behavior; final qualification/package. No undo, recursive
expansion, mounting, ZIP, `/LZ`, encryption or interactive browser is added.

## 2. Finite format and codec compatibility baseline

The ARC baseline is the classic sequential `1Ah` header family documented by
Robert Freed's **ARC-FILE.INF**, based on ARC 5.12. `.ARK` and `.ARC` are filename
conventions for that family. Bounds must be validated before opaque preservation.
Recognizing a method does not establish decoded checksum coverage.

The following is the target for the later ARK increment, **not current NOAH
capability**. A selector must never fall back to another method when output grows.

| ARC method | Representation | Recognize / preserve bounded members | Decode and contents-test | Encode / selection |
| --- | --- | --- | --- | --- |
| 0 | End marker | Structural marker only | N/A | Emit archive terminator |
| 1 | Old stored, 25-byte header | Yes | Yes | No; new stored uses method 2 |
| 2 | Stored, 29-byte header | Yes | Yes | Default ADD without codec |
| 3 | Packed, RLE90 | Yes | Yes | No initial encoder required |
| 4 | Packed + Huffman squeezed | Yes | Yes | `/ADD /SQ` on ARK |
| 5, 6, 7 | Historical static-LZW variants | Yes, with known safe classic headers | Unsupported initially; report not contents-tested | No |
| 8 | Packed + dynamic LZW | Yes | Yes | `/ADD /CR` on ARK |
| 9 | Squashed dynamic LZW | Yes, classic bounded header | Unsupported initially; report not contents-tested | No |
| Later/ambiguous methods, Spark flags, subdirectories, extension records, self-extractors | Outside initial family | Reject unsupported structure; no blind relocation or resynchronizing scan | No | No |

Opaque retained members keep original header metadata and stored bytes. A known
unsupported method can be removed/replaced without decoding; retained unsupported
contents cannot earn a TEST PASS. Unknown structures whose bounds/meaning cannot
be established block updates. The original tool's permissive salvage scanning is
not a requested NOAH feature.

For LBR, retain the LUDEF5 reader model, including older unstamped directories.
CRC zero is ambiguous in legacy files; fixture coverage must separate absent,
valid-zero and garbage directory CRCs. Preserve deleted fields/data and holes
without interpreting malformed deleted references during ordinary updates;
active-only rebuilds discard them. These writer checks remain for increment 3.

| Standalone / LBR inner stream | Reuse target | Boundary |
| --- | --- | --- |
| Squeeze `76 FF` | `src/codec/sq.*`, `usq.*`, ABI 1 | Existing checksum/header/name policy; two encoder passes, stable rewind |
| Crunch `76 FE`, significant revision `20h`, checking selector 0 | `cr.*`, `uncr.*`, ABI 1 | CRUNCH 2.x stream; other versions/selectors refuse as unsupported |
| Ordinary bytes | Binary copy | Notice on standalone EXPAND; one-layer rule for X+EXPAND |
| CrLZH / reserved `/LZ` | No new integration | Existing separate utility does not put this in initial NOAH scope |

ARK method 4 can share compatible Huffman/RLE internals, with native archive
framing and CRC. Method 8 needs a native ARC bitstream implementation; CP/M
Crunch dictionaries, header and checksum are not interchangeable. **UNCR memory
measurements below do not establish ARK method-8 feasibility.**

### Pinned references, provenance and oracles

[references.json](../../tests/fixtures/noah/references.json) pins URLs, exact
source revisions, byte counts and SHA-256 hashes. `tools/noah_compatibility.py`
verifies them before using the ignored research cache. No downloaded historical
binary or external source is shipped or incorporated into BetterCP/M here.

* LUDEF5 HTML: reference definition, SHA-256 pinned; formatting is John Elliott's
  HTML rendering of the version-5 document. Consult for interoperability, not
  permission to copy implementation source.
* SEA/Unix ARC revision `325047b2dc60fad5f6c8238d8cb5294b9a5ada38`: Arcinfo,
  dispatch/packing source and license files pinned. Its current LICENSE records
  the 2003 GPL grant; COPYING is GPL v2. The old Readme contains older restrictive
  wording. Use as format/oracle research here; importing implementation would
  require an explicit license-compatible integration, not presumed permission.
* Deark revision `c19b47c80a5ff8a7b41eb4f578e1afdda99202a2`: decoder source,
  source archive and MIT-style COPYING pinned. Built unmodified as an independent
  host oracle. Any future copied code needs its notices and exception review.
* Original `crc32a.arc`, `de-lbr.arc`, `nulu15.arc` from the archived CP/M collection:
  seven real members, method 8 plus method 9. Independently extracted by Deark;
  lengths, output hashes and CRC diagnostics retained. `de-lbr.arc` has 146 bytes
  after its end marker: a padding/trailer qualification case, not data to silently
  discard during preservation. Inspection alone grants no redistribution rights;
  these archives stay in the ignored cache.
* Generated methods 1–4: independent host fixture generator, binary all-byte
  content including `00/1A/90/FF`, independently decoded and byte-compared by
  Deark. These are synthetic fixtures, not historical encoder output.
* Existing pinned SQ 1.7/USQ and CRUNCH/UNCR 2.4 fixtures and expected hashes remain
  in `tools/test_codec_historical_cpm.py` and the existing Compression Historical
  Interoperability evidence. This PR does not repeat their completed qualification.

The inventory is finite. Historical CP/M ARK encoder/decoder interchange, old
methods 5–7 preservation fixtures, malformed/valid-zero LBR CRC coverage, and
new native-method-4/8 encoder output remain explicit later qualification gates.
The downloaded `ark11.com` candidate was identified as a PMsfx self-extracting
distribution, not treated as a ready ARK executable or an established oracle.

## 3. API proof and overlay profile

`tools/noah_proof/proof.inc` is the single shared **prototype profile 1** include.
It reuses archive read ABI 1 and codec ABI 1 without changing either production
include. Generated cross/native sources consume those same definitions. No
writer interface or new codec step ABI is advertised by this experiment.

| Surface | Actual exercised contract |
| --- | --- |
| LBR | IX points to caller-owned 138-byte context; OPEN/NEXT/READ entry table; 32-bit absolute source offset, 16-bit count/pointer, explicit actual count and AS result |
| UNCR | IX points to caller-owned 26,582-byte context; INIT/HEAD/RUN; byte callbacks, verified stream end, latched CS errors |
| Registers | Existing libraries preserve IX/IY, alternate banks and stack balance; ordinary registers scratch |
| Alternate source | Resident memory-source callback feeds a generated LBR; deliberately clobbers ordinary registers; offset high words, wrap and source bounds checked |
| Live nesting | Codec READ callback saves codec IX, calls the separately loaded LBR reader with archive IX, and returns a member byte; both modules remain loaded throughout |
| Output | Resident sink compares every decoded byte and exact 1,024-byte count against `00..FF` repeated four times; codec also validates its own checksum |
| State lifetime | Both contexts, metadata, source fixture, DMA, sink count, stack and callbacks are outside replaceable module bodies |

The prototype overlays only code. It reserves the **entire current 19,674-byte
NOAH image additionally**, including its existing 6,656-byte frozen plan,
publication state, buffers and old stack. This is conservative accounting, not
execution of the production selector/publisher inside the prototype. It avoids
claiming that the final resident controller will shrink by an unmeasured amount.

The companion is a record-aligned `NOAH.OVL`: 128-byte header, two indexed modules,
and zero alignment padding. The include defines every header/index field. Header
has magic `NHOV`, format version, module count, 8-byte build identity, physical
length and header size. Each 16-byte index entry records module/ABI, file offset,
code length, load/entry addresses and context bytes. The executable binds the
entire expected header before using code; untrusted addresses never drive loads
or dispatch. Host construction uses fixed non-overlapping code/state allocations.

CRC-32/ISO-HDLC covers the **whole file**, including index, sizes, module bodies
and record padding, treating checksum bytes 124–127 as zero. Exact length, EOF,
signature, ABI, build, entry/offset/workspace fields and CRC are checked before
executing either module. A corrupt invocation-DU copy does not trigger fallback.
Lookup is invocation DU, then A0 only when absent. Caller user and default DMA
are restored; the loader never changes caller drive. There are no filesystem
mutation calls. Each invocation reloads and validates all code, so no stale
companion validation is cached across loads.

This fixed two-module profile proves simultaneous code/callback safety. It is
not the final demand loader: changed-companion checks between later module
loads, writer capabilities, CP/M streaming adapter binding, block step/yield
semantics and mid-transaction overlay failures still need implementation in
their owning increments. Existing byte callbacks require an explicit adapter or
deliberately versioned extension for the spec's bounded step interface.

## 4. Measured Model 4 memory boundary

The proof checks the active exclusive ceiling at `(0006h)` **before** switching
to its private stack or accessing overlay/context allocations. Low memory returns
an explicit refusal using the caller stack. It does not lower the OS contract or
borrow screen/resident RAM. Bounds are generated from assembled lengths.

| Allocation | Bytes |
| --- | ---: |
| Existing NOAH, fully reserved | 19,674 |
| Proof resident, fixture, DMA, extra 512-byte stack | 2,573 |
| Alignment before companion | 25 |
| Companion header, two module bodies and alignment | 2,688 |
| Archive context | 138 |
| Largest current required decoder context, UNCR | 26,582 |
| Context guards/gaps | 4 |
| Total TPA, `0100h..CAE3h` | **51,684** |

Actual ranges and source/artifact hashes are in the accompanying JSON evidence.
[The evidence index](NOAH-Compatibility-Memory-Proof.json) records scoped results
and hashes; the [portable bundle](NOAH-Compatibility-Memory-Proof-evidence.tar.gz)
retains controller/module bytes, native receipts, console captures and oracle
logs without external programs, OS images or historical archive distributions.
LBR module: 957 bytes including 9-byte entry table. UNCR: 1,458 bytes including
entry table and common codec helpers. Other current codec measurements, including
common helpers: SQ 1,385 + 3,524 context; USQ 929 + 1,440; CR 1,194 + 25,207.
These are assembled sizes, not estimates from source length.

| Configuration observed on disposable normal-RAM media | Ceiling | Result / margin |
| --- | --- | --- |
| cpmsim, bare | D501h | PASS, 2,589 bytes above prototype minimum |
| cpmsim, ANSISCRN + ANSI | C501h | Refuses; short 1,507 bytes |
| Model 4, bare | D501h | PASS, 2,589 bytes above prototype minimum |
| Model 4, M4SCRN + ADM3A | CA01h | Refuses; short 227 bytes |

The Model 4 **can run this simultaneous LBR/UNCR proof with no terminal RSXs**.
The conservative layout cannot run with the observed terminal pair. Neither is
a guarantee that the completed writer fits: new transaction buffers, codec/native
ARK state and code have not been measured. Removing duplicated linked reader
code as part of real overlay integration may recover space, but that saving is
not claimed here and the frozen selection plan is not silently reduced.

The added prototype needs two directory entries, COM 22,247 bytes (174 records)
and OVL 2,688 bytes (21 records). Filesystem allocation rounds further to its
block size. It uses no scratch output. This gives no bound for future archive
transactions, which still require staged original-sized output and preservation
of recovery files on error. No throughput claim is made from this small fixture.

## 5. Bounded qualification and remaining gates

Host full-Z80 checks cover successful nested decoding, exact minimum and one byte
below, untouched protected memory, zero-capacity read, caller DU/DMA restoration,
invocation/A0 lookup, no arbitrary DU search, invalid local-copy refusal, changed
header/index fields with recomputed CRC, body/checksum corruption, truncated or
extra records, read and close failure. All original input bytes remain unchanged.
The 512-byte private stack retains its bottom 64-byte guard and contexts retain
their checked canaries. This is an observed bound on these exercised paths,
**not a formal worst-case stack bound for future writers or arbitrary callbacks**.

Both target runtimes execute the same pinned prototype/companion and demonstrate
successful bare operation and safe loaded-RSX/corrupt-companion refusal. cpmsim
has complete native ZSM4/LINK byte parity for controller and both modules.
Model 4 ZSM4 reports zero errors for all three; its controller REL is byte-identical
to cpmsim's and both smaller modules link. **Controller LINK on Model 4 remains
BLOCKED**: LINK 1.3 prints `NO FILE:` even with an explicit input drive and the
terminal modules unloaded. Runtime success there uses the cross-built controller;
it must not be reported as complete Model 4 native toolchain qualification.
Resolving that bounded build gate is follow-up work, not a reason to modify the
external ZSM4/LINK programs in this PR.

The proof closes the requested measurement question to the extent above. It
does not approve starting a substantial memory redesign. Before full CLI closure:
complete the actual controller split, common writer/step interface and measured
writer/ARK budget; close the Model 4 native LINK gate; then qualify the new feature
increments and final exact COM/OVL pair. Physical hardware, checked/ROM profiles,
final Utilities media and historical CP/M ARK interchange are NOT RUN here.

### Reproduction

```
python3 tools/test_noah_proof.py
python3 tools/build_noah_proof.py
python3 tools/qualify_noah_proof.py --platforms z80pack --output /absolute/new/native-proof
python3 tools/qualify_noah_proof.py --runtime-only --platforms trs80gp --output /absolute/new/model4-proof
python3 tools/noah_compatibility.py --fetch --generate-vectors --oracle-deark /absolute/pinned/deark
```

Native runs need the existing disposable-system campaign inputs, cpmtools,
cpmsim/trs80gp and external ZSM4/LINK. Override `--system` and `--utilities` for
their locations. References are hash-checked downloads; build the pinned Deark
source unmodified with `make`, then use a fresh oracle output cache. No broad
regression suite or release-disk rebuild is required for this prototype PR.
