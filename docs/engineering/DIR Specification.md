# BetterCP/M 1.0 transient DIR specification

Received 2026-10-09. DIR.COM now implements the shared selection language,
attribute predicates/display, file grouping, allocated KiB/record units,
name/type/size/native-order sorting, automatic/explicit columns, paging,
per-DU selected totals and once-per-drive free space. It is self-contained and
works with RCP unloaded. Extent units (`/Z=E`) await their definition; combined
qualification of the implemented feature set passes on both platforms.
Explicit :DIR/.DIR works; automatic handoff is still unimplemented.

The implementation history below records each qualified increment.
## Selection baseline — 2026-10-10

The host and native builders produce a self-contained 5,370-byte DIR.COM from
the same source used by resident DIR. It includes one copy of the DU map/iterator,
qualifier splitter, attribute predicate compiler and bounded filespec validator.
This first build retains the common command body; later reporting work can
replace that transitional packaging. There is no dependency on a loaded CPX,
new BDOS service, or protected-memory allocation. RCP and the five other transient
builds are unchanged by this increment.

The baseline has the existing four-column display, drive/user row prefixes,
per-DU NO FILE results, and caller-DU restoration. It validates the full operand
before searching, rejects unsupported drives and malformed selectors, and uses
*.* for omitted filespecs. Plain selection hides SYS; an explicit attribute
predicate replaces implicit SYS suppression. This matches the qualified resident
selector behavior and resolves that selection question for the transient too.
At this baseline, sizes, summaries, adaptive columns, paging, attribute display
and sort options were not implemented; later increments are recorded below.

Native ZSM4/LINK and host assembly match DIR.COM. The native build stages DIR's
source on B: to keep the three source images within its disposable floppy capacity.
Six selection cases pass on z80pack and Model 4 with RCP explicitly unloaded,
including :DIR and .DIR, compound user selection, SYS/ARC/RO predicates, malformed
wildcards, and invalid user numbers. z80pack disk images remain byte-identical;
Model 4 fixture content and attributes remain unchanged (SUBMIT's stream changes).
The test also confirms that the saved Model 4 DIR image matches the tested binary.
Evidence: `/private/tmp/dir-selector-z80pack-current-20261010` and
`/private/tmp/dir-selector-model4-20261010`.

## Size-accounting foundation — 2026-10-10

DIR.COM now accumulates selected allocation records, logical records and physical
directory-entry counts while its existing directory search visits each entry.
The accounting helper issues no BDOS calls, so it cannot replace the active
search or alter its DMA buffer. Totals cover the whole selected DU set and reset
at each invocation. Predicate filtering and implicit SYS hiding apply before
accounting; entries beyond the first physical extent group still contribute.

All three totals use four bytes, including entry counts across multi-DU sets.
Allocation uses the DPB's byte/word block-map format and BSH; logical
records use `(EX & EXM) * 128 + RC`. Zero allocation slots contribute nothing.
This increment prepared reporting without yet adding visible sizes, `/Z`, sorting,
per-file aggregation or summaries. The physical-entry counter is available for
the proposed E metric; its displayed definition remains part of the reporting
contract clarification below.

The helper is linked only into DIR.COM, now 5,607 bytes (237 bytes added).
Native ZSM4/LINK matches host assembly. RCP, BDOS and the other five transient
utilities are unchanged. Production-binary execution checks 450 accumulation
cases covering empty/sparse/full maps, both block-number widths, several block
sizes, EXM/RC boundaries, repeated entries and carries into higher total bytes;
selection visibility gates also pass.
The existing six z80pack selection cases pass, with unchanged private disk
images. Evidence: `/private/tmp/dir-metrics-z80pack-qualified-20261010`.

## Per-file allocation display — 2026-10-10

The transient now collects one record per normalized filename within each DU,
aggregates all selected physical entries, and displays allocated KiB. An empty
file is 0K; a multi-extent file is listed once with its complete allocation.
Each DU has a heading and a file-count/allocated-KiB summary; the same filename
in two DUs is counted independently. Implicit SYS hiding now excludes hidden
entries from both collection and totals; an explicit predicate controls visibility.

The collector makes a single directory traversal per DU and does not perform
nested file searches. Its 24-byte records occupy disposable TPA after the
transient image, bounded below the current BDOS/RSX entry with 256 bytes reserved.
If another unique filename will not fit, `Directory too large.` stops the command
before printing that DU's listing; existing records can still aggregate without
requiring more space. The caller DU is restored on completion and this error path.
The buffer is reset between DUs. No filesystem writes are performed.

This is an intermediate one-column formatter in native discovery order.
Name sorting, adaptive columns, `/Z` units, attribute display, paging and
drive-free-space reporting remain pending; the final interface below is still
the target. Decimal output is generated from COPY's qualified formatting source,
linked independently into DIR, so DIR does not depend on COPY.COM or RCP.

Qualification covers out-of-order multi-extent aggregation, attribute-bit masking
in filename identity, empty files, buffer exhaustion, aggregation at capacity and
32-bit KiB conversion. The public platform cases include a 40,000-byte file
displayed once as 40K and the same filename in another user area at 2K.

DIR.COM is 6,014 bytes, 407 bytes larger than the accounting foundation. Host
assembly and native ZSM4/LINK match. Eight public cases pass on z80pack and
Model 4 with RCP unloaded, including filtered totals and caller-DU restoration.
Private z80pack images remain byte-identical; Model 4 fixture bytes/attributes
remain unchanged after SUBMIT. Evidence:
`/private/tmp/dir-sizes-z80pack-final-20261010` and
`/private/tmp/dir-sizes-model4-final-20261010`.

## Default name sorting — 2026-10-10

DIR.COM now sorts each collected DU independently by ascending normalized
filename, then extension. Sorting occurs after collection and before display,
without changing directory search order, issuing BDOS calls or writing the disk.
Whole 24-byte records move together, preserving all per-file metrics. Equal keys
retain their original order. Empty and single-file listings require no sorting.
The sorter stops after a pass with no exchanges and omits the already-sorted
tail from later passes.

This adds 139 bytes: DIR.COM is 6,153 bytes. No additional per-file workspace is
needed. Host and native ZSM4/LINK assembly match, and resident code and other
transient utilities are unchanged. Thirty-six production-binary cases cover
permutations, equal keys, already-sorted and reversed inputs, extension tie-breaks,
buffer guards and a 260-file count; complete record identities and totals remain
unchanged. Collection, capacity and 450 metric cases continue to pass.

Nine public cases pass on z80pack and Model 4 with RCP unloaded. They check
alphabetical ordering within each DU, extension tie-breaks with different sizes,
multi-extent de-duplication, filtered totals and caller-DU restoration. Private
z80pack disks remain byte-identical, and Model 4 fixture content and attributes
remain unchanged. Evidence: `/private/tmp/dir-name-sort-z80pack-20261010` and
`/private/tmp/dir-name-sort-model4-20261010`.

The formatter still uses one column. Explicit `/S=N`, reverse ordering, type/size
sorts and `/S=U` remain pending, along with the other reporting options. The
specification below continues to describe the final target.

## Explicit sort switches — 2026-10-10

Implemented `/S=N`, `/S=T`, `/S=Z` and `/S=U`. N/T/Z accept optional `+` or `-`;
no sign means ascending. U preserves the collector's native discovery order and
rejects either sign. Name order compares filename then extension. Type order
compares the extension; size order compares the full unsigned 32-bit allocated
record count, independently of displayed KiB. Type and size ties use ascending
filename+extension even when the primary key is reversed.

A transient-only command transaction separates one selection operand from
command-wide switches. Switches may precede or follow the operand; repeated
valid sort switches use the last value. Defaults reset to name ascending at
every invocation. Unknown switches or invalid values report `Invalid option.`
and reject the complete command. Invalid operands still report `Invalid filespec.`
The original command tail is unchanged, and failed validation clears the shared
selection map, FCB and predicate before any drive/user selection or directory
listing. An invalid earlier switch is not excused by a later valid switch.
The `/` inside a qualifier such as `[$R/O]` remains part of the operand.

DIR.COM is 6,640 bytes, 487 bytes larger than the default-name-sort build. The
growth includes a 128-byte private operand buffer; no protected state, BDOS or
resident CPX change is required. Host and native ZSM4/LINK assembly match.
Twelve valid and sixteen invalid command forms pass production-binary tests,
including a 127-byte tail, failure atomicity and resetting defaults between invocations. Sort
qualification now covers 246 cases across all keys and directions, with size
boundaries crossing 8-, 16- and 24-bit values and the maximum unsigned DWORD.
Whole-record identity, stable equal keys, buffer guards and DU totals are preserved.
Collection/capacity tests and the 450 metric cases also pass.

Eighteen public cases pass on z80pack and Model 4 with RCP unloaded, covering
all keys, reverse order, native order, last-switch-wins behavior and rejection
before listing. Caller DU restoration, sizes and filtered totals remain correct.
Private z80pack disks are byte-identical before/after; Model 4 fixtures retain
their content and attributes. Evidence:
`/private/tmp/dir-sort-options-z80pack-20261010` and
`/private/tmp/dir-sort-options-model4-20261010`.

The one-column formatter remains unchanged. Alternate `/Z` units, attribute
display, paging, adaptive/explicit columns and drive-free-space reports remain
pending. Unsupported options currently reject rather than silently doing nothing.

## Attribute-display implementation increment

Implemented `/A` as the fixed `SRA` field after the allocated-KiB size. SYS,
read-only and ARC use positions 1, 2 and 3; a clear bit prints `-`. The option
is repeatable, case-insensitive and independent of sorting. It resets to off
for every invocation. `/A=...`, `/AA` and other malformed forms reject the
complete command before listing.

Display does not change selection or SYS visibility: `/A` alone still hides SYS
files. Existing attribute-expression operands select files independently.
There is no wheel position or new metadata. The existing reserved byte in each
24-byte collected file record now holds RO/SYS/ARC bits, conservatively ORed
across the selected physical entries. Sorting moves those bits with the entire
record. No extra per-file buffer space is needed and filesystem metadata is
never modified.

DIR.COM is 6,763 bytes (+123 from the sort-switch increment), SHA-256
`349cb447469ef5035e12552c6eff899bed7dd55fff105db9b41a71c52ebf4450`.
Native ZSM4/LINK assembly matches the host binary byte for byte. Other derived
utilities, RCP, CCP and BDOS are unchanged by this increment.

Focused qualification covers all eight attribute masks, disabled display,
immutable directory entries and extent aggregation. Fifteen valid and twenty
invalid command forms pass, including reset and failure atomicity. The
collector/capacity checks, 246 sort cases and 450 metric cases also pass.

Twenty-five public cases pass on z80pack and Model 4 with RCP unloaded,
including all eight displayed masks, default SYS hiding, explicit SYS selection,
compound-DU selection, reverse sorting with attributes, repeated `/A`, a following
invocation without `/A`, and malformed-option rejection before listing. Caller
DU restoration and existing size/count reports remain correct. z80pack images
are byte-identical before and after; Model 4 fixture contents and attributes
are preserved. Evidence: `/private/tmp/dir-attributes-z80pack-final-20261010`
and `/private/tmp/dir-attributes-model4-20261010`.

Alternate `/Z` units, paging, adaptive/explicit columns, drive-free-space reports
and final combined qualification remain pending.

## Allocated-size unit implementation increment

Implemented `/Z`, `/Z=K` and `/Z=S`. K remains the default allocated-KiB
representation; S is allocated 128-byte records, not physical sector count,
logical length or exact file bytes. Per-file and selected-DU totals use the
same chosen representation and suffix. Size sorting remains based on allocated
records, independently of the display option. Options can appear on either side
of the selection operand; the last valid size option wins, and `/Z` restores K.
Each new invocation resets the unit to K. Malformed units reject the complete
command before any listing. Attribute display and selection are independent.

The `/Z=E` definition is still awaiting the explicit physical-directory-entry
versus logical-16K-extent decision. It is not implemented in this increment.

DIR.COM is 6,848 bytes (+85), SHA-256
`8805cb72f8bc6d5c21b899c68694e94167341cf68435234a947269f5b89fa30d`.
The native ZSM4/LINK output is byte-identical. No resident component or other
utility changes are required.

Focused checks cover K/S conversion across DWORD boundaries, defaults, last
value wins, reset, coexistence with sorting and attributes, and invalid options.
Twenty-one valid and twenty-six invalid parser cases pass, along with the eight
attribute combinations, collection/capacity checks, 246 sort cases and 450 metric
cases.
Thirty-four public cases pass on both z80pack and Model 4 with RCP unloaded.
The new cases cover `/Z` equivalence with `/Z=K`, allocated records and matching
totals, compound-DU attribute reporting in S, last-unit-wins, default reset and
malformed-option rejection. Existing selection, sorting and K reports remain
correct. z80pack images are byte-identical before/after; Model 4 fixture contents
and attributes are preserved. Evidence:
`/private/tmp/dir-size-units-z80pack-20261010` and
`/private/tmp/dir-size-units-model4-20261010`.

## Paging increment — implemented

Implemented `/P` in transient DIR.COM only. All character and string output
passes through one line counter, including headings, blank lines and summaries.
The current supported display baseline is 24 rows: pause after 23 emitted LF
characters, immediately before the next output character. This avoids a redundant
pause when the final output ends exactly at a page boundary. No public console
geometry query is introduced; variable-height paging remains a future extension.
Current single-column output fits within the supported 80-column display.

The prompt is `MORE -- Space/ENTER for next page; ^C abort.` Space and Return
continue; other keys are ignored. Ctrl-C unwinds the output stack and restores
the caller's drive/user before returning. `/P` is repeatable, works alongside
selection, sorting, units and attributes, and resets to off on each invocation.
Malformed paging options reject the invocation before listing.

DIR.COM is 7,072 bytes (+224), SHA-256
`607c479bf38054efad4582fd4e2aa54c578ef47d43cd9cf7493daecf407d7087`.
Native ZSM4/LINK output is byte-identical. BDOS, BIOS, CCP and RCP are unchanged.
Focused execution checks cover page boundaries, no final pause, ignored keys,
Space/Return, disabled paging, and Ctrl-C stack/DU restoration. The parser passes
24 valid and 29 invalid forms. Existing collection, attribute, metric and sort
checks and all 34 public z80pack regression cases pass.

Public paging qualification passes on z80pack and Model 4 using thirty empty
files, with RCP unloaded and a
caller DU different from the selected DU. It checks Space/Return continuation,
Ctrl-C restoration, repeated `/P`, combined attributes/record units, and paging
reset on the next invocation. Disk contents and attributes must remain intact.
Evidence: `/private/tmp/dir-paging-z80pack-20261010c` and
`/private/tmp/dir-paging-model4-20261010b`.

## Column-layout increment — implemented

DIR now measures the actual rendered file fields in each selected DU using the
same numeric/attribute formatter as visible output. Dry measurement emits no
BDOS output and consumes no paging lines. The widest selected cell determines
padding; three-character ` : ` separators occur only between adjacent cells.
Automatic layout tries four, two and one column against the supported 80-column
display. This uses the existing platform width baseline, not a new resident
geometry service. A wider/narrower console binding needs separate qualification.

`/C=1`, `/C=2` and `/C=4` are case-insensitive. Last valid request wins; each
invocation resets to automatic. Malformed forms reject the command transaction.
A valid explicit count that cannot fit reports `Requested columns do not fit.`
before that DU's heading/listing; prior DU sections may already have been shown.
There is no silent reduction. Rows fill left-to-right in the selected sort order,
with one newline after a complete or partial final row. Paging counts these
rendered rows, including headings/summaries, rather than individual file cells.

DIR.COM is 7,381 bytes (+309), SHA-256
`b4d1ed2dd153309ab420b089f12476ddcf85b32bf3f2d71c7aafae7ac3b3c705`.
No resident component or other utility changes are required. Focused width/fit
checks cover 176 combinations of allocated sizes through DWORD boundaries,
units, attributes and automatic/explicit counts. The parser covers 27 valid and
38 invalid forms, including last-value wins and next-command reset. All 34
existing public z80pack cases pass. Nine new public cases pass on z80pack and
Model 4 with RCP unloaded: explicit 1/2/4, actual digit-width padding, attribute
widths, automatic fallback to two columns and rejection of oversized explicit
requests. Fixture contents and attributes are preserved. Native ZSM4/LINK is
byte-identical. Collection, eight attribute masks, 246 sort cases, 450 metric
cases and focused paging controls/boundaries pass.

Column evidence: `/private/tmp/dir-columns-z80pack-20261010` and
`/private/tmp/dir-columns-model4-20261010`. Paging regression evidence:
`/private/tmp/dir-columns-paging-z80pack-20261010` and
`/private/tmp/dir-columns-paging-model4-20261010`.

## Drive-free-space increment — implemented

After all selected DU sections, DIR prints one `drive: nK FREE` footer per
selected drive, in drive order. This separate footer also serves a single DU;
it avoids implying that user areas have separate space pools. Empty matches
still receive the selected-drive footer. Free space always uses KiB, independent
of `/Z=S`; selected file counts/sizes retain their DU-level meaning.

The transient asks BDOS for each selected drive's live DPB and allocation vector
only after Search Next has finished. A pure shared-source helper counts clear
allocation bits through inclusive DSM, ignores padding bits, and scales by BSH
into a DWORD KiB result. It neither alters the allocation vector nor changes
filesystem metadata. The normal exit restores caller DU; paging also covers
footers, with the existing Ctrl-C restoration path. Early errors and aborts do
not print success footers.

DIR.COM is 7,585 bytes (+204), SHA-256
`8547e20f9ab2581d7f43625e034e0387b4f01b7a1f5c1317ea04f44c59f4eab0`.
BDOS, BIOS, CCP, RCP and other utility binaries are unchanged. Native ZSM4/LINK
output is byte-identical. Focused arithmetic covers 165 cases: empty/full/mixed
vectors, MSB-first order, inclusive DSM, partial final bytes, 65,536 blocks and
DWORD scaling. The test CPU now implements INC (HL)'s zero flag and SLA (HL),
needed to exercise the count and scale instructions accurately.

All 43 existing public z80pack cases pass. Four new drive-summary cases pass
on both z80pack and Model 4. They verify
single DU, several users on one drive, several drives and empty matches, with
exact free counts and no redundant footers. z80pack counts are checked against
cpmtools; Model 4 counts are independently calculated from directory allocation
blocks, including SUBMIT's live command-stream allocation on A0. Model 4 A
uses SYSTEM media and B uses DATA media to match their configured bindings.
Evidence: `/private/tmp/dir-free-z80pack-20261010b` and
`/private/tmp/dir-free-model4-20261010b`.

## Combined implemented-feature qualification — complete

The full 53-case public campaign passes on z80pack and Model 4 with RCP unloaded.
Ten new edge cases combine selectors, duplicate users/leading zeros, terminal
star runs, attribute predicates/display, record units, columns, paging and sort
options. Malformed syntax and invalid superseded options reject the invocation;
empty predicates/matches retain free-space reporting; ordinary invocations reset
all report options. File contents and attributes remain intact.

A separate sixty-file, two-column paging campaign passes on both platforms,
checking the first-page boundary at PG041, Space/Return, ignored keys, Ctrl-C,
caller-DU restoration and next-command reset to four plain KiB columns. No utility
or resident code changes were required. DIR.COM remains 7,585 bytes with the
free-space increment's SHA-256.

See [DIR Qualification.md](<DIR Qualification.md>) for evidence paths, campaign
scope and remaining closure. `/Z=E` is not included: its definition still needs
a decision, implementation and qualification.

## Audit clarifications awaiting resolution

- K/S use allocated KiB/128-byte records; size sorting uses allocated space.
  Proposed E definition: count physical directory entries (decision pending).
- Column layout uses the supported 80-column platform baseline. Narrative rules
  override examples that show three columns or omit always-enabled size. Other
  console widths need a future binding/query and qualification.

## User documentation

The user guide's DIR section contains a polished planned-interface description,
examples and option reference. It distinguishes implemented selection and
allocated-KiB reporting from remaining transient reporting options. Date-related placeholders
were removed because dates and wheel metadata are outside this 1.0 contract.
The alternate size-unit definitions remain identified as pending; allocated KiB
is now qualified behavior. Exported
DOCX/PDF manuals are not regenerated in this documentation increment.

## Shared implementation dependency

DU selection and qualifier splitting exist. The attribute predicate compiler
is implemented and connected to public resident/transient DIR and COPY.
It compiles the bounded !/+/comma grammar and attribute
aliases to an eight-state RO/SYS/ARC truth mask. No wheel or date metadata is
interpreted. See COPY Utility.md for shared-parser qualification.

## DIR.COM — Complete Transient Command Specification for Work

Please implement transient BetterCP/M `DIR.COM` according to the following specification.

This is the consolidated 1.0 design for `DIR.COM`. It is a strict superset of the already-completed resident DIR and should reuse the shared BetterCP/M DU-selector, bounded-filespec, attribute-qualifier, and resident-to-transient handoff machinery already established elsewhere.

The resident DIR design is **not being reopened**.

---

# 1. Purpose and relationship to resident DIR

Resident DIR remains the small, traditional command:

```text
A0>DIR
A: COPY     COM : CONFIG   COM : DUP      COM : TIME     COM
A: SYSGEN   COM : STAT     COM : SUBMIT   COM : README   TXT
A0>
```

Resident DIR has no sorting, summaries, totals, size display, paging, attribute display, or other extended reporting features.

Transient `DIR.COM` is the richer implementation.

It adds:

- multi-DU selection;
- attribute selection;
- size display;
- optional attribute display;
- sorting;
- adaptive 4/2/1-column presentation;
- explicit column control;
- paging;
- file-count/size/free-space summaries.

Advanced syntax encountered by resident DIR should hand off to `DIR.COM` using the common force-transient mechanism.

---

# 2. Basic syntax

General form:

```text
DIR [options] [filespec[qualifiers]]
```

Examples:

```text
DIR
DIR *.COM
DIR B7:*.COM
DIR B[-]:*.COM
DIR [A0,B[3-5],C[4,5,9],5]:*.COM
DIR B2:*.COM[$ARC]
DIR /A /S=Z- B2:*.COM[$ARC+!$SYS]
```

Options are free-standing command-wide switches.

Bracketed qualifiers are attached to the file operand and qualify the selected files.

---

# 3. Shared DU/location-selector syntax

Use the already-implemented common DU selector parser.

Examples include:

```text
B7:
B[3-5]:
B[5,7,11]:
B[4-]:
B[-]:
[A0,B7,C3]:
[A0,B[3-5],C[4,5,9],5]:
```

Semantics follow the existing shared implementation.

Examples:

```text
B[-]:
```

means all user areas on B:.

```text
[A0,B[3-5],C[4,5,9],5]:
```

selects the DUs represented by those terms according to the already-frozen shared DU-selection rules.

Do not create a DIR-specific location parser.

Use the common bitmap representation and iterator.

The complete invocation must be validated before output begins.

---

# 4. Filespec matching

Use the shared BetterCP/M bounded wildcard grammar already used by DIR/COPY.

Relevant examples:

```text
*.COM
FOO.*
F?*.DAT
F.??*
F***.DAT
```

Terminal `*` fills the remainder of its filename field.

Repeated terminal stars collapse.

Examples that remain invalid include embedded/nonterminal-star constructions such as:

```text
F*A.DAT
F**?.DAT
B*C*.DOC
F.*A
```

Default filespec is:

```text
*.*
```

---

# 5. Attribute selectors

The old DIR-specific `/A=...` filtering proposal is retired.

File attributes are selected using bracketed operand qualifiers.

Examples:

```text
DIR *.*[$SYS]
DIR *.COM[$RO]
DIR *.COM[$ARC]
DIR *.COM[$ARC+!$SYS]
DIR *.DOC[$RO,$SYS]
```

Canonical 1.0 attribute vocabulary:

```text
$SYS
$DIR
$RO
$RW
$ARC
```

Historical aliases may also be accepted where the shared parser supports them:

```text
$R/O  = $RO
$R/W  = $RW
```

Underlying relationships:

```text
$DIR = !$SYS
$RW  = !$RO
```

Attribute-expression operators:

```text
!    NOT
+    AND
,    OR
```

Precedence:

```text
! > + > ,
```

Examples:

```text
[$ARC+!$SYS]
[$RO,$SYS]
[!$ARC]
[$SYS+$RO]
```

Do **not** implement wheel-protect selection in DIR 1.0.

F7 has been reserved/established for future wheel semantics, but the wheel byte itself is post-1.0 and is not yet implemented. `DIR.COM` 1.0 should therefore neither interpret nor expose it.

---

# 6. SYS-file default behavior

Plain DIR suppresses SYS files by default.

For example:

```text
DIR
```

does not display files with the SYS bit set.

However, an explicit attribute selector overrides this implicit suppression.

Thus:

```text
DIR *.*[$SYS]
```

must display SYS files.

Likewise:

```text
DIR *.*[$SYS,$RO]
```

must evaluate the user's explicit predicate as written; the default SYS suppression must not silently remove SYS matches.

Conceptually:

> SYS suppression is an implicit default only when the user has not explicitly requested attribute selection that includes SYS files.

---

# 7. Command-wide switches

The complete transient DIR switch set for 1.0 is:

```text
/A
/P
/Z[=K|S|E]
/C=1|2|4
/S=N[+|-]
/S=T[+|-]
/S=Z[+|-]
/S=U
```

No date-related switches or sorting are included in 1.0.

Date stamping has not yet been implemented in BetterCP/M, so all previously discussed date display/filter/sort functionality is explicitly out of scope.

---

# 8. `/A` — display attributes

Syntax:

```text
/A
```

No argument.

Displays the fixed three-character attribute field:

```text
SRA
```

Positions are:

```text
S   SYS
R   Read Only
A   Archive
```

A clear bit is represented by `-`.

Examples:

```text
---    no displayed attributes set
-R-    read-only
S-A    system + archive
SRA    all three
```

Example listing:

```text
COPY     COM   6K  --A
CONFIG   COM   4K  -R-
SYSGEN   COM   7K  S-A
SYSTEM   COM  12K  SRA
```

`RW` and `DIR` are not separate display positions because they represent the clear states of RO and SYS respectively.

Repeated `/A` is harmless.

Do not reserve a visible fourth position for wheel in 1.0.

---

# 9. `/Z` — size display

Syntax:

```text
/Z
/Z=K
/Z=S
/Z=E
```

`/Z` and `/Z=K` are equivalent.

Meanings:

```text
K    allocated kilobytes
S    allocated sectors/records
E    extents
```

K is the default size representation.

Examples:

```text
DIR
DIR /Z
DIR /Z=K
```

all use K for size reporting.

```text
DIR /Z=S
```

uses sector/record units.

```text
DIR /Z=E
```

uses extents.

If several `/Z=` options occur, the last one wins:

```text
DIR /Z=K /Z=E
```

means extents.

Per-file size and the selected-file `TOTAL` should use the same chosen size representation.

---

# 10. Default size display

Transient DIR displays file size by default.

Typical default output:

```text
A0>DIR
A: CONFIG   COM   4K : COPY     COM   6K : DUP      COM   5K
A: README   TXT   1K : STAT     COM   8K : SUBMIT   COM   2K
A: SYSGEN   COM   7K : TIME     COM   3K
8 FILES, 36K TOTAL, 116K FREE
A0>
```

This is intentionally richer than resident DIR.

Resident DIR remains unchanged.

---

# 11. `/S=` — sorting

Transient DIR defaults to **name sort ascending**.

Thus:

```text
DIR
```

and:

```text
DIR /S=N
```

are equivalent in sorting behavior.

Supported sort keys:

```text
/S=N      name
/S=T      file type / extension
/S=Z      size
/S=U      unsorted/native directory order
```

For `N`, `T`, and `Z`, an optional suffix specifies direction:

```text
+    normal/forward/ascending
-    reverse/descending
```

Omitting the suffix is equivalent to `+`.

Examples:

```text
/S=N
/S=N+
/S=N-
/S=T
/S=T-
/S=Z
/S=Z-
```

Therefore:

```text
DIR /S=N
```

and:

```text
DIR /S=N+
```

are equivalent.

Example:

```text
DIR /S=Z-
```

lists largest files first.

---

# 12. `/S=U` — unsorted/native order

Syntax:

```text
/S=U
```

This suppresses sorting and preserves native CP/M directory/search order.

`U` means unsorted.

Do not define:

```text
/S=U+
/S=U-
```

There is no need for reverse directory order.

---

# 13. Repeated sort options

Exactly one sort mode is active, but multiple sort options are not an error.

The **last one wins**.

Example:

```text
DIR /S=N /S=Z-
```

means:

```text
/S=Z-
```

This rule is deliberate and intended to be friendly to SUBMIT files and constructed command lines.

Do not abort merely because an earlier sort option is superseded later.

The same last-value-wins rule applies to value-bearing `/Z=` and `/C=` switches.

---

# 14. Sort tie-breaking

The user selects only one primary sort key.

Do not expose compound multi-key sorting in 1.0.

Implementation may use a deterministic internal tie-breaker, preferably filename/name+type, where needed to make output stable.

That tie-breaker is not a user-selectable secondary sort.

---

# 15. `/C=` — explicit column count

Syntax:

```text
/C=1
/C=2
/C=4
```

Without `/C=`, DIR automatically selects the greatest column count in which the requested fields fit cleanly.

Only these column counts are supported:

```text
1
2
4
```

Examples:

```text
DIR
```

may choose four columns.

```text
DIR /A
```

may still choose four columns if attributes fit.

```text
DIR /C=1
```

forces one column even if more would fit.

```text
DIR /C=2
```

forces two columns if two columns fit.

---

# 16. Column-fit rule

Automatic layout is based on actual rendered width, not simplistic feature rules.

For example, attributes alone may still fit in four columns:

```text
COPY    COM --A CONFIG  COM -R- SYSGEN  COM S-A SYSTEM  COM SRA
```

But combinations such as size plus attributes may require fewer columns.

General rule:

> Unless the user explicitly requests a column count, DIR uses the greatest supported number of columns that fits the selected fields within the terminal width.

Try, in order:

```text
4
2
1
```

Use the first that fits.

If the user explicitly requests a column count greater than the maximum that can fit, report an error.

Do not silently reduce an explicit `/C=` request.

Repeated `/C=` values use the last one.

---

# 17. Output formatting

The traditional CP/M-style filename presentation should remain recognizable.

Without attribute display:

```text
A: COPY     COM   6K : CONFIG   COM   4K : DUP      COM   5K
A: STAT     COM   8K : SUBMIT   COM   2K : SYSGEN   COM   7K
```

With `/A`, when width permits:

```text
COPY    COM --A CONFIG  COM -R- SYSGEN  COM S-A SYSTEM  COM SRA
```

For narrower column counts, align fields cleanly.

Example one-column form:

```text
COPY     COM    6K  --A
CONFIG   COM    4K  -R-
SYSGEN   COM    7K  S-A
SYSTEM   COM   12K  SRA
```

The formatter should derive its layout from the active fields and requested/automatic column count.

---

# 18. `/P` — paging

Syntax:

```text
/P
```

Paging is off by default.

When `/P` is active, pause after a screenful of output.

At the paging prompt:

```text
SPACE
RETURN
```

continue to the next page.

```text
^C
```

aborts the listing cleanly.

Repeated `/P` is harmless.

The paging mechanism should count actual emitted lines and should not corrupt DU restoration or leave DIR state altered after abort.

---

# 19. Summary line — single DU

Transient DIR displays a compact summary after the listing.

Example:

```text
8 FILES, 42K TOTAL, 116K FREE
```

For a filtered listing, `FILES` and `TOTAL` refer only to the files actually selected/listed.

`FREE` is the free space on the drive.

Example:

```text
A0>DIR *.COM
A: CONFIG   COM   4K : COPY     COM   6K : DUP      COM   5K
A: STAT     COM   8K : SUBMIT   COM   2K : SYSGEN   COM   7K
A: TIME     COM   3K
7 FILES, 35K TOTAL, 116K FREE
A0>
```

Use singular grammar where appropriate:

```text
1 FILE
```

rather than:

```text
1 FILES
```

---

# 20. Multi-DU output

When a DU selector selects multiple directories, do **not** merge all files into one global listing for 1.0.

List one DU at a time.

Example conceptually:

```text
DIR [A0,B[3-4]]:*.COM
```

produces separate sections for:

```text
A0
B3
B4
```

Sorting applies independently within each DU.

Do not implement a global cross-DU sort in 1.0.

Do not prepend the DU to every filename merely to construct a merged listing.

That can remain a possible future enhancement.

---

# 21. Multi-DU headings

Each selected DU should be clearly identified before its listing.

Example:

```text
A0:
A: CONFIG   COM   4K : COPY     COM   6K
2 FILES, 10K TOTAL

B3:
B: LINK     COM  10K : ZSM4     COM  12K
2 FILES, 22K TOTAL
```

The exact cosmetic spacing may be adjusted to fit the formatter, but the user must always be able to tell which DU the following listing belongs to.

---

# 22. Multi-DU summaries and free space

File count and selected-file size are DU-specific.

Free space is a **drive property**, not a user-area property.

Therefore, when several user areas on the same drive are listed, do not redundantly print the same free-space value after every DU.

Example:

```text
B3:
B: FOO      COM   6K : BAR      COM   8K
2 FILES, 14K TOTAL

B4:
B: TEST     COM   4K : UTIL     COM   7K
2 FILES, 11K TOTAL

B: 25K SELECTED, 94K FREE
```

If several drives are selected, produce the corresponding drive-level free-space summary for each drive.

The exact wording may be kept compact, but the distinction must remain:

```text
DU-level:
    file count
    selected size

drive-level:
    free space
```

Do not imply that B3 and B4 have independent free-space pools.

---

# 23. No matching files

For a single-DU search with no matches, retain the familiar diagnostic:

```text
NO FILE
```

For multi-DU selection, do not let one empty DU prevent later selected DUs from being processed.

A DU with no matches may report:

```text
NO FILE
```

for that DU and continue to the next selected DU.

---

# 24. Defaults

Transient `DIR.COM` defaults are:

```text
filespec             *.*
SYS visibility       hidden
sort                  name ascending
size display          K
attribute display     off
paging                off
column count          automatic maximum fitting
summary               on
```

Thus plain:

```text
DIR
```

means approximately:

```text
DIR *.*
```

with:

- SYS hidden;
- name sorting;
- K size display;
- no attribute field;
- no paging;
- automatic 4/2/1-column selection;
- summary.

---

# 25. Switch parsing and repetition

Switches are case-insensitive.

Repeated standalone switches are harmless:

```text
/A /A
/P /P
```

Repeated value-bearing switches use the last value:

```text
/Z=K /Z=E
```

means E.

```text
/C=4 /C=1
```

means one column.

```text
/S=N /S=Z-
```

means reverse size sort.

Unknown switches or malformed values are syntax errors.

Examples:

```text
/C=3
/Z=X
/S=Q
/S=U-
```

are invalid.

---

# 26. Interaction between sorting and size units

Size sorting is independent of how size is displayed.

For example:

```text
DIR /Z=E /S=Z-
```

means:

- display size in extents;
- sort by file size descending.

The sort should use the actual file-size metric, not formatted string comparison.

---

# 27. Attribute selector vs attribute display

These are separate concepts.

Example:

```text
DIR *.COM[$ARC]
```

selects ARC files but does not necessarily display the `SRA` field.

Example:

```text
DIR /A *.COM
```

displays attributes for all matching visible files.

Example:

```text
DIR /A *.COM[$ARC]
```

both:

- selects files having ARC;
- displays the `SRA` field.

Do not make `/A` implicitly mean `[$ARC]` or vice versa.

---

# 28. Future wheel attribute

BetterCP/M has reserved/established F7 for the future wheel-protect attribute.

However:

- the wheel byte is not implemented in 1.0;
- wheel semantics are post-1.0;
- DIR 1.0 must not expose `$WHL`;
- DIR 1.0 must not display a `W` position;
- DIR 1.0 should not interpret F7 as active file metadata.

The 1.0 attribute display is therefore exactly:

```text
SRA
```

not `SRAW`.

Future wheel support can extend this later without changing the existing three positions.

---

# 29. No date support in DIR.COM 1.0

Explicitly omit:

- date display;
- date sorting;
- date filtering;
- timestamp-format options.

Do not reserve implementation complexity for this now.

Date functionality may be added later if/when BetterCP/M has a defined timestamp architecture.

---

# 30. No general query language in `[...]`

The bracket mechanism is the general operand-qualification container, but for DIR 1.0 its practical defined use is file attributes.

Do not expand it into a generic expression system such as:

```text
[SIZE>32K]
[DATE>...]
```

Size/date-type filtering, if ever added, belongs in command-level functionality and should be designed separately.

Keep this implementation bounded.

---

# 31. Resident/transient handoff

Resident DIR remains the common subset.

If the invocation requires transient functionality, resident DIR should hand off through the common force-transient mechanism.

Examples likely requiring transient DIR include:

```text
DIR /A
DIR /S=Z-
DIR /P
DIR /C=1
DIR B[-]:*.COM
DIR [A0,B[3-5]]:*.COM
DIR *.COM[$ARC]
```

Conceptually, handoff should behave as though the command were reinvoked with the force-transient prefix.

No duplicated loader/search path should be introduced.

Explicit user force-transient syntax remains available independently.

---

# 32. Implementation structure

Where practical, reuse existing shared BetterCP/M components for:

- DU/location selector parsing;
- DU bitmap iteration;
- bounded filespec parsing;
- attribute-expression parsing;
- CPX→transient handoff;
- caller DU capture/restoration.

DIR-specific code should focus on:

- collecting matching logical files;
- computing size;
- sorting;
- formatting;
- summaries;
- paging.

---

# 33. File collection and logical-file handling

As resident DIR already does, multiple directory extents belonging to the same logical file must be represented once in the user-visible listing.

Transient DIR must aggregate whatever directory metadata is required to determine:

- one logical filename;
- selected size representation;
- displayed attributes;
- sort key.

Do not list each extent as though it were a separate file.

---

# 34. Validation and side effects

DIR is read-only.

Nevertheless, validate the complete invocation before beginning the listing where practical.

On exit, error, paging abort, or `^C`:

- restore caller DU/context;
- leave no persistent directory/user selection changes;
- do not alter file attributes or directory entries.

---

# 35. Qualification expectations

Please test at minimum:

### Basic compatibility

```text
DIR
DIR *.COM
DIR B7:
DIR B7:*.COM
```

### DU selectors

```text
DIR B[-]:*.COM
DIR B[3-5]:*.COM
DIR [A0,B[3-5],C[4,5,9],5]:*.COM
```

### Attributes

```text
DIR *.COM[$ARC]
DIR *.*[$SYS]
DIR *.*[$ARC+!$SYS]
DIR /A *.COM
DIR /A *.COM[$RO]
```

### Sorting

```text
DIR /S=N
DIR /S=N-
DIR /S=T
DIR /S=T-
DIR /S=Z
DIR /S=Z-
DIR /S=U
DIR /S=N /S=Z-
```

Confirm final example uses `Z-`.

### Size formats

```text
DIR /Z
DIR /Z=K
DIR /Z=S
DIR /Z=E
DIR /Z=K /Z=E
```

Confirm `/Z` = `/Z=K`, and last value wins.

### Columns

```text
DIR /C=1
DIR /C=2
DIR /C=4
DIR /A /C=4
```

Test both valid and width-invalid explicit requests.

### Paging

```text
DIR /P
DIR /P /A
```

Test continuation and `^C`.

### Multi-DU summaries

Use multiple users on one drive and multiple drives to verify:

- separate DU listings;
- DU file/size subtotals;
- free space not redundantly treated as per-user;
- correct drive-level free-space reporting.

### Error cases

```text
DIR /C=3
DIR /Z=X
DIR /S=Q
DIR /S=U-
```

and malformed DU/filespec/attribute expressions.

---

# 36. Scope boundary

Do **not** add any of the following unless implementation uncovers a compelling existing requirement:

- date support;
- wheel support;
- global merged multi-DU listing;
- global cross-DU sort;
- multi-key sort;
- generic bracket query language;
- extra display metadata beyond name, size, and `SRA`;
- new persistent system state;
- BDOS growth solely for DIR.

The goal is a capable but bounded `DIR.COM`, not a general database/query utility.

---

## Final command-language summary

```text
DIR [options] [du/filespec[attribute-expression]]
```

Options:

```text
/A              show SRA attributes
/P              page output

/Z              size in K
/Z=K            size in K
/Z=S            size in sectors/records
/Z=E            size in extents

/C=1            one column
/C=2            two columns
/C=4            four columns
                 omitted -> maximum fitting count

/S=N[+|-]       name sort
/S=T[+|-]       type sort
/S=Z[+|-]       size sort
/S=U            unsorted/native directory order
```

Defaults:

```text
SYS hidden
name ascending
size in K
attributes hidden
paging off
automatic maximum-fitting columns
summary on
```

Representative example:

```text
DIR /A /S=Z- [A0,B[3-5],C[-]]:*.COM[$ARC+!$SYS]
```

Meaning:

> Search the selected DUs for `.COM` files whose ARC bit is set and SYS bit is clear; display the `SRA` attribute field; sort each DU's results by size descending; use the widest valid column layout; show per-DU totals and appropriate drive free-space summaries.
