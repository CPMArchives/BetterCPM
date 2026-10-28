# BetterCP/M PATCH.COM 1.0 — Engineering Specification

**Status:** Implemented development candidate; native/cross and cpmsim qualification recorded separately; Model 4 qualification pending\
**Target:** BetterCP/M Utilities Disk, CP/M 2.2-compatible Z80 environment\
**Implementation authorization:** Maintainer instruction after PR #536 merged; see [implementation and qualification notes](PATCH-Implementation.md)\
**Historical DRI patch translations:** Separate project; not part of the PATCH parser\
**Repository review:** 2026-10-28; functional design retained, with the integration assessment in Section 11

## 1. Purpose and scope

PATCH.COM applies a file of verified, fixed-offset binary replacements to an input file, producing a separate patched output file. It is noninteractive except for output-file collision handling and associated filename entry. The original input file is never modified. PATCH is not a binary editor, assembler, DDT interpreter, text-diff applicator, or disk-track patcher.

PATCH supports multiple changes per operation. Every expected original byte is verified against the *unmodified input* before any output file is created. Replacements never insert or delete bytes, so the output retains the input's CP/M logical-record length.

## 2. Invocation

```text
PATCH patchfile [ /INPUT=filespec ] [ /OUTPUT=filespec ] [ /VERBOSE ]
PATCH /HELP
PATCH /VER
```

The patch file may contain `INPUT` and `OUTPUT` directives. Command-line switches override those directives independently. Both resolved filenames must be known before patching begins; a missing name is an error. Each filespec names exactly one ordinary CP/M file, optionally with a single BetterCP/M DU qualifier. Reject wildcard names and expanded DU lists or ranges. Resolve unqualified names using the caller's original current drive/user; do not let changes of working DU affect resolution. The patch instruction file also resolves to a single file.

`/HELP` and `/VER` follow the project's established utility identity/help conventions. Option names are case-insensitive. Unknown, malformed, duplicate conflicting, or missing-value options are errors. A patch file is the sole positional operand.

**Implementation review:** Match the exact existing BetterCP/M single-DU parser, `/HELP`/`/VER` precedence, and utility revision reporting. Do not introduce new global command-line semantics.

Controlling repository contracts are [extended DU syntax](208%20Extended%20DU%20Syntax.md), [utility help](../../specifications/UTILITY-HELP.md), [utility versioning](../../specifications/UTILITY-VERSIONING.md), [component revision tracking](../../specifications/COMPONENT-REVISION-TRACKING.md), [visual identity](../../specifications/VISUAL-IDENTITY.md), and the [interactive prompt convention](Interactive%20Prompt%20Convention.md). Exact `/HELP` or `/VER` tokens ignore other arguments; `/HELP` wins when both occur. Query paths return before file access or drive/user/DMA inquiries or changes. This does not make `/VERBOSE` a `/VER` query.

## 3. Native patch-file language

Example:

```text
; BetterCP/M PATCH file
; Format: OFFSET: OLD -> NEW

INPUT  PROGRAM.COM
OUTPUT PROGRAM.NEW

0120: CD 05 00 C9 -> 00 00
0122: 00 C9       -> 3E 02
02A4: 3E 01 15    -> 3E 02
```

- Each physical line is at most **255 characters**, excluding its CR/LF terminator. Reject longer lines without truncation.
- Blank lines are ignored. A semicolon starts a comment, either on its own line or following a statement. The two-line explanatory header is recommended, not required.
- `INPUT` and `OUTPUT` directives are case-insensitive. Their operands are single filespecs. Each directive may appear at most once; duplicate directives are errors.
- Offsets are unsigned hexadecimal absolute **file byte offsets**, not DDT load addresses. An optional trailing `H`/`h` is permitted. Without a suffix, the value remains hexadecimal.
- `OLD` and `NEW` are nonempty sequences of exactly two-digit hexadecimal bytes, case-insensitive, separated by spaces or tabs. No partial bytes, wildcards, escape sequences, decimal byte values, or implicit padding.
- Whitespace may appear around the colon and arrow and at line beginnings/endings. The replacement operator is the two-character ASCII token `->` and means **OLD is verified, then NEW replaces the leading bytes**.
- The parser shall reject malformed syntax with the patch filename and physical line number before creating an output.
- Patch instruction count is not arbitrarily capped; process with bounded RAM and multiple passes as necessary.

The patch file is read as CP/M logical records. CR/LF is the normal line terminator; support bare CR and bare LF for portability. A conventional trailing `1Ah` may terminate the *textual instruction file*; this does not change binary input/output semantics. Reject embedded NUL and unsupported control characters in statements. The implementation accepts these line endings, counts CRLF once, and rejects embedded NUL/unsupported controls before textual EOF. After a `1Ah`, only `00h` or `1Ah` record padding is accepted; other trailing bytes are an error. These text rules never apply to the binary input/output.

## 4. Replacement semantics

For a patch at offset `O`, let `E` be the expected-byte sequence and `R` the replacement-byte sequence:

```text
1 <= length(R) <= length(E)
```

All bytes in `E` must match the original input at offsets `[O, O+length(E))`. Only `[O, O+length(R))` is modified; any additional expected bytes are verification context and remain unchanged. Every modified byte therefore has a verified corresponding original byte. The verification range must be wholly within the input file; no patch may extend beyond EOF. Arithmetic overflow is an error.

All expected-byte checks use the original input, not the output of preceding patch statements. Patch statement order has no semantic effect. Verification ranges may overlap, including overlaps with another statement's write range. **Modification ranges must not overlap**, even if the replacement values agree. Duplicate writes are rejected. Reject the entire patch on any mismatch or overlap, before creating any output.

Illustration: the first two changes below are permitted and produce the same result as the third line by itself:

```text
0120: CD 05 00 C9 -> 00 00
0122: 00 C9       -> 3E 02

; equivalent output effect, not an additional instruction:
0120: CD 05 00 C9 -> 00 00 3E 02
```

Do not combine all three as one patch: the third overlaps the earlier modification ranges.

## 5. Input and output protection

Resolve and canonicalize input, output, and patch-file identities by drive, user and 8.3 name. Reject an output identical to either the original input or the patch instruction file, including aliases arising from explicit versus inherited DU notation. Never modify the input or patch file.

If the output does not exist, create it only after complete syntax validation, verification of every expected byte, and detection of all overlapping modification ranges. Copy every input logical record, applying the replacements. Preserve all record bytes including `1Ah`, unused final-record bytes, and other apparent padding. Never infer a text EOF or strip bytes.

If the output exists, prompt **after all patch validation**:

```text
PATCH: PROGRAM.NEW exists.
Overwrite? (y/N/r/?)
```

- `Y`/`y`: authorize staged replacement of the existing output.
- `N`/`n` or Enter: abort without changes.
- `R`/`r`: request a new single-DU output filename; revalidate identities and existence, repeating the prompt if necessary.
- `?`: display `Y Yes, N No (abort), R Rename, ? Help` and repeat the prompt.

No `Q` choice is needed; No already aborts. Other keys reprompt with no destructive action. The default is **No**.

Following the common interactive prompt convention, help and invalid-response reprompts repeat the resolved destination DU/name as well as the original choices. Repeated `?` changes no files, counters, authorization or transaction state. The example above abbreviates the destination; diagnostics must distinguish destinations on different DUs.

For authorized overwrite, use a **same-DU staged replacement with backup**:

1. Allocate a collision-free temporary output filename on the destination DU, without overwriting any existing file.
2. Construct the complete patched copy in that temporary file, close it successfully, and perform mandatory full-output byte-for-byte verification.
3. Rename the existing destination to a distinct, collision-free backup name on the same DU. If this fails, leave the existing destination unchanged and clean up the temporary output where safe.
4. Rename the verified temporary output to the requested destination name. If this fails, attempt to restore the original destination name from the backup. If restoration also fails, **retain the backup** and report its exact DU-qualified filename, together with the state/name of the staged file.
5. Delete the backup **only after** the new destination is installed successfully. If backup deletion fails, report success with a prominent warning and the exact retained backup filename; never silently delete or overwrite it later.

If the requested output does not exist, create the output only after successful preflight; it must still be fully written and verified before reporting success. If creation, writing, closing, or verification fails, delete the incomplete output where possible and explicitly report any cleanup failure. A failed operation must never describe an incomplete file as successfully patched.

The replacement is **not atomic** under CP/M 2.2. A power failure between backup and installation may leave the requested destination name temporarily absent; the backup and/or staged file may remain. No recovery guarantee is made for nonreturning BDOS/BIOS errors or power loss. Temporary and backup filenames must never collide with input, patch file, destination, or existing files; allocate without destructive replacement. A staged overwrite may require disk space for an additional full copy of the destination.

## 6. Verification, execution and reporting

The implementation must use a **preflight phase** to parse the complete patch and verify all expected bytes against the original input before any output creation. Bounded-memory implementation may reread the patch file and input as necessary. The patch file should be checked for consistency across passes; do not silently apply a different patch from the one verified.

The output stage copies the complete input, applying only approved replacements. Recheck expected bytes while copying where practical to detect input changes between phases; any mismatch is a failure, not a successful patch. **Full-output verification is mandatory**: after closing the completed output or staged file, reread it and compare every byte against the original input with the approved replacements applied conceptually. This verifies both modified and untouched regions, not merely the replacement positions or a checksum. Verification must use the same authoritative patch instructions as preflight; changes to the patch file between passes must be detected or prevented. No `/NOVERIFY` switch exists in 1.0. Readback is an application-level check, not a guarantee against dishonest or volatile storage caches.

`/VERBOSE` is an approved, case-insensitive option in addition to `/INPUT=`, `/OUTPUT=`, `/HELP` and `/VER`. In normal mode, report the first preflight validation failure with the patch filename, physical line number where applicable, byte offset, and expected/found bytes as relevant; then abort without creating output. With `/VERBOSE`, show each patch instruction and its validation result and continue checking independently identifiable mismatches **without applying changes**. Where malformed syntax prevents safe resynchronization, stop rather than fabricate diagnostics. If any validation fails, abort without creating output in either mode. Errors are always reported regardless of `/VERBOSE`; the switch controls diagnostic detail, not whether errors are visible.

A concise successful summary shall identify input, output, instruction count, bytes written, bytes actually changed, and full-output verification status. Count *changed bytes* as positions whose final value differs from the original; it may be less than the number written. `/VERBOSE` additionally reports per-instruction offsets, expected and replacement bytes, and validation results. Do not require storing the complete instruction list in RAM merely for verbose display.

For errors, identify the patch filename and line number for syntax, duplicate, overlap and expected-byte mismatch problems; include offsets and expected/actual values where practical. Report missing files, read errors, output-space exhaustion, write failures, readback mismatches, rename failures and cleanup failures distinctly. Never report a partially written output as successful. A failed preflight creates **no output at all**; do not offer to retain a partially patched file, because no such file exists at that stage. After a write-stage failure, best-effort cleanup applies as specified in Section 5.

## 7. CP/M implementation constraints

- Use ordinary CP/M 2.2-compatible BDOS services and the established BetterCP/M utility build/version conventions.
- Operate in bounded TPA without whole-file or whole-patch storage. Multiple sequential passes are acceptable.
- Preserve the caller's drive/user and other owned state on all handled exits. Keep FCBs, DMA and directory enumeration state distinct.
- Support files and offsets beyond 64 KiB without wrap; detect overflow of offsets, lengths, line numbers and counts.
- Use no terminal-specific escape sequences or monitor-specific service for prompts.
- Handle actual floppy disk I/O failures honestly. A nonreturning BIOS/BDOS fatal error cannot be promised to permit cleanup.
- Do not assume an atomic rename/replace operation, disk journaling, or POSIX-like process exit status.

## 8. Explicit exclusions and historical DRI work

PATCH.COM 1.0 does **not** directly read Digital Research patch notices, DDT transcripts, debugger commands, assembly source patch files, Unix `diff` patches, or DOS DEBUG scripts. It does not patch system tracks or in-memory code, search for byte patterns, insert/delete bytes, or provide interactive undo/redo.

A **separate accompanying historical package** may translate selected DRI corrections into native BetterCP/M `.PAT` files. Each translation must identify its original notice, exact target executable/version, verified original bytes, and replacement bytes. Source-level or machine-specific patches that cannot be represented as fixed-offset replacements are excluded. The package has independent qualification; it must not delay or expand PATCH.COM's core parser.

## 9. Qualification and acceptance

At minimum, test:

1. Valid and invalid invocation forms, override precedence, caller-DU inheritance, wildcard/range rejection, `/HELP` and `/VER` conventions.
2. Blank lines, full-line and inline comments, whitespace, optional `H`, lowercase hex, 255-character boundary, malformed lines and line-numbered errors.
3. Multiple patches, unequal OLD/NEW lengths, unchanged context bytes, independent verification against original input, and order independence.
4. Overlapping verification permitted; overlapping or duplicate write ranges rejected before output creation.
5. Mismatches at first/last byte, patches spanning 128-byte records and 64-KiB boundaries, offset beyond EOF, and arithmetic overflow.
6. Exact preservation of input length, `1Ah`, final-record padding, and all unmodified bytes.
7. Output identical to input or patch file under alternate DU spellings rejected.
8. Existing-output `Y`, `N`, Enter, `R`, `?`, invalid keys; default No and repeated rename conflicts.
9. Staged overwrite success; insufficient space; temporary name collisions; failed write, full-output readback, rename, backup restoration and cleanup; explicit surviving-backup/staged-file diagnostics and backup-deletion warnings.
10. Large patch files exceeding available RAM, large input files, many instructions and wide counters.
11. Successful totals: instructions, bytes written, bytes actually changed; mandatory complete byte-for-byte output verification; no false success after errors. Normal first-error abort versus `/VERBOSE` multi-mismatch reporting, both with no output creation.
12. Native build parity and execution on supported BetterCP/M targets using disposable test media.

## 10. Implementation qualification and repository integration

The functional choices of `/VERBOSE`, mandatory full-output byte-for-byte verification, and same-DU staged overwrite with backup and best-effort restoration are **approved**, not open questions. Work shall implement these behaviors rather than substitute a simpler write or verification scheme.

Before qualification, inspect the current repository conventions for `/HELP` and `/VER` precedence, command option parsing, single-DU filename resolution, version/revision metadata, and textual patch-file EOF handling. Confirm actual target TPA, buffer and stack budgets, temporary/backup name allocation, and BDOS rename/error behavior. These are implementation audits, not permission to alter the approved semantics. If an established repository constraint prevents compliance, report the conflict for review before changing the contract.

Do not implement direct DRI/DDT/ASM import in PATCH.COM. Historical DRI corrections will be separately translated into verified native `.PAT` files and may be distributed alongside PATCH.COM after independent qualification.

**Release status:** Development implementation and candidate-media inclusion are recorded in [PATCH-Implementation.md](PATCH-Implementation.md). Full paired-platform qualification and release acceptance remain pending; this functional contract is not a release receipt.


## 11. Repository assessment — 2026-10-28

The core design is suitable for implementation on the existing utility framework.
Its preflight rule, separate immutable input, disjoint write ranges, mandatory
complete readback and explicit backup recovery give it a precise and testable
contract. The shorter replacement rule is consistent: trailing OLD bytes verify
context without becoming writes. Do not reinterpret it as padding, insertion or
a chained edit against earlier replacements.

The Utilities manual entry is maintained in
[patch_manual_entry.md](../user/patch_manual_entry.md) and embedded in the
[Utilities manual](../user/utilities_manual.md#patch-verified-binary-file-patching).
The approved source document was supplied as
`BetterCPM_PATCH_Engineering_Specification_v1.0(1).md`.

### Implementation policy defaults

The following review recommendations were adopted as implementation defaults
when development was authorized after PR #536. They add no switches or actions.

| Detail | Behavior |
| --- | --- |
| Ctrl-C during processing, collision prompts and rename entry | Cancel at safe boundaries, restore caller state and apply handled-failure cleanup. Do not poll between backup/install/restore recovery steps. Report cancellation without a completed-patch claim. |
| No replacement statements | Reject before output creation. A nonempty patch writing identical bytes is valid and reports zero changed bytes. |
| Existing read-only or system output | Refuse replacement without clearing protection or adding override switches. Check again before installing. Input/patch data and attributes remain unmodified. |
| New output attributes | Create an ordinary read/write, directory-visible file. Do not copy input or old-output attributes to the new file. |

### Implementation audits and qualification details

- Apply the instruction-text EOF/control rules in Section 3. Test non-padding
  bytes after `1Ah` as errors and CRLF as one physical line terminator. Never apply text EOF handling to
  binary input or output.
- Define wide numeric representation and limits from CP/M 2.2 random-record
  addressing, not from a 16-bit file offset. Bounds must be checked before
  arithmetic wraps. A representation limit is distinct from an arbitrary
  instruction-count cap.
- Document how instructions remain authoritative across passes and how input
  changes are detected. Rereading only the current patch cannot establish that
  it is the patch verified earlier. Do not weaken the preflight/readback contract
  merely to reuse an existing checksum routine.
- Measure worst-case pass counts and floppy I/O for unsorted instructions,
  overlapping context and a patch larger than TPA. A bounded-memory multi-pass
  design may trade speed for storage; retain the uncapped-instruction contract.
- Clarify summary terminology in the implementation design: distinguish total
  output-file bytes from replacement bytes written (sum of NEW lengths), and
  count actually changed bytes separately. Avoid an ambiguous single total.
- Qualify temporary/backup allocation, returned BDOS failures, destination
  protection and rollback on disposable media. Do not assume ordinary overwrite
  authorization bypasses CP/M protection or that rename is atomic.
- Add component identity, builders, corresponding-source packaging and capacity
  checks during implementation. Register only actual built artifacts and distinguish candidate inclusion from
  release acceptance. The implementation notes record current capacity and
  placement on the NOAH companion volume.
- Obtain PATCH's own native/cross parity and target runtime evidence. Existing
  CRCKSUM/MD5SUM Model 4 deferrals do not automatically waive PATCH qualification.
