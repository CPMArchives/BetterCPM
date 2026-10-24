# DASM Engineering Specification

Status: selected implementation direction, 2026-10-25. Adopt Richard Conn's
DASM 1.5 as a maintained Utilities Disk adaptation. The requirements below
define implementation and acceptance work; they do not claim that a binary
has been integrated, rebuilt with ZSM4 or qualified on either platform.

## 1. Purpose and scope

Provide an interactive Z80 disassembler whose Zilog assembly output can be
rebuilt with the packaged ZSM4 4.7 and Digital Research LINK 1.3. Preserve
the useful RESOURCE-derived workflow: inspect bytes, classify code and data,
create and edit symbols and comments, save analysis, and generate source.
Correct unsafe memory and file operations rather than preserving defects.

The required targets are TRS-80 Model 4/trs80gp and z80pack/cpmsim. Physical
Model 4 results are separately identified; emulator results must not be
represented as physical-hardware qualification. Use the same portable program
on both targets unless a documented platform dependency requires otherwise.

Initial scope includes Zilog output, bounded in-memory analysis, exact
drive/user file selection, safe publication, symbol conversion, and native
round-trip qualification. TDL output may remain available as an optional
build, but is outside the default ZSM4 round-trip contract. Full 64 KiB input
residency, disk-backed analysis paging, control-flow reconstruction, debugger
execution, and Z180/Z280 decoding are outside the first release.

No BIOS/BDOS ABI changes or permanent resident allocations are authorized.
Follow the [distribution manifest](../releases/DISTRIBUTION-MANIFEST.md),
[shared input specification](Shared%20Input%20and%20UI%20Specification.md),
and existing file-access contracts. Preserve DASM's command language where
it does not conflict with explicit corrections in this specification.

## 2. Upstream identity and provenance

Use the original [SIG/M volume 91 distribution](https://ftp.trailing-edge.com/pub/oakcpm2/sigm/vol091/)
as the authoritative import. Its [-CATALOG.091](https://ftp.trailing-edge.com/pub/oakcpm2/sigm/vol091/-catalog.091)
records release on 18 December 1982 and lists DASM.COM, DASM.MAC,
DASMTDL.MAC and DASMZLG.MAC. DASM.MAC identifies Richard Conn, version 1.5,
16 August 1982, derived from Dave Barker's ZZSOURCE and Ward Christensen's
RESOURCE. Do not confuse the source date with the volume release date.

The maintainer accepts SIG/M's public-domain distribution practice as the
basis for redistribution and modification. Preserve that historical basis
explicitly; do not invent a modern SPDX license or represent the blank
[SIG/M contribution template](https://ftp.trailing-edge.com/pub/oakcpm2/sigm/vol091/sig/m.lib)
as Conn's signed submission. Retain inherited credits and relevant notices.
The catalog's SIG/M copyright notice must remain with the catalog.

Before implementation, preserve unmodified upstream files, the volume catalog,
READ.ME and submission template in a clearly identified reference location.
Record retrieval URLs, retrieval date, byte lengths and SHA-256 values in a
machine-readable provenance record. Preserve original bytes separately from
any CRLF, WordStar high-bit or filename normalization. Hash the imported
binary independently; never assume a later ZDASM15.COM is identical.

Maintained sources, build preparation and corrections must be distinguishable
from the reference import. Include original and modified sources, build
instructions, notices and change history with the host release package.
Do not modify synced project files under sources/.

## 3. Identity and command behavior

The adaptation is DASM.COM on the Utilities Disk. Retain Conn's attribution
and upstream 1.5 identity, with an independently identifiable BetterCP/M
adaptation revision. Implement ordinary /HELP and /VER queries without
requiring an input file or creating output. Version output identifies the
adaptation, upstream origin and build revision; it must not alter third-party
ZSM4 or LINK versioning.

Preserve and document list/disassemble, dump, automatic label generation,
symbol insertion/deletion, control-region classification, comments, origin
offset, prologue generation, analysis save/load and orderly exit. Publish a
command compatibility table mapping every upstream command to retained,
corrected, unsupported or deferred behavior. Invalid commands must not mutate
the analysis. Validate all arguments before destructive or persistent action.

Operate through normal console services. No direct Model 4 video-memory or
keyboard access is required. Qualify ordinary line input, backspace, cancel,
pagination and long listings with the normal terminal personalities. Console
abort must stop work predictably and leave files recoverable.

## 4. ZSM4 build compatibility

### 4.1 Build the disassembler

Build from maintained source using the packaged ZSM4 and LINK binaries.
The upstream M80 dialect uses .Z80, ASEG, ORG, INCLUDE, IF1, .PRINTX,
DB/DEFB, DW/DEFW, DS/DEFS and expression operators supported by ZSM4.
This is a source-level finding, not a completed build result.

Retain DASMZLG.MAC and DASMTDL.MAC as the documented include names, or record
an explicit deterministic mapping. Default ZILOG to true and TDL to false;
reject configurations enabling both or neither. Normalize source encoding
only through a reproducible preparation step with original bytes retained.

The build recipe must specify assembler/linker hashes, switches, source and
include locations, absolute placement, entry address, output name and padding.
Require zero assembly errors, no unresolved symbols and no address overlap.
Do not infer success from a COM file's existence or batch continuation.

Keep a historical-baseline rebuild separate from corrected adaptation builds.
If the baseline differs from the archived binary, explain each difference
with source/configuration or padding evidence before using it as a reference.
An unexplained mismatch blocks claims of upstream reproduction, but must not
be hidden by modifying the imported binary.

### 4.2 Assemble generated source

Default output is ZSM4-compatible Zilog source. Emit an explicit .Z80 and ASEG
before the origin, followed by the required EQU definitions and code/data.
Terminate with END. The supported default is absolute reconstruction, not
automatic production of relocatable modules.

Qualify the exact LINK command for absolute output. Document the treatment of
ORG 100H, leading gaps and CP/M record padding. Do not copy a relocatable CSEG
recipe into this workflow without proving the resulting addresses and bytes.
Non-0100H origins require an explicitly qualified output/extraction procedure;
do not describe an arbitrary-origin image as a directly runnable COM program.

Generated numeric literals must be unambiguous to ZSM4, including a leading
zero where a hexadecimal literal would otherwise begin with A through F.
Check quoted apostrophes, empty strings, control bytes, high-bit bytes,
indexed displacements, relative targets, conditions and symbol expressions.
Never allow line wrapping or pagination text into assembly output.

DASM's maximum 12-character symbols match ZSM4's 12 significant source-symbol
characters. Detect collisions under ZSM4 comparison rules, reserved words and
illegal identifiers. Object/export symbol significance is a separate toolchain
setting; do not assume that all 12 characters survive external-symbol export.

Unknown, unsupported, redundant-prefix and noncanonical encodings must have a
literal-byte representation. If a mnemonic would reassemble to different bytes,
emit DB bytes with an explanatory comment. For example, equivalent instruction
encodings must not be silently canonicalized in exact reconstruction mode.

DS denotes an uninitialized region, not a promise to preserve original file
bytes. Exact-file mode emits DB for existing bytes, including zero-filled runs.
An explicit analysis-only BSS choice may use DS but must report that exact
file reconstruction is no longer promised for that range.

## 5. Symbols and conversion

### 5.1 Canonical DASM interchange

Use textual symbol interchange, distinct from REL objects and listings:

```text
0005 BDOS
0100 START
0123 LOOP
```

The canonical writer emits four uppercase hexadecimal address digits, one
space, an uppercase identifier and CRLF. Names contain 1 to 12 characters
legal to both the adaptation and ZSM4. Accept horizontal whitespace and LF
on import; accept a final CP/M 1Ah text terminator and record padding only
after complete records. Reject embedded terminators followed by meaningful
records. Report malformed lines with line numbers; never silently skip them.

First characterize upstream SYMRD/SYMSV/READFILE against fixtures and capture
their actual accepted format. Preserve compatibility with valid upstream SYM
files through a validated reader. Validate entire files before replacing live
symbols; do not load unchecked input over the symbol arena. Export followed
by import must preserve all supported names and values.

Allow multiple names for one address; choose the displayed primary alias
deterministically and preserve the others in interchange. Identical duplicate
records may coalesce with a count. The same normalized name at different
addresses is an error. Never silently truncate or rename an imported symbol.
Handle addresses 0000H and FFFFH without confusing them with sentinels.

### 5.2 ZSM4 and LINK conversion

Provide a native CP/M conversion command so the Utilities Disk workflow does
not require a host. Its final command name is chosen during packaging after
checking namespace and disk-space constraints. Provide a host reference
converter using the same fixtures for reproducibility.

The mandatory conversion input is a supported, explicitly identified
post-link address/symbol report or symbol file from the pinned toolchain.
Before choosing its grammar, capture actual ZSM4/LINK outputs and document
their switches, record layout, pagination and symbol significance. Do not
promise compatibility with an assumed .SYM format merely because the suffix
matches. Identify the input dialect explicitly; ambiguous autodetection fails.

Assembly-listing conversion is optional and must be restricted to known
absolute symbols or supplied link placement. Relocatable CSEG/DSEG/COMMON
offsets are not final addresses. Reject unresolved externals, ambiguous section
locations and reports from failed builds. Do not add 0100H indiscriminately.
Preserve absolute EQU values and aliases. Any excluded symbol must be counted
and explained; silent omission is prohibited.

The native converter streams input with bounded buffers and checks output
through the file publication contract in section 6. It must report imported,
coalesced and rejected records and exit unsuccessfully if required records
cannot be represented. Overlength names or significance collisions require an
explicit user-supplied mapping, retained with the analysis, or rejection.

Acceptance requires a linked multi-module fixture containing code, data,
absolute equates, aliases, long names and unresolved-symbol negative cases.
Import converted symbols into DASM and prove that labels, references and
external equates resolve to the linked addresses. Export them again and compare
the normalized symbol set. No ZSM4/LINK binary modifications are required.

## 6. File access and recoverable publication

### 6.1 Input and identity

Support exact simple drive/user-qualified operands through existing BetterCP/M
services. Resolve and compare full drive, user and 8.3 name identities for every
input, output and scratch file. Do not compare only displayed filename strings.
Prevent source binary, symbol, control, comment and command-input files from
being overwritten by another role in the operation.

Open binary input in record-transparent mode: 00H, 1AH and FFH are ordinary
bytes. CP/M record count does not establish the original host byte length.
Accept an explicit logical length, validate it against readable records, and
record it with the analysis. Without one, treat all physical file-record bytes
as input and state that policy; do not infer length by stripping 1Ah or zeros.

### 6.2 Output state machine

Replace upstream OPEN's erase-before-create behavior. All persistent outputs,
including assembly, SYM, CTL and DOC files and converter output, use:

1. Resolve identities and validate operation, bounds and overwrite choice.
2. Reserve an unused scratch name on the destination drive/user. Create-new
   semantics must prevent a collision from replacing another file.
3. Write the complete staged file, checking every BDOS status and close result.
4. Preserve an existing destination under an unused recovery name, if replacing.
5. Rename the staged file to the requested destination and verify completion.
6. Remove recovery material only after successful publication and according to
   the documented retention policy.

CP/M renames do not provide a multi-file atomic transaction or power-loss
durability. Describe the reachable states truthfully. On failure before step 4,
the old destination remains intact. On failure after step 4, preserve recovery
and staged files and report their exact identities and recovery instructions.
Never erase the only complete copy. Read-only destinations and media must fail
before replacement; do not silently clear attributes.

Interactive source generation is a pending output transaction until explicitly
completed. Ordinary cancellation must not publish a partial source as complete.
If partial output is deliberately retained, identify it explicitly and retain
the existing destination. Restore the default DMA and any changed drive/user
state on every orderly exit and error path.

Saving an entire analysis is a multi-file operation. Publish a small session
descriptor last, containing format version, logical origin/length, binary hash
and identities/hashes of component files. A new session uses unique component
names until the descriptor commits; never overwrite components referenced by
the previous descriptor first. Interrupted saves leave the old session usable.
Legacy separate-file saves remain available with their individual guarantees.

## 7. Memory ownership and input limits

### 7.1 Runtime boundary

Obtain the active transient-memory ceiling from the accepted BetterCP/M runtime
contract at entry. The conventional BDOS operand at 0006H must be interpreted
according to that contract with CPX/RSX modules loaded, not as an unloaded BIOS
constant. Reserve executable/static storage, stack, safety margin, file buffers
and workspaces below the exclusive ceiling before admitting any input.

The [core baseline](../releases/CORE-1.0-BASELINE.md) gives a 54,272-byte
record-aligned COM ceiling before resident modules. That is not DASM's input
capacity or a guaranteed loaded Model 4 TPA. Report the measured runtime bound
and actual available analysis capacity in diagnostics and qualification data.
Additional modules must reduce capacity safely or cause a clean startup refusal.

### 7.2 Workspace design

Replace unchecked fixed partition assumptions. Upstream CTLTBL follows ENDALL;
SYMTAB is CTLTBL+0600H, INITOFF is SYMTAB+2000H, and COMTBL is INITOFF+4000H.
Those expressions do not establish ownership or validate growth. Existing
partial checks are insufficient evidence that all operations are bounded.

Use explicit half-open arenas for control entries, symbols, input bytes,
comments, I/O buffers and stack. Record base, capacity and used length for each.
All insertion, deletion, movement, import, reload and automatic-label paths must
check complete proposed sizes before mutation. Include terminators and temporary
copies. Use overflow-safe arithmetic and checked address-to-buffer translation.
User-entered offsets must never permit writing code, stack, another arena or
resident memory. Read-only inspection of system addresses must not authorize
writes or bypass file-input bounds.

Separate logical Z80 addresses from physical buffer pointers. Use a representation
capable of expressing end-exclusive 10000H and a 65,536-byte length, even though
the first release cannot retain a whole address space in the TPA. Reject logical
ranges crossing the address space unless a separately specified wrap mode exists.
Do not let a logical address plus offset wrap into low memory.

Before reading each record, ensure its entire DMA footprint fits. Use a private
128-byte staging buffer when a final partial logical record would overrun an
arena. An instruction's operand fetch may not read past logical EOF; emit the
remaining bytes literally if the instruction is incomplete.

No unmeasured minimum input capacity is a release claim. Publish a link map,
stack bound, arena allocation table and measured maximum admitted input under
each normal platform configuration. Require useful representative inputs to
pass; set the supported minimum capacity from the measured implementation and
record it before release acceptance. Never silently shrink tables during a
session. Capacity exhaustion leaves the prior valid analysis intact and gives
a recoverable diagnostic. Disk-backed paging requires a later specification.

## 8. Text and analysis preservation

Analysis commands must not modify loaded binary bytes unless an explicitly
documented patch command is selected. Preserve a binary identity and logical
length throughout save/load. A session whose binary differs must require an
explicit rebind and must not silently apply stale address classifications.

Source output uses CRLF and a documented CP/M EOF/padding policy. Preserve
literal bytes through quoting or DB, including apostrophes, semicolons, tabs,
CR/LF, high-bit values and 1Ah. Comments must remain comments; embedded newlines
or control characters in imported annotations must not inject assembly commands.
Reject unsupported annotations with a precise diagnostic or escape them using a
documented reversible form. Validate identifiers separately from comment text.

Retain classification boundaries, symbols, aliases, comments and the selected
origin across a session round trip. Version new session formats and reject
unknown versions without changing the live session. Preserve valid legacy CTL,
SYM and DOC import behavior through explicit compatibility readers and fixtures.

## 9. Round-trip qualification

### 9.1 Byte comparison contract

The core campaign is known input bytes -> DASM analysis/source -> packaged
ZSM4 -> packaged LINK -> reconstructed bytes. Do not execute arbitrary inputs.
Compare every byte in the declared logical interval and verify output length.
Report separately any approved linker record padding; do not broadly trim 00H
or 1Ah, which can be real data. Host references supplement native execution and
must not replace it. Store the generated source, REL, COM, listings, diagnostics,
symbol conversions and comparison report for each case.

### 9.2 Required corpus

| Area | Required cases |
|---|---|
| Base instructions | Every documented opcode with representative operands and all conditions |
| Prefixes | CB, ED, DD, FD and indexed-CB families; positive/negative boundary displacements |
| Exact encodings | Undocumented/unsupported instructions, aliases, redundant/repeated prefixes and literal-byte fallback |
| Branches | Forward/backward JR and DJNZ, range boundaries, external targets, targets inside instructions |
| Address bounds | Origins 0000H, 0100H and high memory; final byte FFFFH; invalid overflowing ranges |
| Data | All 256 byte values, quoted strings, word tables, mixed code/data, embedded 1Ah and noncanonical zeros |
| EOF | Empty input, 1/127/128/129-byte logical lengths, record padding, every truncated instruction length |
| Symbols | Aliases, external equates, 12-character names, illegal/overlength names and significance collisions |
| Analysis | Save/reload symbols, controls and comments; session descriptor commit and binary mismatch |
| Capacity | Exact arena limits, one-byte/one-entry overflow, dense automatic labels, long comments and low TPA |

Generate opcode fixtures from an independently checked specification or tool,
not solely from DASM's own tables. Where the native assembler cannot spell an
encoding, the input fixture and expected output bytes remain authoritative.
Representative real inputs include small utilities, a multi-module linked
program and a larger utility that fits the measured supported capacity.

### 9.3 Platform matrix

Run the corpus on both Model 4/trs80gp and z80pack/cpmsim against frozen System
A: and Utilities B: images, with outputs on writable work media. Record emulator,
BIOS, system image, Utilities image, DASM, converter, ZSM4 and LINK hashes.
Use each platform's normal resident-module configuration; also exercise a reduced
TPA profile and insufficient-memory startup. Report configurations separately.

On both platforms test filename/DU parsing, included source lookup, command-line
and interactive operation, console cancellation, pagination and clean CCP return.
Verify default DMA, user and drive restoration and absence of resident-memory
corruption using canaries or emulator write tracing. Include at least one native
DASM rebuild and one linked-symbol conversion/round trip per platform.

### 9.4 Failure injection

Inject directory full, data disk full, read-only file/media, create failure,
write failure, close failure, both publication renames failing, recovery-name
collision, scratch-name collision and cancellation during output. Interrupt
between each publication state and each session-component publication. Preserve
and inspect disk contents after each case; compare original files byte-for-byte.
Emulated failures do not imply power-loss durability beyond the defined model.

## 10. Implementation order and release gates

1. Freeze provenance and original files; capture historical behavior fixtures.
2. Establish reproducible ZSM4/LINK baseline build and record discrepancies.
3. Implement checked memory ownership and safe input/output before extending use.
4. Implement Zilog output corrections and byte-preserving fallback.
5. Capture actual toolchain symbol formats; implement and qualify conversion.
6. Complete corpus, failure injection and both-platform campaigns.
7. Integrate packaging and manuals; rebuild and accept exact release images.

Release requires a reviewed command table, measured capacities, zero unexplained
round-trip mismatches, passing recovery tests and passing component acceptance
on both platforms. Tests must bind verdicts to artifact hashes. A selected tool,
successful host assembly or historical COM execution alone is insufficient.

Package DASM.COM and the native converter on Utilities, with concise invocation,
limits, origin/length rules, recovery instructions and a complete worked native
example. Include provenance and full source/build companions in the host package.
Final converter and notice filenames are recorded in the distribution manifest
when implemented. Keep pending selections distinct from actual image membership;
do not count this specification as a new qualified binary or update existing
image acceptance hashes without rebuilding and testing those images.

## 11. Required implementation evidence

The implementation change supplies original/adapted source hashes, toolchain
identity, build commands, map and stack analysis, measured arena capacities,
symbol-format fixtures and converter specification, golden round-trip corpus,
failure-state disk evidence, per-platform logs and machine-readable verdicts.
Every unsupported command/encoding and every remaining limit is in the user
documentation. ZSM4 and LINK remain externally versioned tools; the adaptation
does not bring them into BetterCP/M-owned component version numbering.
