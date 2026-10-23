# Engineering assessment Part 8: carrier binding and migration

Date: 23 October 2026. Status: bounded assessment complete; awaiting maintainer
review. Part 7 was approved and Part 8 authorized. Core 1.0 remains
`3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## 1. Finding and scope

The checked cpmsim prototype now admits migrated RSX carriers according to an
explicit public/private binding. It rejects a private carrier built for the
other memory profile before activating it. **The integrated RSX checks retain
56 KiB unloaded and 53 KiB with ANSISCRN + ADM3A, without another permanent or
temporary allocation.** This preserves the earlier 3 KiB recovery and the
headroom available for applications and optional services.

CCP/CPX migration is **not complete**. Candidate formats and an executed Z80
binding-record checker demonstrate a possible representation, but the command
reloader has insufficient room for a simple addition of that checker. A live
experiment also confirms that the existing loader does not enforce the CPX
payload checksum. The next design must address both compatibility and
integrity, rather than adding an identity check around the current behavior.

This is implementation evidence for the per-system build recommendation from
the comparative assessment. It is not another measurement of NZ-COM, a general
ranking of operating systems, or a supported release build.

The isolated branch is `assessment/part8-carrier-binding`, based on the tested
Part 7 commit `62f241034c4d8b30045f231f550184fd5c297372`. Part 7 subsequently
merged through PR #457 at `de30d831ead16cea0f786e7e7d742fc8ec1533d0`.
Remote main was observed at `96b8c41956db8e58e7939458511bf2469cc1d046`,
including newer CR utility work. This experiment does not overwrite that work
or claim qualification of it.

## 2. Integrated RSX migration

The experimental BRSX wire format advances from 2 to 3 and BMET from 1 to 2.
A mandatory first metadata record occupies 20 bytes: type, length, binding
schema, public/private class and a 16-byte compatibility ID. Its location is
fixed so the loader can check the binding before publishing parsed facts or
executing the payload. Existing payload checksums remain enforced.

Private means the ID must match the resident core's build contract. Public
means the ID must be zero and the carrier uses the defined public interfaces.
Unknown classes, nonzero public IDs, malformed or truncated binding records,
old carrier versions and duplicate binding records are rejected. Internal
normalized carrier facts deliberately retain format value 2; the on-disk
version changes without unnecessarily changing that internal interface.

HELLO and ECHO are admitted as public after inspecting their source for
references: relocated self-references, BDOS entry 5 and the defined RSX ABI.
They are not classified public merely because two builds happen to match.
Public does not mean compatible with arbitrary CP/M implementations.

Other known in-tree modules are conservatively bound to the private contract.
Some may warrant a later public classification after a separate audit. The
builder refuses unknown module names rather than automatically stamping
imported binaries. M4SCRN and FREHDCLK remain in their old format and are
rejected by this cpmsim experiment; their hardware paths are not qualified.

The new `--carrier-bindings` option is admitted only for checked cpmsim
profiles. The wrapper still constructs fresh staging trees and rebuilds the
checked products. A carrier epoch and the migration implementation enter the
compatibility-ID input closure, so the new contract cannot silently share the
old helper identity. The tested full-RAM ID is
`682f3b071d3462869b17426449f3cf34`.

These bindings prevent accidental mixing of known build products. They are
not authentication or proof that an author has correctly declared a public
module. The existing additive RSX checksum is also not cryptographic
integrity protection for the entire carrier.

## 3. Memory and storage costs

| Quantity | Part 7 | Part 8 RSX prototype |
| --- | ---: | ---: |
| Maximum loadable COM, no RSXs | 57,344 bytes | 57,344 bytes |
| Maximum loadable COM, ANSISCRN + ADM3A | 54,272 bytes | 54,272 bytes |
| Temporary transaction reservation | 4,096 bytes | 4,096 bytes |
| R3CARR executable | 683 bytes | 774 bytes |
| R3META executable | 974 bytes | 983 bytes |
| Helper slot size | 1,024 bytes | 1,024 bytes |
| Additional resident allocation | — | 0 bytes |

The extra loader code fits existing transient helper slots. It does not
restore any resident slack consumed in Part 7. R3META now has only 41 bytes
left in its slot; keeping memory allocations fixed does not make future
checks free.

All twelve migrated RSX files gain exactly 20 bytes. Their executable
payloads, relocation information and declared allocations are unchanged.
None crosses a 128-byte file-record or 512-byte transfer boundary in this
sample. A future carrier near a boundary could do so; this is not a universal
zero-I/O-cost claim. M4SCRN and FREHDCLK are excluded from those twelve.

As before, these TPA figures are record-aligned maximum COM loads after the
command environment can be overlaid, not the smaller free area while CCP and
RCP remain present at the prompt. The startup is still banner-only. The 53 KiB
screen configuration is explicitly loaded for testing. Future default
datestamping and named-register services are not included in these costs.

## 4. CCP/CPX candidates and the capacity constraint

The separate candidate encoder produces BCPX version 2 and BCM2 CCP carriers.
It appends a 20-byte binding trailer after the existing content, preserving
payload allocation and relocation structures. These candidates are saved
outside the bootable image and are not consumed by its command loader.

| Candidate | Old file | Candidate file | 128-byte records, both | Allocation |
| --- | ---: | ---: | ---: | ---: |
| CCP | 6,506 | 6,526 | 51 | 5,632 |
| RCP.CPX | 8,734 | 8,754 | 69 | 7,168 |
| HELLO.CPX | 665 | 685 | 6 | 256 |

The isolated Z80 binding-record checker assembles to **80 bytes**. It checks
record extent, address wrap, magic, schema, class and ID, and requires CCP to
be private. Executed fixtures accept matching private and public CPX records
and matching private CCP records, and reject the tested malformed cases.
Host-side carrier parsing also verifies the CPX payload checksum. Neither is
a complete integrated command-loading path.

The current cpmsim reloader is **924 bytes in a 932-byte allowance**. Actually
assembling the checker appended to it produces **1,004 bytes**, before adding
stream positioning, trailer reading, checksum enforcement or recovery glue.
Even reclaiming the obsolete selector's space up to the raw carrier's
binding offset of 1,000 would leave this simple composition four bytes over.

This is evidence against a direct addition, not proof that a refactored
loader cannot fit. The 80-byte checker is not a lower bound or an optimized
production design. We should compare compact reloader refactoring with a
verified second stage before choosing another memory allocation. A second
stage must account for where its code, buffers and stack live and how they
survive failures and command restoration.

## 5. Confirmed open issue: CPX checksum is not enforced

HELLO.CPX contains a stored additive payload checksum. In a private disk copy,
one byte of its message was changed from `Hello from HELLO.CPX` to
`Jello from HELLO.CPX`, leaving that checksum untouched. `CPX LOAD HELLO`
followed by `HELLO` executed the altered payload and printed the new message.
This was reproduced on both the Part 7 image and this Part 8 image.

This is a demonstrated integrity-check gap, not a claim of an observed field
failure. It shows why helper identity checks and format acceptance must not
be reported as complete command-carrier validation. The Part 8 RSX work does
not fix it. Treat it as a required adoption gate for CCP/CPX migration.

The next loader design should validate the bytes it will actually execute.
If it reads a carrier more than once, it must address consistency between
validation and the later copy, and specify the recovery path if a read or
validation fails after the command environment has been overwritten.

## 6. Verification and limits

The assembled RSX admission and metadata code was exercised with all twelve
migrated carriers; both excluded platform carriers were rejected. Fixtures
also reject old wire/BMET versions, wrong record type or length, unknown
schema/class, each of the sixteen altered private-ID bytes, each nonzero
public-ID byte, all twenty binding truncation positions, duplicate bindings
and a changed payload checksum. Failure leaves the applicable parsed-facts
area unchanged. A foreign private carrier is rejected while a foreign public
carrier is accepted.

Eight live cpmsim campaigns cover foreign private, old-version and malformed
RSX carriers, plus a foreign carrier encountered while reconstructing an
already active provider during both load and removal. Stateful service checks
continue to pass; the failed operations preserve their reported capacity;
restoring the matching carrier permits the operation. A public HELLO from the
checked legacy build loads and executes its service in the full-RAM build.

The Part 7 boundary and return campaign was rerun: a patterned 57,344-byte COM
executes; 57,472 bytes is rejected; RET, JP 0, BDOS Function 0 and BIOS WBOOT
return successfully. Stateful relocation, screen load/unload, raw-helper and
packed-helper fixtures pass. Direct/no-op operations with zero workspace,
malformed mutation workspace, and deliberate rejection of damaged/foreign
raw reloaders also pass. A checked legacy image loads, mutates and unloads
STATEFUL and returns to 54,272 bytes.

The candidate command checker separately rejects all twenty short lengths,
forty single-byte mutations across the private/public records, public CCP,
address wrap and unknown carrier kind. Those are executed record-checker
tests, not end-to-end CCP/CPX migration tests.

Two fresh full-RAM builds produce the same compatibility ID and **182 matching
binary/media artifacts**. The inventory includes intermediate products and
the final system image; it is not a count of newly qualified modules. The
build validates distribution read-back and CONFIG fingerprint/startup data.
Unsupported binding/profile combinations are refused before output creation.

Host assembly uses z80asm 2.1. Live runs use the pinned Part 2 cpmsim binary,
SHA-256 `b2d4384af06dbea8d32bc43eab539bf9e4857e74780577a249d0e8c5e22c955d`.
Commands are in [Part8-Reproduction.md](Part8-Reproduction.md). The companion
report includes manifests, tested images, generated sources, fixtures,
transcripts and the still-open checksum reproduction.

These tests do not qualify actual Model 4 hardware, ROM, native ZSM4 builds,
private utilities/installers, arbitrary third-party modules, every disk-fault
timing, or complete stack/workspace exhaustion. Stateful service checks are
not an exhaustive byte-for-byte proof for every possible active provider.
No elapsed-time performance result is claimed.

## 7. Decision and next bounded part

Retain the integrated RSX prototype and its unchanged memory budget. Keep
CCP/CPX migration and checksum enforcement explicitly open; do not promote the
profile to general release support yet.

**Proposed Part 9:** design and measure the command-loader solution, comparing
compact refactoring against a verified second stage. Include carrier binding,
payload integrity, repeated-read consistency, failure recovery and exact
permanent/temporary memory costs in the same decision. First test whether
56 KiB unloaded and 53 KiB with the screen pair can be preserved. Do not
silently trade away the recovered RAM to accommodate checks.

This is a useful point for an Astra High architectural critique if the
maintainer wants one. Part 8 itself is complete as a bounded assessment; it
does not claim the larger migration is complete. Pause here for review and
Work-credit assessment before starting Part 9. Model 4 window mapping remains
a separate future investigation.
