# Utility presentation stabilization — 2026-10-30

Status: implemented and regression checked. New release packages and the reduced
Model 4 acceptance checks remain pending. Source identity is the commit containing
this record, based on merged PR #550 (f59c840). Historical Model 4 results retain
their original component and image identities.

## Implemented changes

- DIR 011: empty DU output is two rows: `D0: NO FILE`, followed by
  `---- 796K FREE ----`, using the actual DU and free space.
- CRCKSUM 008: /40 emits complete heading/rule/value groups of two equal-width
  checksum columns, preserving algorithm selection and command-line order.
  Later groups align beneath the first checksum column. Saved native/legacy
  list formats are unchanged.
- NOAH 020: dotted member names, decimal sizes/counts and compact summaries.
  Routine capacity/candidate/disposition accounting and zero recovery counts
  are omitted. Errors, skips, failures, cancellation, incomplete CRC coverage
  and nonzero recovery-artifact information remain visible. Empty selections
  report no work without generic warning prose. Internal outcome codes are
  unchanged; quiet standalone codec operations retain a final summary.
- NOAH adds /L, /A, /QUIET and /H aliases for /LIST, /ADD, /Q and /HELP.
  Help keeps precedence over /VER and works without the overlay. No /V alias.
- COPY 009: /HELP lists both operand forms and /O, /S, /B, /V, /BACKUP,
  /HELP and /VER in the Utilities presentation. Help wins over /VER without
  file operations. Short syntax errors and resident COPY remain unchanged.
- Manuals describe the revised output and mounting the companion disk in C:.
  The authoritative component registry and generated legacy projection agree.

The utility-wide /H consistency update remains a separately deferred task.

## Verification

Passed against these changed binaries:

- CRCKSUM: 134 compiled fixtures, explicit grouped-layout/order checks, exact
  narrow/wide saved-list comparison, native ZSM4/LINK parity and cpmsim commands.
- DIR/COPY: native ZSM4/LINK byte parity; DIR column-fit checks (264 cases),
  populated/empty reports and banner execution; COPY decimal/allocation checks
  and side-effect-free help/precedence execution.
- NOAH: 181 command/adapter cases; 238 focused archive-write, accounting,
  outcome, quiet, source-failure, coverage/recovery, staged-failure, ARK,
  method-3 and method-4 transactions; 37 LZW and 88 codec/overlay transactions.
  Tests inspect internal status/counts where accounting prose was removed.
  Decimal output is checked through 4,294,967,295. The low-memory fixture uses
  400 names because the smaller controller permits the old 300-name case.
- All nine NOAH production modules match native ZSM4/LINK output under cpmsim.
- A cpmsim smoke campaign runs new DIR/COPY/CRCKSUM/NOAH against the retained
  bfe4556 candidate system and primary Utilities media. NOAH creates, lists,
  tests and quietly extracts a fixture into another user area; independent
  export matches the original bytes exactly. These mixed test media are not
  release candidate packages.
- MD5SUM: 87 fixtures. Its rebuilt bytes match the preceding candidate image,
  excluding physical record padding; its revision remains unchanged.
- Registry/projection tests: nine passed. `git diff --check` passed.

External host archive-oracle entry points could not run because this checkout
lacks their pinned arc/deark executables in build/noah-proof/references.
The corresponding production transaction suites passed; no new external-oracle
PASS is asserted. No automated trs80gp launch was attempted.

## Evidence and remaining acceptance

Retained records in [evidence/2026-10-30-stabilization](evidence/2026-10-30-stabilization/)
identify local artifact hashes, native module parity, cpmsim media/input/output
hashes, commands and independent extraction readback. Local build logs remain
under build/final-stabilization-noah-native-v2 and build/final-stabilization-cpmsim.

No new Model 4 runtime PASS, fresh-package installation PASS or release acceptance
is claimed. Rebuild and package one candidate from the accepted source commit,
then perform the reduced manual checks in Model4-Manual-2026-10-29.md.
