# Cromemco engineering checkpoint — 28 November 2026

**PASS: hardware bring-up and bounded OS integration. Release qualification remains open.**

The [platform target sheet and reproduction instructions](../../../../src/platform/cromemco/README.md)
define the scope. This is the common BetterCP/M 1.3 source tree with a Cromemco
platform adapter, based on `90a766a29fe210b1f4082c8b6449ea4c705813a6`.
Exact prepared source hashes are in `engineering-build.tar.gz` →
`profile-state.json`; candidate/contract hashes identify the modified source
closure, rather than claiming that the baseline commit alone contains this port.

| Retained evidence | Content |
| --- | --- |
| `emulator-build.json` | Pinned z80pack revision, serial build command, modified host configuration hashes, executable hash |
| `hardware-result.json` | ROM boot, recovered upper 16 KiB, console, four-drive read/write and complete-image comparison, invalid addresses and three media fault cases |
| `hardware-artifacts.tar.gz` | Bootstrap/probe source, binaries/listings, diagnostic media, configuration and all hardware transcripts |
| `engineering-build.tar.gz` | Exact prepared-source inventory, generated profile, build transcript, assembled components/listings, candidate manifest, SYSTEM.SYS, four engineering images and diskdefs |
| `system-result.json` | OS checks, full candidate identity, file hashes and carrier refusal cases |
| `system-artifacts.tar.gz` | Private tested media, console transcripts, cpmtools extractions and damaged-carrier cases |
| `manifest.json` | Artifact lengths/hashes and host check results |

The emulator cold-boots via RDOS 2.52 and the new 0080h bootstrap. The bootstrap
removes ROM and loads the shared checked system. The guest verifies **57,344
bytes maximum loadable COM**, overwrites the transient region and reconstructs
successfully, and restores 56 KiB after ECHO RSX load/call/unload.

B–D each receive a 140-record file (17,920 bytes) through BDOS, crossing extents;
independent cpmtools extraction matches the expected byte pattern. The test
checks geometry discovery and rejected unsupported setters, preservation of B
through warm boot, unchanged reserved system tracks and active system files,
and failure to enter the CCP after stage-one/stage-two corruption or a foreign
stage-one identity.

Host validation: 11 build-profile tests, 14 component-input tests, Python syntax
checks and `git diff --check` passed. Existing profile boundaries are included
in those checks; this checkpoint does not repeat the other platforms' guest
acceptance campaigns.

The engineering collection includes CONFIG/SYSGEN/DUP and PATH/NDR/BATCH tools,
but their full release acceptance is not inferred from mere inclusion. Remaining
gates are complete System/Utilities media, integrated display modules, saved
CONFIG, independent SYSGEN installation/cold boot, disk utility/media-change
acceptance, independent compatibility checks, release packaging and publication.
Physical hardware and other Cromemco disk geometries are outside this result.
