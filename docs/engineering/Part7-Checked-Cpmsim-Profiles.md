# Engineering Assessment Part 7: checked cpmsim profiles

Date: 2026-10-23. Status: bounded prototype assessment complete; awaiting
maintainer review. The accepted core 1.0 baseline remains
`3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## Finding

The cpmsim full-RAM profile retains the complete **3,072-byte TPA gain** after
adding private compatibility IDs and integrity checks to its reserved-track
helpers and R3PACK loading path. The measured unloaded maximum remains
**57,344 bytes (56 KiB)**. ANSISCRN plus ADM3A leaves **54,272 bytes (53 KiB)**.

The checks add **no permanent allocation** in this prototype. They consume
159 previously spare bytes inside existing BIOS and disk allocations. They
also increase temporary RSX transaction workspace from 3,840 to **4,096 bytes**.
This is the +256-byte candidate from Part 6; the additional 1,024-byte fallback
resolver buffer was not needed in the tested paths.

This supports continuing the profile approach. It does **not** establish a
fully checked or release-qualified OS: CCP carriers, general RSX/CPX carriers,
private utilities, installation bundles and native builds remain separate
compatibility gates. The resident spare space used here is now exhausted.

## 1. Scope and repository boundary

The isolated branch is `assessment/part7-checked-profiles`, based on Part 6
commit `7704c1e31249fe6e8fc5702dd6a08ecf4938ecb1`. No Part 7 change is merged
into main. Main was observed at `d9e5db00ab4ea020550c12cc5b64afb465c506df`,
including subsequent UNCR utility work; that work is preserved and is not part
of this prototype's tested source snapshot.

The builder stages complete, fresh source trees because existing builders
import a global layout. Source transformations are guarded against source
drift and are confined to each staging tree. This is an assessment bridge,
not a finished production build interface.

| Explicit profile | Behavior |
| --- | --- |
| `cpmsim-legacy` | Original F400h resident ceiling, unchecked regression control |
| `cpmsim-legacy-checked` | F400h ceiling with the new helper gates |
| `cpmsim-fullram` | 10000h exclusive resident ceiling with the new helper gates |
| `model4-legacy` | Prepare-only legacy layout; this wrapper refuses to build or qualify it |
| Other targets/modes | Rejected before creating output |

The checkout's default layout is restored to the accepted legacy addresses.
Full RAM is selected explicitly in staged cpmsim builds. Model 4 full-RAM and
ROM profiles are not admitted. The existing cpmsim build pipeline still
produces intermediate Model 4 artifacts while obtaining shared metadata;
these are not deliverables and are not qualified by this assessment. Removing
that dependency remains production integration work.

## 2. What the checked loading path does

**Reserved-track helpers.** The resident BIOS validates a 16-byte private ID
and the CRC-16 of all 1,024 bytes before entering the reloader, CPX control
image or RSX transaction entry. The ID occupies a checked, previously unused
16-byte region at payload offset 1000 decimal. Build guards check the actual
code bounds and refuse overlap. The resident ID and compact comparator occupy
the disk adapter's former 26-byte tail allowance; CRC and rollback state fit
inside the BIOS allocation.

This is a deliberate simplification of Part 6's proposed separate system
manifest: fixed positions, a common binding field, and resident checksum
anchors describe the three admitted raw images. It adds no raw records. The
reloader/selector carrier is checked as a whole, although the RSX entry path
no longer executes the selector. This is not a generic extensible carrier
manifest and must not be described as one.

**R3PACK.** A 512-byte header precedes fifteen 1,024-byte slots. The resulting
15,872-byte file occupies 124 CP/M records, still one extent. Each open checks
the expected length, the generated header checksum and its full private ID.
The header checksum is anchored in the already-checked entry/reader, covering
the generated slot directory, format fields and reserved bytes. Runtime
addresses and accepted slot numbers are fixed by the reader; a header cannot
choose an arbitrary destination. The selected payload is fully staged and
CRC-checked before any copy into CFG or manager memory. Record completion is
checked independently of checksum validation.

The header has its own CRC field, but this prototype's runtime check uses the
CRC of the complete generated header, including that field. It therefore
accepts the exact build's helper set rather than independently parsing a
family of interchangeable manifests. A compatible payload update requires
regenerating the affected anchors. This conservative restriction is acceptable
for this experiment, not a final update policy.

**Private identity.** A canonical versioned contract includes profile, layout,
workspace size, an explicit private epoch and conservative source/builder
input hashes. Documentation, timestamps and the Git commit ID do not enter the
compatibility hash; provenance records the commit separately. The tested
full-RAM ID is `aa416f49caa7e35a690db9eeb9d41bf4`. The source closure deliberately
rejects some potentially compatible code changes. A production contract still
needs a reviewed semantic ABI policy and native generation.

CRC-16 detects accidental damage; it is not authentication, and collisions
are possible. Identity and checksum are separate tests: fixtures deliberately
supplied a matching checksum for an image carrying the wrong ID and verified
that identity rejection still occurred.

## 3. Resolver preservation and failure recovery

The initial RSX control image now executes in the existing CONFIG buffer.
The live manager/resolver remains in place while the request and workspace are
validated. ENUM, QUERY, idempotent LOAD and absent UNLOAD need no mutation
workspace and do not open R3PACK.

For a mutation, the entry saves the active resolver before the first manager
replacement. Abort recovery copies the resolver from temporary RAM; it does
not read the medium that just failed. A zero rollback pointer represents a
request that left the manager untouched. The initial load clears that pointer
before every request, preventing reuse of stale transient memory.

Before commit, the finalizer prefetches and checks the replacement resolver in
the same temporary resolver area. This is usable for abort recovery of the
old profile too: it resolves against the published live chain, not a captured
new-chain address. Source inspection found request initialization at entry,
operation-specific counter resets, cleared output/status fields, and provider
bindings derived during each live traversal. Late MOVE and COMIT corruption
tests exercised this reuse after prefetch; the old stateful provider remained
callable and retained its mutated state. This is bounded evidence for the
current resolver, not a promise that a future stateful resolver can share the
same buffer without review.

The commit and publication code's disk-free structure is unchanged. No
additional fallible reads were introduced after movement begins. A full
instrumented proof of all post-commit paths and interrupt/stack high-water
behavior is still required before supported-profile adoption.

## 4. Measured memory and disk costs

| Item | Previous | Checked prototype | Consequence |
| --- | --- | --- | --- |
| Full-RAM unloaded maximum COM | 57,344 bytes | 57,344 bytes | Entire 3,072-byte gain retained |
| Full-RAM ANSISCRN + ADM3A maximum | 54,272 bytes | 54,272 bytes | No added resident allocation |
| Legacy checked unloaded maximum | 54,272 bytes | 54,272 bytes | Checks also fit the old layout |
| cpmsim BIOS occupied bytes | 624 / 757 | 757 / 757 | 133 spare bytes consumed |
| cpmsim disk occupied bytes | 916 / 942 | 942 / 942 | 26 spare bytes consumed |
| Copied reader | 242 / 256 | 450 / 512 | Expanded code allowance fits |
| RSX entry executable bytes | 660 | 893 | Binding begins at offset 1000 |
| Temporary transaction reservation | 3,840 bytes | 4,096 bytes | +256 temporary bytes |
| R3PACK file | 15,360 bytes | 15,872 bytes | +512 disk bytes, still one extent |

With the 7000h effective workspace ceiling, prospective transaction data now
ends at 6000h rather than 6100h. The extra workspace is borrowed only during a
transaction; it does not reduce the advertised TPA. It can nevertheless
reduce the largest profile reconstruction that fits. This assessment did not
measure the maximum possible transaction size for every module combination.

The pinned startup remains banner-only. NDR and datestamping are not loaded or
budgeted by these results; their future default costs must be measured. The
four-provider limit also remains unchanged.

Every uncached packed-helper load now reads a 512-byte header in addition to
the 1,024-byte payload and computes CRCs. That is four additional CP/M records
before directory overhead. No elapsed-time or original-hardware performance
claim is made.

## 5. Execution and build evidence

**Live cpmsim, full-RAM checked media:**

- A 57,344-byte patterned COM executes and verifies its loaded contents and
  both memory boundaries; a 57,472-byte COM is rejected. The fitting program
  executes again after that rejection. RET, JP 0, BDOS Function 0 and BIOS
  warm boot return successfully.
- Stateful services survive normal load/unload/relocation and a missing-module
  failure. ANSISCRN and ADM3A load and unload with the expected memory maps.
- Nine active-profile failure campaigns cover a foreign pack, truncation,
  header corruption, missing pack, and corrupted COORD, FINAL, MOVE, COMIT and
  RESOL payloads. Each retains usable stateful service state and the same
  reported TPA; restoring the good pack permits a subsequent successful load.
- Four direct/no-op operations succeed with zero mutation workspace while
  R3PACK is absent. Three malformed mutation work ranges are rejected; the
  active stateful provider still responds correctly.
- Corrupt reloader code and a foreign reloader ID produce the deliberate halt
  marker before a command prompt, rather than executing an unchecked image.

**Executed Z80 fixtures:**

- All fifteen matching R3PACK slots load into CFG. All fifteen also load in
  manager mode, preserving the last twelve manager bytes and restoring CFG.
- All twelve relevant record failures for each of fifteen slots are rejected:
  four header records and eight payload records. Sampled corruption at three
  positions in each payload, 37 header positions, malformed lengths/slot
  descriptors and foreign IDs is rejected before destination replacement.
- Raw helper checks cover all three admitted carriers, damaged payload and ID
  bytes, deliberately matching CRCs with foreign IDs, partial initial reads,
  preservation of manager code, and restoration with disk code made unusable.

The fixtures execute the assembled code with controlled disk adapters. Live
cpmsim campaigns exercise the complete platform path, but they do not inject
a physical read error at every instruction. Stateful and map checks are not
an exhaustive byte-for-byte snapshot proof of every possible provider.

**Build evidence:** two clean full-RAM builds produced identical compatibility
IDs and **136 binary/media artifacts**. The legacy control's twelve selected
core artifacts are byte-identical to the prior accepted-layout control,
including the resident image, BDOS, CCP, raw helpers and old R3PACK. A checked
legacy image also boots, loads/mutates/unloads STATEFUL and returns to its
54,272-byte unloaded capacity. Unsupported profiles and reuse of an existing
output directory are rejected before a new build starts. Distribution file
read-back and CONFIG fingerprint/startup validation pass.

The private cpmsim executable is the pinned Part 2 reconstruction, SHA-256
`b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`.
Host assembly uses z80asm 2.1. Logs, source transformations, manifests, tested
artifacts, checksums and transcripts accompany the report. Commands and host
requirements are in [Part7-Reproduction.md](Part7-Reproduction.md).

## 6. Decision and next bounded work

Retain this prototype and its 56 KiB result. Do not adopt it as a generally
supported profile yet. The main remaining risks are incomplete carrier
coverage, exhaustion of resident slack, production/native build integration,
and complete workspace/stack qualification.

The next bounded part should address **CCP and RSX/CPX carrier binding and
migration**, measuring both permanent and temporary costs. That may reveal a
need to reorganize existing resident allocations; Part 7 does not assume the
remaining checks will also be free. Private utility/discovery and installation
validation, followed by native/package parity, remain additional gates.
Continue to keep Model 4 mapping work separate.

For that later Model 4 investigation, retain the refined leaf-stub idea:
prepare access in registers, map the keyboard/video window, perform the
access, restore RAM, then return. A stack may remain in hidden upper RAM if
no push/pop/call/return or interrupt/NMI accesses it while hidden. All actual
access paths, including M4SCRN, must obey the rule. No Model 4 banking code or
hardware qualification was performed in Part 7.

Part 7 ends here for maintainer review and Work-credit assessment.
