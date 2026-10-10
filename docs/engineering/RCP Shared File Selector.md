# RCP shared file-selector integration

Status: common DU/qualifier/predicate components linked and qualified in RCP on
2026-10-10. The combined transactional parser is implemented and tested;
resident DIR uses the interface; other command migrations remain pending. This work precedes expanded DIR.COM
implementation.

## Placement and scope

The current package is RCP.CPX. Include the common selection implementation once
inside that package for its sequential command handlers. Transient utilities
remain self-contained, linking the same source privately. This is an internal
RCP calling convention, not a new cross-package CPX service or BDOS function.

Reuse the [extended DU contract](208%20Extended%20DU%20Syntax.md): a 64-byte map,
four bytes per drive, one bit per user, with a shared iterator. Capture caller
DU once, validate the full operand before mutation, clear results on failure,
and retain a meaningful error position. Include bounded 8.3 wildcard parsing
and the shared attribute predicate grammar. Command-specific operation and
protection policy remains with DIR, ERA, COPY, REN or TYPE.

Scratch/results may be package-owned because commands execute sequentially.
COPY must preserve its source result before parsing the destination. No pointer
into reconstructable CPX memory may survive transient execution or WBOOT.

## Audit measurements

The pre-integration audit measured the current RCP as 3,795 executable bytes,
3,840 allocated bytes, and 425 relocation entries. Appending a single DU engine
and workspace produces 4,442 bytes, a 4,608-byte allocation, and 511 relocations.
Appending DU, operand qualifiers and attribute predicates produces 4,800 bytes,
4,864 allocated bytes, and 544 relocations. These are prototypes, not the final
integrated command implementation or a qualified expanded RCP.

The DU component uses 571 code bytes plus 76 map/workspace bytes. Qualifier
splitting uses 106 bytes; attribute predicate parsing uses 252 bytes. Existing
bounded filespec code is already shared among RCP handlers and must be refactored
for common use rather than duplicated. The current qualifier splitter's failure
position also needs attention when assembling the combined error contract.

## Qualifier error-position prerequisite

The shared qualifier splitter now exposes `OQ_ERRPTR` without changing its
existing restored-HL calling convention. Success clears the pointer. Failure
points to the offending byte; a missing closing bracket points immediately past
the input. A suffix after `]` points to the first suffix byte. Failed calls still
clear qualifier pointer/length, and a subsequent successful call clears stale
diagnostics. The combined wrapper must translate this pointer to its operand
error position and clear its complete result; the splitter alone does not clear
the DU map.

This adds 14 bytes to RCP (4,814 executable bytes, still 4,864 allocated bytes),
with 547 relocations. The shared source also adds 14 bytes to COPY.COM (10,320
bytes); COPY's existing callers retain their behavior. No BDOS change is involved.
Exact malformed/truncated error positions and success-after-failure were tested
in COPY and at three relocated RCP origins. DU, attribute, carrier-format, COPY
filespec, mapping and reporting regressions pass. This prerequisite does not
complete the transactional wrapper or migrate any resident command.

## Combined operand transaction

`FS_PARSE` is an internal RCP entry supplied by `common/rcpselect.inc`. Input is
HL/B (operand pointer/length) and D/E (captured caller drive/user). It makes no
BDOS calls and leaves the input untouched. Success returns carry clear and:

- `DU_MAP`: the existing 64-byte location map, consumed through `DU_NEXT`;
- `FS_FCB`: a 36-byte search FCB with an unqualified drive byte;
- `FS_MASK`: the shared eight-state attribute truth mask (FFh if unfiltered).

An empty filespec defaults to `*.*`, including DU-only selections. Unqualified
filespec qualifiers are separated from DU scanning without modifying the common
DU library. Qualified operands retain the complete DU grammar. The existing
bounded lexer and FCB expander are reused; COPY's wildcard and operand-policy
settings are saved/restored. Their remaining parser workspace is scratch.

Failure returns carry set, HL at the detected position, and `FS_ERROR` identifying
location (1), qualifier (2), predicate (3), or filespec (4) processing. The entire
DU map, result FCB and predicate mask are cleared. Error classes identify the
stage that detected the problem, not a guessed intent for malformed syntax.
A later valid call clears the error. No command operation is performed here.

RCP now measures 5,091 bytes, rounded to 5,120 bytes: +277 executable bytes and
+256 reclaimable allocated bytes over the preceding increment. There are 588
relocations; the 1,536-byte header remains sufficient. Native ZSM4/LINK produces
the same 5,091 bytes. BDOS is unchanged; transient builds exclude this RCP wrapper.

Relocated tests at 4000h, 8101h and A000h cover inherited/compound scopes,
unqualified predicates, empty defaults, wildcard expansion, policy preservation,
input immutability, failed-result clearing, and successful reuse after failures
in every stage. Existing DU, qualifier, predicate, carrier and COPY filespec
checks pass. Evidence: `/private/tmp/rcp-selector-transaction-pass-20261010`.
Resident DIR is the next consumer; this increment does not yet expose the expanded
syntax through a command handler.

## First consumer: resident DIR

The RCP-only build replaces DIR's single-DU setup with `dir-select.inc`, leaving
the current transient fallbacks unchanged. DIR parses the complete operand before
selecting a location, rejects any drive beyond the current A:–D: bindings before
iteration, and searches each selected DU through the shared iterator. A separate
index survives BDOS calls. It restores the original DU after success or errors.

Each output row now identifies the drive and user (`A0:`, `B3:`, etc.). The existing
four-column display and physical-extent grouping remain. An empty matching scope
reports NO FILE per DU. Attribute predicates run against the three directory bits.
Without a qualifier SYS files retain their traditional hidden behavior; with an
explicit qualifier the predicate determines inclusion, including SYS files.
No sorting, size reporting, paging or command-specific display options are added.

RCP measures 5,234 executable bytes, 5,376 allocated bytes (+256 reclaimable),
605 relocations, and a 6,842-byte carrier. Native and host assembly match. BDOS
is unchanged and all six transient fallback binaries remain unchanged. Relocated
predicate tests cover five masks across all eight attribute states at three
origins. The z80pack native lifecycle test includes populated users 0 and 2,
filter exclusion, malformed predicates and atomic unsupported-drive rejection.
The Model 4 test uses the same commands (user 2 is empty there). SUBMIT test scripts
escape literal dollar signs as `$$`, rather than invoking parameter substitution.
Both native platform runs passed, including unload/reload and WBOOT with DIR.COM
absent. Evidence is retained in `/private/tmp/rcp-dir-native-z80pack-20261010`,
`/private/tmp/rcp-dir-native-model4-captures-20261010`, and
`/private/tmp/rcp-dir-relocated-20261010`.

A larger shared parser does not by itself implement multi-DU COPY: its frozen
batch/preflight storage and operation contract require separate accounting.
Other modifying commands also need their own protection and preflight contracts.
Parsing acceptance must not silently broaden destructive behavior.

## First increment: carrier capacity

The former host packer limit was a 1,024-byte relocation header, allowing 488
entries. Both appended prototypes exceed that limit. The native loader already
uses declared aligned header size and streams relocation records; no loader or
BDOS change is required for a third header group.

The host builder now permits up to 1,536 header bytes (744 relocation entries).
One- and two-group output remains unchanged, and excess capacity is rejected.
The header is file storage, not extra runtime allocation. Version-1 fields and
ABI remain unchanged; see [Engineering Specification 119](119%20BCPX%20Version%201%20Module%20Format.md).

`tools/test_cpx_large_header.py` builds a private HELLO-derived probe with 489
additional relocated words. It compares every word with the actual loaded
message address on three invocations: initial load, WBOOT reconstruction, and
explicit unload/reload. It also checks packer boundaries at 232/233, 488/489,
744/745. This probe qualifies header handling, not the future selector API.

The probe passed on z80pack and Model 4. Current RCP.CPX and HELLO.CPX rebuilt
byte-for-byte unchanged; the existing carrier-format checks also passed.
Evidence bundle: `/private/tmp/rcp-header-qualification-bundle-20261010`.
All 42 inventoried files passed size/hash verification. Manifest SHA-256:
`2ec5f4c23954caa64e4c9c21753e813b192d73349dd13348b30cbd1d764ef612`.

## Following increments

1. Integrate one shared parser/result/iterator implementation and qualify its
   syntax, relocation and error atomicity.
2. Migrate resident read-only listing behavior first, with command-specific
   options outside the generic selector handled separately.
3. Migrate modifying commands only with their explicit operation contracts,
   accounting for complete preflight and protection semantics.

Measure actual final executable size, rounded allocation, relocation count,
reconstruction and recovered TPA at each increment. BDOS growth remains zero.

## Shared component integration — 2026-10-10

### Resident ERA validation prerequisite

RCP's ERA handler now passes its full operand through `FS_PARSE` before its
legacy selection/deletion path. The gate captures caller DU, preserves the input
pointer/length, and rejects malformed bounded filespecs before any mutation.
It deliberately rejects bracketed scopes and predicates with a distinct
unsupported-selection diagnostic: accepting those parsers must not let the old
erase operation silently ignore them. Empty operands and ordinary single-DU
forms retain their existing behavior, including the all-wildcard confirmation.

This is validation adoption, not multi-DU ERA implementation. Its destructive
selection/confirmation/protection contract remains a separate step. Transient
builds exclude this RCP-only gate. RCP is 5,371 bytes, still allocated 5,376 bytes,
with 622 relocations; BDOS remains unchanged. Native assembly matches the host
payload. Relocated gate tests cover valid/rejected operands, input preservation
and captured caller DU at three origins. Native tests reject a malformed pattern
and an extended selector, inspect the surviving marker, then erase it with an
ordinary exact filename and confirm NO FILE.
Both z80pack and Model 4 pass with DIR.COM absent. Evidence:
`/private/tmp/rcp-era-gate-relocated-20261010`,
`/private/tmp/rcp-era-gate-z80pack-final-20261010`, and
`/private/tmp/rcp-era-gate-model4-captures-20261010`.

RCP now links exactly one copy of the existing DU parser/iterator, qualifier
splitter, and attribute predicate compiler, with package-owned scratch. Build
expansion uses the same common source files as the transient utilities; the
RCP marker is omitted from transient builds to avoid duplicates and byte growth.
No resident command uses the added entry points yet. In particular, this does
not claim complete invocation validation or error atomicity across all three
components. The qualifier splitter still returns its original HL on failure;
the combined wrapper must resolve that error-position contract and clear all
results on later parsing failures.

Measured RCP code: 4,800 bytes; rounded allocation: 4,864 bytes (+1,024 reclaimable
bytes from the prior RCP); relocations: 544; carrier header: 1,536 bytes; file:
6,408 bytes. Carrier SHA-256:
`a130dc4e1d419e9c5ef6f402528c6f8a8991be208b503afde8fb2324318334e6`.
BDOS bytes match the preceding header qualification snapshot. All six generated
transient fallbacks remain unchanged, including the 10,306-byte COPY.COM.

Native ZSM4/LINK and host assembly produced identical 4,800-byte payloads. Native
build staging now explicitly emits the cross assembler's FF scratch fill; LINK
does not define DS fill bytes, and implicit fill initially prevented parity.
Runtime parsing initializes the scratch it uses; this is build reproducibility,
not a new runtime initialization policy.

The actual carrier's relocation table was applied at 4000h, 8101h and A000h.
Tests executed DU scopes, caller-drive inheritance, domain/syntax errors,
input preservation, all 512 iterator positions, qualifier splitting, predicate
truth masks, and the existing bounded wildcard validator. The common library
campaigns additionally passed 1,024 ranges, 295 expressions across eight
attribute states, malformed/truncated qualifiers, and iterator boundaries.

The expanded production carrier passed unload/reload and resident DIR dispatch
before and after CPX.COM-induced WBOOT on z80pack and Model 4. DIR.COM was absent
in both tests. This qualifies carrier lifecycle and existing command behavior;
the new parsing routines were executed in the relocated instruction harness.

Evidence: `/private/tmp/rcp-selector-component-bundle-20261010`; all 47 files
passed manifest size/hash verification. Manifest SHA-256:
`1d9513b7c27db18dee0b49ae855237d075fe9ba500b6e8646b5da6bb827d086f`.

Next: compose the parsers into one transactional result contract, share bounded
filespec validation without COPY-specific state coupling, then migrate resident
DIR. This step does not broaden ERA/COPY/REN/TYPE operation semantics.
