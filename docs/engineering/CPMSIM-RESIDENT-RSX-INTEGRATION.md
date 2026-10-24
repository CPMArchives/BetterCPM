# cpmsim build integration: resident services and RSX reconstruction

24 October 2026. Fourth integration checkpoint; ready for maintainer review.
The previous commit `a015119` was already pushed and was verified before this
increment began. Full checked distribution integration remains pending.

## Implementation

`tools/build_checked_resident_rsx.py` now builds the checked resident services,
RSX transaction entry, copied reader and reconstruction pack from maintained
sources in a prepared profile workspace. It also builds the previously migrated
command stages. It does not construct or publish checked distribution media.

The shared assembly sources select checked behavior with `BP_CHECKED` conditions.
Default builds explicitly select zero; prepared checked profiles select one.
This keeps the common routines together while preserving both implementations.
The checked path includes the CFG-based initial manager, 4 KiB transaction
workspace, resolver backup/restore, 512-byte copied-reader allocation, pack and
per-slot checksums, private binding, BRSX3 carrier admission and BMET2 metadata
handling. The default BRSX2 path remains available.

The host builders generate identity/pack-checksum constants and link origins.
They do not rewrite source files or patch assembly instruction sections.
Three labelled BIOS checksum operands are fixed up after their complete carrier
bytes are known; the builder verifies each operand's opcode and carrier size.
The pack excludes its transaction entry, so computing the pack checksum before
assembling the entry avoids a circular checksum dependency.

The CRC, identity-compare and identity-data services occupy the same BIOS/disk
space as the prototype. Link checks enforce their addresses and require the
preceding code/state to finish before them. `checked_rsx_pack.py` emits the
bounded 15-slot directory and private first-entry/control bindings directly.
The driver requires a fresh prepared workspace and rejects partial reuse of
already built disk/stage directories.

| Profile | Component-build ID | Entry | Copied reader | Internal pack |
| --- | --- | ---: | ---: | ---: |
| `cpmsim-fullram` | `5bf8e98103676022b4a8c287c4a62112` | 893 bytes | 450 bytes | 15,872 bytes |
| `cpmsim-legacy-checked` | `9b2417624094fdae0e48bc1a17916562` | 893 bytes | 450 bytes | 15,872 bytes |

The entry remains below its 1,000-byte binding boundary, and the copied reader
fits its 512-byte allocation. BIOS occupies 757 bytes, including its existing
verification tail. These products retain the qualified layout and allocations;
this increment adds no TPA charge. It does not claim a new live checked-OS TPA
measurement.

## Verification

Every counted case passed in both checked layouts:

| Case family | Per profile |
| --- | ---: |
| Actual resident CRC/ID/gates, partial reads and disk-free restore | 109 |
| Copied reader: slot copying, header/payload corruption, failed reads and foreign packs | 302 |
| Carrier/metadata admission, binding corruption and unchanged facts on failure | 63 |
| Command stages: integrity, stream admission, relocation and allocation boundaries | 63 |

That is 1,074 emitted-code cases, plus 11 profile/contract and 13 distribution
unit tests: **1,098 counted cases**. Existing default carrier-normalization and
file-backed overlay-handoff campaigns also passed.

The resident checks execute the emitted CRC and comparison routines, rather
than substituting those services. CRC vectors include `123456789` and multiple
record-boundary lengths. Foreign IDs are rejected even when their carrier CRC
is deliberately made correct. Partial raw reads refuse admission. Resolver
restore copies the 1,012-byte prefix while preserving the final 12 bytes, with
the disk-read entry replaced by HALT to prove it is not called.

The copied reader uses the actual protected file loader and resident CRC while
a controlled disk adapter supplies failures. All 15 slots copy correctly to CFG
and through the resolver-safe path. Every selected header/slot read can fail
without publishing the destination; malformed headers, damaged payloads and
foreign packs are rejected. Carrier fixtures exercise public/private admission,
all identity bytes, short/malformed/duplicate binding records, payload checksums
and old metadata rejection, preserving normalized facts on failure. Those are
test fixtures, not newly adopted distribution carriers.

For each layout, 23 artifacts reproduce the earlier qualified reference exactly
when assembled with its reference identity. These include all internal RSX
carriers/pack, transaction entry, copied reader and four platform components.
The current BIOS differs only in its three identity-dependent checksum operands;
the disk component differs only in its 16-byte private ID. Independent repeat
compilation reproduced 19 RSX artifacts per profile. Source-closure checks and
prepared-cache reuse passed after the tests.

The default regression checks caught a missing profile include in the extracted
reader subassembly. Adding the include restored the default build. The ordinary
default cpmsim distribution then rebuilt and boot-qualified successfully, with
its 30-file, 368,640-byte image unchanged:
`d806fa1911fa18623f9d7495d561cae57d6623bb66fbe68e85f3b355a866ee96`.
The default Model 4 distribution also built and passed filesystem, file integrity,
CONFIG fingerprint/cold-patch and DMK structure checks. Its 1,020,496-byte image
is unchanged: `fd2873d3c1ac3c428ef1ba1bc290d015167cf50961c49f0b348cef88b628d642`.
Live Model 4 boot was not retried because the reference host-launch failure was
already established at the preceding checkpoint.

The [machine-readable evidence](CPMSIM-RESIDENT-RSX-INTEGRATION.json) retains the
1,093-file input closure, component hashes, per-case results, reference/repeat
comparisons and default image checks. Tests ran on `a015119` plus the exact
recorded working-tree input bytes, preserved by this checkpoint commit.

## Reproduction and remaining work

Prepare fresh workspaces for both profiles using the ordinary distribution
tool's `--prepare-profile --work` options from the
[profile-input checkpoint](CPMSIM-BUILD-PROFILES.md). From each prepared
`WORK/profiles/PROFILE/z80pack/` directory:

```sh
export BETTERCPM_BUILD_CONTEXT="$PWD/build/profile/context.json"
python3 tools/build_checked_resident_rsx.py
python3 tools/test_checked_resident_rsx.py --reference /path/to/matching-reference-profile --foreign-pack /path/to/other-profile/build/system/R3PACK.RSX --output "$PWD/build/z80pack/rsx-qualification.json"
```

Build both profiles before testing cross-profile refusal. The reference argument
identifies the frozen earlier full-RAM or legacy checked build, including its
`assessment-profile.json`; it is comparison evidence only. Run the existing
command-stage qualifier separately for its 63 cases. Native assembler builds,
physical hardware execution, a new live checked-OS transaction/rollback campaign
and whole-OS stack bounds are not qualified by these component tests. The
earlier measured two-byte BDOS stack margin remains a limit to track.

Next, migrate direct RSX/CCP/CPX carrier generation, checked package/install/export
and private utility guards, then perform full checked distribution integration
and acceptance. Existing full-distribution guards remain in force. Historical
assessment reproduction uses its pinned source snapshots; ongoing production
integration uses the maintained profile-aware builders. HELLO development
fixtures remain excluded from distribution. Core 1.0 remains `3b2d2d7`.
