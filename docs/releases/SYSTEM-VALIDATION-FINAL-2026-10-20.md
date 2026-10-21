# Final accounting and clean-build acceptance — 20 October 2026

## Status

**V052 acceptance is complete for the core OS and both System Disks**, for
merged revision `408560d528e353288c903289c1a799015331dc30` and the exact images
below. No release-blocking findings remain within that scope. The two A0 lookup
profile differences are explicit; V050 remains a failed historical candidate.

Scope remains the core OS and two System Disks. Documentation alignment follows
validation; the Utilities and CP/M Tools disks have separate qualification.

## V050 clean source and images

Clean detached source: `2e1b51635bf0e8c7e8f8d1e46ece85875f148e59`.
Both images were built in new, isolated work roots; no daily images were reused.
The distribution builder passed boot/identity, manifest, CONFIG fingerprint,
file-integrity and independent filesystem checks. Source remained clean.

| Platform | Candidate SHA-256 | Manifest/free space |
| --- | --- | --- |
| cpmsim | `12095ecfd82f6f749854895536c6df4073d3c9ab7e8e458cbb028c7d15f50e51` | 30 files / 148 KiB |
| Model 4 | `0e0de947f8370e0d74b57d1ebc9d2229a358dd7a8aaf8236c4c6fd4fa42e90d3` | 29 files / 596 KiB |

The independent suite was rebuilt from pinned revision
`a9a878fcd2e36698c7e856654a85847a004fdd20`; all 13 emitted programs match the
pinned bytes. Source, build-tool/emulator hashes and build inputs are retained.

## Fresh evidence and accounting

cpmsim returning groups captured 412 canonical rows: 273 pass, 115 not run and
24 observed, with no failed/error rows. Canonical executable ownership prevents
prerequisite rows from overwriting the actual owner program's results.
Supplemental console, read-only, ecology, full-TPA and COPY/MOVE witnesses pass.
All three monitor personalities pass on both backends; operator recovery passes
on cpmsim and native Model 4. Native DIR/BDOS/file/random, CCP/entry and
CPU/ecology/disk-safe groups and BIOS/error-safe checks pass with independent
media and shipped-file audits. Group summaries do not become invented native
per-card transcripts.

The [627-card matrix](SYSTEM-VALIDATION-FINAL-V050-CARDS.tsv) and
[evidence index](SYSTEM-VALIDATION-FINAL-V050-EVIDENCE.json) account separately for:

| Classification | Cards |
| --- | ---: |
| Actual canonical suite pass | 273 |
| Reviewed external pass | 57 |
| Reviewed controlled-instruction pass | 14 |
| Confirmed failure | 2 |
| Required evidence reconciliation still open | 84 |
| Non-guaranteed not run | 119 |
| Observed | 24 |
| External profile observation | 1 |
| Outside baseline | 50 |
| Optional profile review | 3 |

The open required cards are exactly enumerated in the matrix: BDOS 3, BIOS 16,
CCP 20, console 23, directory 3, entry 8 and error handling 11. Open means no
accepted exact fresh oracle has yet been assigned; it does not mean a failure.
Controlled providers/private DPBs qualify common compiled code, not physical
peripherals. Actual suite rows are retained even when another oracle finds a
failure. The original foundation did not test sequential directory exhaustion;
0405/0516 are explicitly failures, never inferred passes from that foundation.

The fresh auxiliary-device run is **blocked** while a separate user-owned
cpmsim session occupies the shared endpoint. That session was not interrupted
and no data was fed into its input. Historical Step 7 endpoint qualification is
retained as historical evidence, not presented as a fresh candidate pass.
No physical clock was changed.

## Confirmed directory-full finding

A disposable disk contains one full physical extent, a probe and zero-length
files occupying every directory slot; data blocks remain free. Actual DRI CP/M
2.2 and BetterCP/M programs issue public Function 21 at the extent boundary.
DRI returns `01h` without changing the 36-byte caller FCB. V050 returns `FFh`
and changes EX/CR to the uncreated extent. Source content, full data-disk bytes
and independently checked filesystem remain unchanged on both systems.
Allocation exhaustion is a separate controlled fixture and returns `02h`.

The defect is nonlocal failure propagation from the shared Make path: it
bypasses sequential rollover cleanup. The candidate correction returns the
logical failure through the extent helper, restores EX/S2/CR, preserves the
sequential `01h`/random `05h` distinction and retains allocation-full `02h`.
No rollback after destructive writes is involved.

The correction's compiled BDOS is still **3,454 bytes**. Live-state and stack
anchors remain `E3CDh`, `E412h` and `E43Ah`; its 40-byte private stack is unchanged.
Twelve controlled clean/dirty FCB and EX/S2-boundary cases pass, with 28 bytes
maximum measured stack use. Foundation, grouped extents, BIOS and operator
recovery checks pass. Compaction uses the active IX FCB during Open, word stores
for vector reset, and shorter equivalent error/branch sequences. Shifted-ROM
assembly discovers 790 operands instead of 794 (three fewer live-RAM and one
fewer ROM target); individual source/target/relocation checks remain mandatory.

The first correction build stopped at stale expected ROM operand counts and
published no distribution. The inventory was independently regenerated and its
per-source differences reviewed; corrected expectations accompany the fix.
V051 below passes the corrected-candidate checks. Final merged release
acceptance remains separate.

## V051 — correction qualified on clean development images

Clean source `9f2affeae7c6` includes the BDOS correction and reconciled ROM
inventory assertions. Both isolated builds pass the full distribution builder.

| Platform | Corrected candidate SHA-256 |
| --- | --- |
| cpmsim | `6823e809d2e52ab978bd37646b9f201ff3a074fc910fdd0ec1df780030e8fae2` |
| Model 4 | `e748de7d6cf2da503a1d5887c70568011bd8aeb5d3264a1d3113c369b17cc19e` |

The actual cpmsim DRI comparison passes Functions 21 and 34: sequential `01h`
with all caller FCB bytes unchanged, random `05h`, and unchanged source/full data
disk bytes. All 11 selected returning conformance groups pass again, with no
failed/error rows. Fresh compiled-model foundation, 12 boundary cases, grouped
extents, BIOS, error recovery and ROM/RAM ownership pass. Common BDOS/CCP bytes
match across both platform builds and frozen state/stack addresses match V050.

Native FILETEST passes 68 required checks. A separate native full-directory disk
has 128 occupied slots, 390 free data blocks, and one 16K extent using the native
16-bit allocation map. Actual Functions 21/34 return `01h`/`05h`; sequential FCB,
whole data disk and all 29 shipped system files are preserved. Independent
filesystem checks pass before and after. This qualifies the fix across the two
physical extent/allocation-map representations, rather than relying solely on a
common-code model.

Native harness exclusions are retained. The first run reused the same status
marker and its parser selected prior output; raw captures already showed the
correct guest statuses. The repeat uses distinct sequential/random markers and
passes. A scoped postprocessing review corrects the repeat's random FCB metadata
(the first unscoped parser had selected the preceding FCB text). The immutable
original captures/results remain beside that review. No new guest execution or
random-FCB preservation guarantee is inferred by the review. The final runner
scopes all fields to the corresponding status marker.

The [V051 evidence index](SYSTEM-VALIDATION-FINAL-V051-EVIDENCE.json) records the
accepted result hashes, raw evidence and verified durable archive. The original
V050 failure remains a failure for those original bytes. This is a qualified
correction checkpoint, **not closure of overall validation**.

## Historical gates following V051 (resolved by V052)

1. Merge the V051 correction checkpoint. Its development-image DRI/native and
   affected regression checks pass; retain V050 as the failed candidate.
2. Reconcile the 84 named required cards and three optional-profile cases;
   retain explicit blocked/manual/not-applicable results and their reasons.
3. Resolve the fresh auxiliary-endpoint gate without interfering with the
   user's session.
4. After fixes merge, build again from that exact clean revision and run final
   release acceptance against its identified images. No later code change may
   inherit those acceptance results.

The V050 archive contains 5,655 files (25,230,785 compressed bytes), including
excluded attempts, runner sources, raw captures, before/after media, build
states and compiled artifacts. Every archived file was reopened and checked
against its SHA-256 manifest. The evidence index records the durable local
archive path, archive hash and manifest hash. This preserves the failed
candidate rather than replacing its evidence with corrected results.


## V052 — clean merged-source acceptance complete

The isolated clean build of merged revision
`408560d528e353288c903289c1a799015331dc30` passes boot, identity, manifest,
CONFIG fingerprint, file-integrity and independent filesystem checks. The
accepted images match the qualified V051 bytes:

| Platform | SHA-256 | Files / free space |
| --- | --- | --- |
| cpmsim | `6823e809d2e52ab978bd37646b9f201ff3a074fc910fdd0ec1df780030e8fae2` | 30 / 148 KiB |
| Model 4 | `e748de7d6cf2da503a1d5887c70568011bd8aeb5d3264a1d3113c369b17cc19e` | 29 / 596 KiB |

The [V052 card matrix](SYSTEM-VALIDATION-FINAL-V052-CARDS.tsv) accounts for
all 627 pinned-suite cards. Of 430 required cards, 273 have actual canonical
suite passes, 99 reviewed external passes, 56 controlled compiled-code passes
and two documented profile differences; none remains open, blocked or failed.
Actual suite observations remain 273 pass, 115 not run and 24 observed among
412 canonical captured rows. Supplemental evidence does not rewrite not-run
suite rows into passes or invent native per-card transcripts from group counts.

Cards 0493/0494 require current-DU-only command lookup in the generic oracle.
BetterCP/M intentionally searches A0 after the current DU, as specified in
[CCP Fixed A0 Lookup](../engineering/CCP%20Fixed%20A0%20Lookup.md). Current-DU
precedence, exact qualified lookup and caller-DU restoration pass. These are
profile differences, not generic CP/M passes. Optional Function 37 profile
cards 0435/0523 pass; optional structured physical-error result card 0413 is
not selected. Required ordinary operator error recovery is tested separately.
The remaining classifications retain 119 non-guaranteed not run, 24 observed,
one external profile observation and 50 outside baseline.

The main acceptance cohort covers 25 cpmsim tasks, ten native tasks and six
native workflow tasks. Forty completed directly. The initial cpmsim fault
invocation omitted required host arguments and ran no guest test; its corrected
invocation passes all three recovery scenarios. The fresh runs cover returning
conformance groups, console input/output, read-only behavior, CCP/full-TPA
returns, directory-full comparison with DRI, native documentary probes, monitor
protocols and both backends, COPY/MOVE, batch operation, real media changes,
configuration/export/install/cold boot and repeated release workflows. Independent
before/after media, shipped-file and filesystem audits are retained.

Supplemental compiled-code and actual cpmsim checks cover the previously open
console, IOBYTE, error, BIOS, CCP and allocation cards, with private-provider
and synthetic-controller limits stated per evidence group. Common BDOS/CCP
bytes match across platforms. Fresh unchanged WordStar edit/save/return and
historical MM CONFIG 3.10 opening-menu witnesses pass; the latter does not
claim MM configuration writes. The actual native full-TPA run passes RET,
jump-to-zero, Function 0 and oversize rejection from B31 using A7 programs.
It uses queued SUBMIT commands and explicit input gates. The earlier fixed-delay
attempt and legacy boundary startup/launch failures are excluded harness
attempts, not guest failures or passes; their raw evidence remains retained.

After the user exited their daily cpmsim normally, the fresh PIP printer and
auxiliary endpoint check and DRI comparison passed, resolving the shared-endpoint
blocker. No user session was killed or fed test input. No physical clock was
changed. Emulator profiles do not certify physical printer, serial or clock
hardware. Other hardware/profile limits remain as documented in Steps 7–9.

The strengthened extent-full test restores the entire compiled instruction
prefix instead of inheriting a legacy fixture cache patch. All 12 clean/dirty
EX/S2 cases pass with **30/40 private stack bytes** used, superseding the old
28-byte measurement. BDOS remains 3,454 bytes, CCP 5,482 bytes, and unloaded TPA
53K. No production source changes followed these acceptance runs. Supplementary
runners are hashed independently, not represented as part of tested revision 408560d.
Accounting checks confirm that FAIL/BLOCKED/profile differences override suite
passes and that required cards cannot be excluded as optional. Runner syntax
and whitespace checks pass.

The [V052 evidence index](SYSTEM-VALIDATION-FINAL-V052-EVIDENCE.json) identifies
reviewed evidence and the durable 8,486-file archive. Every regular file was
reopened and SHA-256 checked when archived. The pending closure checkout later
expired before its commit was pushed; its runner sources and card matrix were
recovered byte-for-byte from that verified archive, and this closure prose was
reconstructed from the retained results. Recovery introduced no production
changes or new test verdicts.

Core OS/two-System-Disk validation is closed for those revision/image identities.
Documentation is being completed independently (the User's Manual is complete).
Utilities and CP/M Tools disks remain separate completion and qualification work.
Future production changes require appropriate regression and acceptance checks.
