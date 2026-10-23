# Engineering assessment Part 9: command-loader architecture

Date: 23 October 2026. Status: approved by the maintainer; Part 10 authorized.
Part 9 merged through PR #460 at `c3e1d6bcf7fca8fdf5723f7e32bdf53c70cf6e71`.
Part 8 was approved and Part 9 authorized. Accepted core 1.0 remains
`3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## 1. Decision

**A verified second stage can load checked CCP/CPX carriers without reducing
the recovered TPA.** The live cpmsim prototype retains 57,344 bytes unloaded
and 54,272 bytes with ANSISCRN + ADM3A. It validates the complete declared
carrier, checks its public/private binding, and uses the same buffered bytes
for relocation. No additional resident allocation is required.

There is also a useful correction to any pessimistic reading of Part 8's
size result: **the existing CPX payload-checksum gap can be closed in a
924-byte reloader, exactly the previous executable size.** Rearranging the
normalized header permits a block copy that pays for the checksum code.
Lack of room for a naive addition was not proof that useful checks could not
fit. This compact alternative was assembled, executed and tested live.

Recommend continuing with the verified second-stage architecture for the
complete migration. Do not yet freeze its whole-carrier buffering policy.
That policy is simple and tested, but retaining only the relocation header
while streaming the payload is a promising way to reduce temporary memory.
The latter is a design alternative, not an implemented result of Part 9.

## 2. What was compared

| Property | Compact checksum experiment | Verified second-stage experiment |
| --- | --- | --- |
| Executable size | 924 bytes, within the existing 932-byte allowance | 54-byte bootstrap + 1,172-byte second stage |
| CPX payload checksum | Enforced before relocation | Enforced before copying or relocation |
| CCP/CPX binding | Not implemented | Private IDs checked; explicit public CPX supported |
| Header, relocation table and command metadata integrity | Not added | CRC covers the complete declared carrier except its final CRC word |
| Relocation-data reread | Retained | Eliminated |
| New resident allocation | None | None |
| Temporary-space consequence | Existing loader layout retained | Whole carrier buffered; placement constraint enforced |
| Role | Small independent defect fix | Working architectural prototype for complete migration |

The compact experiment is not a complete counterproposal for all the migration
requirements. A more extensively optimized single-stage loader remains
possible; this part does not prove a minimum executable size. Conversely, the
second stage is no longer just a size estimate: it boots and reconstructs the
command environment in cpmsim.

The work is isolated on `assessment/part9-command-loader`, based on Part 8
commit `6539c66877f3d09605aa86b1add57fe92748b250`. During this work, Part 8
merged through PR #458 at `945bff1508d570414fddac491fd8c0dcbb83aac5`.
Main's separate CR/UNCR utility work is preserved and is not included in this
prototype's qualification.

## 3. Second-stage design and integrity boundary

The existing resident gate still validates the 1 KiB reloader carrier before
entering it. That carrier now contains the small bootstrap. The bootstrap
reads a 2 KiB second-stage carrier, checks its private ID and expected CRC,
and enters it only after both checks pass.

The second stage occupies existing cpmsim raw records 84–99, which the pinned
checked image fills with obsolete helper placeholders. Their old selector
path is not used by the checked RSX loader. The proof image therefore needs
no larger reserved disk area. Reusing those slots is a private package-layout
change: production builders, installers and mixed-version checks must all
agree before it can be adopted. It is not permission to overwrite these slots
on an arbitrary CP/M installation.

For each command carrier, the loader reads the first 128-byte record, checks
the declared bounds, determines the complete extent, and reserves a
non-overlapping staging area below the prospective runtime destination.
It then requires every remaining 128-byte record. It does not use the old
four-record file-stream helper's short-block convention, which can return
success without a valid-byte count and leaves the unread bytes untouched.

The candidate BCPX2/BCM2 formats retain Part 8's 20-byte binding trailer and
extend it by a CRC word. Binding schema 2 identifies this **22-byte** trailer.
The CRC covers the header, header padding, relocation table, payload, command
metadata and binding record. It excludes its own two bytes, unused final
record padding and any unused trailing file records. Private CCP is required;
public HELLO uses a zero ID. The existing CPX additive payload checksum is
also checked.

After integrity and binding checks, every relocation offset must fit wholly
inside the executable payload. The candidate also requires sorted,
non-overlapping relocation words. Only then does it copy the payload, apply
relocations from the retained header and publish the prospective descriptor.
The loader never rereads the file's relocation directory. The CRC therefore
checks the same in-memory bytes used by the subsequent copy and relocation.

These checks address accidental corruption and mixing of build products.
Neither the CRC nor a declared public class authenticates an author or makes
untrusted executable code safe. The candidate format and relocation-table
rules are not frozen public interfaces.

## 4. Exact memory costs and the important tradeoff

| Region in the full-staging prototype | Address range | Reserved bytes |
| --- | --- | ---: |
| First-stage carrier and its initial stack area | 0100h–04FFh | 1,024 |
| Second-stage carrier, including ID and padding | 0500h–0CFFh | 2,048 |
| Second-stage stack allowance | 0D00h–0FFFh | 768 |
| Staged RCP carrier, rounded to records | 1000h–327Fh | 8,832 |
| Total temporary envelope for RCP reconstruction | 0100h–327Fh | **12,672** |

The second-stage executable uses 1,172 of the 2,024 bytes available before
its binding field, leaving 852 bytes in that code allowance. The stack table
describes a reserved envelope, not a proven worst-case stack-depth bound.

This RAM is borrowed after the application has finished and is reusable by
the next application. It does not lower maximum COM size. The separate RSX
transaction reservation remains 4,096 bytes; these two reservations describe
different operations and should not automatically be added together.

The resident comparison covers all 6,656 bytes in its raw carrier. Only the
two-byte expected bootstrap-CRC operand changes. The resident allocations,
upper RAM layout, service addresses and reported TPA are unchanged. These
proof images deliberately hold the Part 8 resident contract fixed; they do
not constitute newly generated, fully checked profile packages. Production
integration must include the new sources and layout in a fresh contract ID.

| Current command carrier | Carrier bytes | Record-rounded staging | Runtime allocation | Minimum incoming boundary for staging + placement |
| --- | ---: | ---: | ---: | ---: |
| CCP | 6,528 | 6,528 | 5,632 | 16,256 |
| RCP.CPX | 8,756 | 8,832 | 7,168 | 20,096 |
| HELLO.CPX | 687 | 768 | 256 | 5,120 |

The final column is an absolute address, not a TPA size. It follows from
`1000h + rounded carrier length + allocation`. Fixtures accept each exact
boundary and reject one byte less. Default reconstruction has ample room,
but a large CPX or a crowded profile can hit this limit. Keeping application
TPA unchanged does not make that restriction irrelevant.

Each candidate file is 22 bytes larger than its original carrier. None of
these three gains a 128-byte record or a 512-byte transfer block. The bootstrap
adds a 2 KiB raw-stage read; eliminating relocation rereads changes other I/O.
No wall-clock speed or original-hardware performance result is claimed.

**Why not declare full staging the final answer?** The relocation header is
the information that needs to survive the payload read. An alternative could
retain the at-most-1,536-byte header, stream payload bytes into an unpublished
destination, and verify an incremental whole-carrier CRC before relocation
or activation. A failed optional module could discard that destination and
restore the allocation boundary. It would not need a second full payload
copy or a relocation reread.

With the same 3,840-byte loader/stack envelope, a 1,536-byte header and one
128-byte input buffer suggest a **5,504-byte temporary budget**, before any
additional state or alignment discovered during implementation. That is a
design estimate, not a tested capacity. It would weaken the current prototype's
guarantee of no destination writes on invalid input, while potentially
preserving the more important guarantee that no invalid module is linked or
executed. That tradeoff deserves the next bounded experiment.

## 5. Failure behavior

An optional CPX that fails validation is skipped with the existing `CPX?`
diagnostic. Its allocation boundary is restored, it is not linked or
initialized, and reconstruction continues. The tested good carrier can be
restored and loaded subsequently. The persistent requested profile remains
available for correction; this is not an atomic rollback of the entire old
CPX environment, whose reconstruction normally follows warm boot.

Active RSX services are separate. Live tests mutate STATEFUL before the CPX
failure and confirm its state afterwards. The second-stage loader does not
reconstruct or discard those RSX instances.

A bad second-stage executable, foreign second-stage ID or invalid mandatory
CCP produces the deliberate `!` halt before a command prompt. There is no
automatic fallback to an unchecked CCP. Recovery from this fatal path still
requires valid media and a restart; Part 9 does not demonstrate a disk-free
CCP recovery image.

The compact checksum-only experiment likewise rejects the stale-checksum
HELLO and permits a later good load. It retains the existing header/relocation
reread behavior and is not presented as solving whole-carrier consistency.

## 6. Evidence and limits

**Executed Z80 fixtures:** matching CCP, RCP and HELLO reproduce the expected
relocated payloads and published entry/lifecycle pointers. Failure of every
required record is rejected before destination writes: 51 CCP records,
69 RCP records and 6 HELLO records. Exact staging boundaries pass and one
byte less fails. Fixtures also cover payload/header/trailer corruption,
all sixteen changed ID bytes per carrier with recomputed CRCs, invalid
header extents and lifecycle offsets, duplicate/out-of-range relocations,
unknown binding schema/class, public CCP and stale CPX checksums despite a
valid whole-carrier CRC.

Bootstrap fixtures reject all sixteen partial-read positions, sampled code,
ID and padding corruption, and a foreign ID even when the expected CRC is
deliberately made to agree. The instrumented matching stage is entered.

**Live cpmsim:** the full-staging image boots, loads/executes/unloads HELLO,
and runs a patterned 57,344-byte COM. A 57,472-byte COM is rejected; the fitting
program runs again. RET, JP 0, BDOS Function 0 and BIOS WBOOT all return.
Four CPX failure campaigns cover changed payload, malformed public ID with a
recomputed CRC, old format and truncated file. Each preserves usable STATEFUL
state, permits recovery with the good carrier and returns to 57,344 bytes.
ANSISCRN + ADM3A leaves 54,272 bytes and unloads successfully. Corrupt stage
code, stage ID and CCP payload each halt before the prompt.

The checked legacy-profile control also boots, loads/executes/unloads HELLO
and retains 54,272 bytes unloaded. This is a smaller control campaign than
the full-RAM campaign, not equivalent platform qualification.

The compact checksum experiment passes matching/mutated-payload fixtures for
both RCP and HELLO, plus the live stale-checksum rejection and recovery case.
Fresh repeat assemblies produce identical bytes for eight prototype
executables/carriers. This is not a claim that an integrated production build
or its complete media has been rebuilt and qualified.

The preserved tests use z80asm 2.1 and the pinned Part 2 cpmsim executable,
SHA-256 `b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`.
[Part9-Reproduction.md](Part9-Reproduction.md) explains the experiment inputs
and commands. The report includes proof images, source, listings, transcripts,
test results and hashes.

Native/ROM builds, actual Model 4 hardware, installation and upgrade atomicity,
private utilities, arbitrary third-party modules, all eight-slot lifecycle
combinations, deep physical-I/O abort paths and complete stack high-water
qualification remain open. Some fixtures substitute controlled disk adapters;
they do not reproduce every physical error timing. Future default datestamping
and named-register costs are still outside these measurements.

## 7. Next bounded work

Retain both prototypes. The compact checksum correction is worth integrating
as an independent defect fix if command-carrier migration will be delayed.
Record any integrated fix as a later commit while retaining the accepted
core 1.0 baseline.

**Proposed Part 10:** implement and measure header retention with single-pass
payload streaming inside the verified second-stage architecture. Compare its
temporary limit, failure behavior and complexity against this full-staging
reference. Require unchanged 56 KiB / 53 KiB application results, no execution
or publication of rejected carriers, and recovery without damaging active RSX
state. Include truncated reads and failure after partial destination writes.

After that decision, integrate the chosen loader into fresh checked-profile
builds and package/install validation, issue the correct new compatibility
contract, and continue stack/private-utility/native qualification. Those are
adoption gates, not work silently claimed complete by the proof images.

Pause here for maintainer review and Work-credit assessment. Model 4 window
mapping remains a separate investigation.
