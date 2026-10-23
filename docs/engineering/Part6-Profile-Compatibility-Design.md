# Engineering Assessment Part 6: profile compatibility and build contract

Date: 2026-10-23. Status: assessment complete; design proposed for maintainer review.
Part 5 is approved. This part changes documentation only. The accepted core 1.0
baseline remains `3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## Finding and recommendation

Proceed with explicit target profiles, but qualify the complete loading and
recovery path before calling the full-RAM profile supported. A check on
`R3PACK.RSX` alone is insufficient. Private code also enters through reserved
tracks, the CCP, address-bound CPXs/RSXs, and system utilities.

The memory result from Part 5 stands: 57,344-byte unloaded COM capacity, a
3,072-byte gain on cpmsim. The final cost of compatibility enforcement has not
been measured. This part measures component constraints and small candidate
formats/routines; it does not implement or boot an integrated hardened OS.

Repository state changed during this assessment: GitHub merged the Part 5
prototype as PR #452, commit `618ed14b94a438764f2e33a76cabd7e90ea649a4`, after
the SQ/USQ work in PR #451. The local working repository was synchronized to
that history. Preserve both merges. The prototype is now on main, but its
qualification limits still apply. In particular, the globally shifted layout
must not be mistaken for a qualified Model 4 layout or ROM build.

## 1. Loading boundaries that need coverage

Source evidence is pinned to prototype commit
`27b73a54f4838c4e09604563c3fc166572a115f3`; relevant core files are unchanged by
the two merges. The evidence bundle retains the inspected sources and hashes.

| Path | Present behavior | Required contract |
| --- | --- | --- |
| Warm/cold command reconstruction | Platform loader reads a reloader and jumps to it | Check resident-compatible manifest and complete payload before the jump; command environment may already be disposable |
| CPX control | Extension calls BIOS +57, then CFG +9 | Validate control image before its first instruction |
| RSX manager entry | BIOS +60 first loads the reloader/selector into CFG; selector reads into manager memory | Validate selector/bootstrap before use; preserve the active resolver before manager replacement |
| R3PACK | Copied reader checks length and record completion, then installs the selected slot | Validate contract, slot identity, bounds and payload integrity before copying executable bytes |
| RSX failure/direct-query recovery | Entry and extension can reload resolver selector 3 from disk | Recovery must not depend on another fallible read from the medium being rejected |
| CCP / modules | CCP has fixed core references; relocatable modules may retain fixed external references | Check private binding before initialization, dispatch, linking or publication |
| System utilities | CONFIG, STAT, SYSBUILD and SYSGEN contain layout-dependent references or package assumptions | New private utilities must check running-system compatibility before private access or writes |

The raw selector currently writes the first seven cpmsim records directly into
the manager. Its last-record handling preserves the live return frame, not the
old resolver image. A late read failure can therefore leave manager bytes
replaced. This is a source-derived recovery weakness; Part 6 does not claim a
new live reproduction of that failure.

RCP calls `LY_BIOS+66`; FDF refers to `LY_BDOS`, `LY_TAB` and `LY_TPA`; M4SCRN
incorporates BIOS cursor/column addresses generated from the listing. Their
carriers differ between the two layout builds. Relocation of a module's own
addresses does not relocate these external references. Conversely, identical
binaries across two layouts are useful evidence, but do not prove portability
to other machines or hardware bindings.

## 2. Three identities with separate purposes

1. **Public interface requirements:** CP/M, CPX/RSX and advertised service ABIs.
   Ordinary applications and public-interface-only modules should not be tied
   to a particular core build.
2. **Private compatibility ID:** 16 bytes derived from a canonical, versioned
   contract containing platform and memory mode, resolved addresses, private
   structure/entry offsets, capacities, scratch ownership, carrier schemas,
   hardware bindings and explicit private-ABI epochs. All address-bound
   artifacts require an exact match. An address match alone is insufficient.
3. **Artifact provenance and integrity:** source revision plus dirty-source
   digest, tool versions and SHA-256 outputs in the build manifest; compact
   CRC-16 checks on disk payloads at runtime. A checksum is not a compatibility
   declaration. Neither mechanism is intended as authentication against
   deliberately forged executables.

Exclude timestamps and documentation-only revisions from the compatibility
ID. Compatible code fixes may share an ID but have different payload checksums.
A changed private calling convention must change its epoch even if addresses
stay fixed. CI should require an explicit compatibility review for changes to
private implementation inputs; hashing cannot infer semantic ABI changes.
The reduced contract in the format experiment is illustrative, not a complete
production contract or an assigned release identity.

Keep one authoritative resolved contract per build. Generate assembler
constants, slot records, native includes, pack headers and installation
metadata from it. Never compute competing identities independently in builders.

For new private COM utilities, a candidate discovery mechanism is a length- and
version-checked `BCPI` extension immediately after Function 180's existing
`BV` record table, with a 16-byte ID. Its proposed size is 22 bytes. Existing
records keep their pointer-based interpretation; existing VER behavior must
be tested before adopting this extension. An old descriptor without the
extension causes the new utility to refuse private operations. No new BDOS
selector is assigned here. Placement, legacy-reader compatibility and all
associated resident costs remain implementation gates.

Unmodified old private COM utilities cannot be made self-checking by changing
their packaging. CP/M can execute arbitrary COM code; this design does not
claim to recognize every old or renamed private utility. Supported profile
media must replace those utilities coherently. Ordinary public-interface
applications remain outside this private-ID requirement.

## 3. Candidate container and module formats

### R3PACK: metadata outside executable slots

Use a 512-byte versioned header followed by the existing fifteen 1,024-byte
slots. Total size becomes 15,872 bytes / 124 CP/M records, still below the
16 KiB extent boundary used by the present reader. Existing slot payloads and
their entry offsets need not move within their execution regions. Record
starts become `4 + 8 * slot` and must be generated everywhere.

| Header offset | Bytes | Candidate meaning |
| --- | ---: | --- |
| 0 | 4 | `BCPH` |
| 4, 5 | 1 each | Header version 1; kind 1 for R3PACK |
| 6 | 2 | Header size 512 |
| 8 | 16 | Private compatibility ID |
| 24, 26, 28, 30 | 2 each | Slot count 15; slot size 1024; total records 124; flags zero |
| 32 | 2 | Header CRC-16 with this field zeroed |
| 34 | 120 | Fifteen 8-byte entries: slot, destination class, start record, length, payload CRC |
| 154 | 358 | Reserved zero bytes |

CRC convention in the experiment: polynomial 1021h, initial FFFFh, unreflected,
no final XOR; `123456789` produces 29B1h. Validate fixed coordinates against
the generated contract, rather than accepting a header-directed arbitrary
destination. Verify a freshly read header on each open and the actual staged
payload before installation. A verified header followed by an unchecked
payload is not enough. Unknown versions/classes/flags fail closed.

The present file service reads 512 bytes per NEXT call. A 128-byte header would
save disk bytes but complicate this interface; 512 bytes is the first candidate
to implement. It adds one NEXT call per uncached helper load: 12 instead of 8
payload/header records, excluding directory I/O. Do not describe that as a
measured latency increase; emulator/hardware timing remains to be measured.

Do not hide identity bytes in helper padding. R3COMIT has only 5 safe trailing
bytes, and the composed R3MOVE has 6. The manager's final 12 bytes have existing
frame/gateway ownership. Headerless old packs are rejected on new profiles.

### Modules: preserve relocation-header capacity

A trial 20-byte extension to the fixed relocation prefix fails the size goal:
ANSISCRN already uses all 232 relocation entries in a 512-byte header; RCP has
741 entries and would require a 2,048-byte header, beyond its current
1,536-byte policy limit.

Prefer mandatory binding metadata outside the relocation directory, guarded
by new carrier versions. Candidate forms are BRSX v3 with a new BMET major and
an 18-byte binding-record payload (schema, class, 16-byte ID), and BCPX v2 with
a 20-byte binding trailer after command metadata. A private CCP carrier also
needs an explicit new version/binding check. Class PUBLIC requires a zero ID;
class PRIVATE requires the matching contract. Unknown/missing declarations
are rejected. Public service-call ABIs and runtime module headers need not
change merely because their disk carriers gain binding metadata.

An isolated packaging experiment on 16 existing RSX/CPX carriers adds 20 bytes
each with no payload, relocation-header or rounded runtime-allocation change.
For this sample, none requires an extra 128-byte file record. This is not a
loader implementation, and the experiment's binary-equality classification
must not substitute for a source/binding audit.

**Migration cost:** old BCPX/BRSX formats do not declare whether they contain
private external references. A new full-RAM profile must not silently treat
all old carriers as public. Rebuild/repackage audited modules with an explicit
declaration; retain the old formats in the pinned legacy profile. Do not
blindly stamp an unknown third-party binary as PUBLIC. Exact version numbers
and wire fields remain proposals until implementation review and native parity.

## 4. Failure behavior and temporary-memory ownership

The resident loader must contain the initial verification logic and anchor;
it cannot rely on code loaded from the unverified medium to validate itself.
Use a versioned system-carrier manifest for reloader, control, bootstrap,
entry and resolver images. Validate it and the complete staged image before
execution. On cpmsim the formerly used carrier positions at records 84 and 92
contain padding/gateway images; they are candidates for a verified bootstrap
and manifest without adding reserved tracks. That is a placement opportunity,
not proof that all new code fits.

For RSX mutations, validate the caller's work range and preserve a usable
resolver **before** overwriting the manager. ENUM/QUERY and no-op operations
must not acquire a new workspace requirement: route them through a verified
control/bootstrap path that leaves the manager intact. Do not assume every
Function 177 request supplies transaction RAM.

Before commit, any missing, foreign, truncated or corrupt input must leave the
profile, provider state, pointers, memory boundary and usable resolver intact.
After live movement begins, retain the existing rule: no disk reads or other
fallible preparation. Warm reconstruction cannot promise to return to a
discarded command environment; a checked retry/halt path is appropriate if
the required compatible reloader or CCP is unavailable. Never jump into
partially loaded recovery code.

The first workspace candidate expands the copied-reader allowance and charges
256 additional temporary bytes, with the same 7000h transaction ceiling:

| Offset from scratch base | Size | Proposed owner |
| --- | ---: | --- |
| 0000h–03FFh | 1024 | Staged incoming helper; header scratch before payload read |
| 0400h–05FFh | 512 | Copied reader and validation code |
| 0600h–06FFh | 256 | Reader state and bounded downward stack |
| 0700h–0AFFh | 1024 | Saved CFG image |
| 0B00h–0EFFh | 1024 | Preserved or prefetched compatible resolver |
| 0F00h–0FFFh | 256 | Isolated manager frame/stack band |

This changes total scratch from 0F00h to 1000h and moves the prospective-data
ceiling from 6100h to 6000h when the effective work ceiling is 7000h. It does
not reserve that RAM permanently or directly lower the advertised TPA, but it
can reduce the largest transaction that fits.

One resolver copy can serve both rollback and post-commit only if its request
state is fully reset and it derives live bindings from the current published
profile on every call. The current resolver contains mutable working fields;
that reuse must be established and tested, not inferred from its name. With
an existing profile, preserve the current compatible resolver; with an empty
profile, prefetch and verify it before commit. If this cannot be proved, a
separate old/new resolver copy costs another 1,024 temporary bytes: total
scratch 1400h and data ceiling 5C00h. Return that larger cost for review rather
than silently consuming it. Stack-depth and overlap proofs are still required.

## 5. Measured costs and limits

| Item | Evidence / cost |
| --- | --- |
| Copied reader today | 242 of 256 bytes; 14 bytes free |
| R3 entry today | 660 of 1012 safe bytes |
| Isolated CRC-16 routine | 30 assembled bytes; 18 CPU-fixture cases match Python CRC, including all 15 slots |
| Isolated 16-byte comparator | 11 assembled bytes; equality and all 16 differing-byte positions tested |
| Proposed discoverable resident ID record | 22 data bytes; layout and integration pending |
| Simple reader-plus-primitives arithmetic | 242 + 30 + 11 = 283, before header parsing/glue; existing 256-byte allowance is not enough for this direct composition |
| cpmsim resident slack | BIOS 133 bytes; disk 26 bytes; several other components exactly fill their allocations |
| cpmsim control/reloader | Control 907/1024; reloader 924/932; selector 55/92 |
| Proposed R3PACK disk growth | 512 bytes; no executable-slot growth |
| Proposed transaction scratch | +256 bytes conditional on safe resolver reuse; larger fallback explicitly unapproved |

The 41 bytes of assembled primitives and 22 bytes of identity data are not a
63-byte completed solution. Call glue, bounds, saved state, diagnostics,
manifest parsing, raw-loader staging and module checks remain. Slack in one
region cannot automatically pay for growth in another. No exact hardened TPA
or full runtime performance claim is made.

Host format probes accept all 15 matching slots and reject all 15 foreign-ID
slots, all 15 legacy payloads under the current header, 512 one-bit header
mutations, 60 sampled payload mutations, 5 malformed directories even after
their CRC is recomputed, 124 truncated-record lengths and an extra record.
The old headerless pack is rejected. These tests exercise the candidate Python
format validator; they do not establish integrated Z80 loader or recovery
correctness. The two small Z80 routines were separately assembled and executed
in the existing CPU fixture. No new cpmsim boot or native-ZSM4 parity campaign
was run in Part 6.

## 6. Production build contract

| Profile | Admission status |
| --- | --- |
| cpmsim / legacy RAM | Pinned core reference and regression control |
| cpmsim / full RAM | Part 5 prototype; compatibility/build integration pending |
| Model 4 / legacy mapping | Preserve its qualified layout independently |
| Model 4 / full RAM | Reject as unsupported until the deferred bank-switching investigation is qualified |
| ROM variants | Explicit separate profiles and execution-in-place gates; never inferred from RAM success |

Build order: resolve target contract, generate includes, assemble components,
check bounds, derive actual platform bindings, build bound modules, package
carriers with checksums, compose media, then verify read-back against the
manifest. Derive compatibility from the pre-assembly contract and relevant
binding offsets, not from checksums that depend recursively on their own
embedded value. Hash final payloads only after binding/identity emission.

All outputs, intermediates, logs and test fixtures belong under a profile- and
toolchain-specific directory. No tool may silently fall back to shared
`build/system` or another profile's artifacts. Until the existing import-time
global `system_layout.py` interface is replaced, complete isolated staging
trees remain the safe bridge used in Part 5. Parallel builds must not rewrite
the source-tree layout include. Unknown profile/mode combinations fail before
assembly. Remove the cpmsim dependency on producing unqualified Model 4
artifacts just to obtain common utility metadata.

The resolved manifest includes profile/contract IDs, source provenance, tool
versions, origins/endpoints/capacities, header versions, actual artifact hashes,
feature/startup selections and qualification status. Represent the exclusive
10000h endpoint as a host integer/count, never as a wrapped 16-bit address.
Preserve explicit reserved-byte counts for native assembler conditions.

The source disk currently includes prebuilt R3PACK and individual helper
images. A native core rebuild does not, by itself, demonstrate that every
private artifact was rebuilt for its profile. Native build/import paths must
use the same generated contract and validate every imported helper. A complete
self-hosted changed-contract build additionally needs native contract/pack
generation, or an explicitly declared external generation step; do not claim
that capability from the current source disk. Identical compatible native and
host builds should share a compatibility ID even though tool provenance differs.

SYSBUILD, SYSGEN and disk builders must reject a mixed bundle before writing.
CONFIG's mutable startup/settings records need a separate validated schema;
changing a startup command must not invalidate an immutable executable-set
checksum. Installation must preserve unrelated filesystem data and validate
the final read-back. Diagnostic helper files are not interchangeable runtime
inputs merely because their extensions match.

## 7. Next bounded work and acceptance gates

Recommend Part 7 as an isolated **cpmsim profile-selection and trusted-loader
prototype**, with a review pause before general module migration or Model 4
work. Establish explicit legacy/full-RAM selection and stop unsupported targets
from inheriting the full-RAM layout. Implement the manifest/bootstrap/R3PACK
path, preserving live resolver recovery, and report its actual resident and
temporary cost. If it needs more scratch than the 1000h candidate, stop at the
measured tradeoff for review. Module-carrier migration and native distribution
qualification can then be separate bounded increments.

Acceptance requires all of the following before supported-profile adoption:

- Matching and deliberately mixed raw carriers, helper slots, CCP, modules,
  utilities and native bundles; same-layout/different-private-ABI rejection.
- Failures at each read boundary and after media changes; rejection before
  execution/publication, with exact retained state and usable service lookup.
- ENUM/QUERY/no-op calls with no mutation workspace; malformed workspace and
  high-water stack tests; no post-commit disk I/O.
- Legacy control parity, repeated isolated/concurrent builds, cross/native
  parity, package read-back and wrong-profile refusal before writes.
- Actual maximum COM execution/return after hardening, plus unloaded, shipped
  startup, explicit monitor and future-default budgets. Keep NDR/datestamping
  and the four-provider limit visible; do not spend their headroom implicitly.

The architectural choices here warrant the previously suggested Astra High
critique if desired, especially resolver reuse and carrier migration. A model
review does not replace the implementation measurements. Part 6 ends here.
