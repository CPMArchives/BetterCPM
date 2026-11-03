# Platform roadmap

Status reviewed: 3 November 2026.

This is a provisional platform inventory and planning order. It does not add
release gates or certify support. The [1.0 roadmap](releases/1.0-ROADMAP.md)
and [implementation contracts](releases/1.0-IMPLEMENTATION-CONTRACTS.md) retain
authority over 1.0 scope.

## Priorities and evidence

- **P0 — existing baselines:** maintain Model 4 and cpmsim and finish their
  established release acceptance work.
- **P1 — near term:** integrate or investigate the reported ports and close
  specific boot/status gaps.
- **P2 — planned:** select reproducible configurations, then implement and test.
- **P3 — exploratory:** retain candidates without starting a port investigation.

All P0–P3 assignments are provisional, not commitments, dates, or release
assignments. All current testing is emulator-based. No physical-hardware
validation is claimed for any port. cpmsim and MyZ80 are emulator-native
targets: physical-hardware validation is **N/A**, rather than an outstanding
test against an equivalent physical machine.

“Emulator-validated” means only the behavior covered by retained evidence for
an identified build and configuration. A reported boot is preliminary evidence,
not compatibility qualification. “Hardware-validated” requires separate results
from a named physical machine, peripherals and media; emulator results cannot
supply that status.

## Platform inventory

| Platform | Priority | Current status and emulator evidence | Physical hardware | Next step |
| --- | --- | --- | --- | --- |
| TRS-80 Model 4 / trs80gp | P0 | Existing integrated baseline; reproducible boot and bounded emulator validation recorded. Final release acceptance remains open. | Not validated | Maintain baseline and complete the existing release checks. |
| z80pack cpmsim | P0 | Existing integrated, emulator-native baseline; bounded emulator validation recorded. Requires the pinned patched emulator, including geometry interface v2. Final release acceptance remains open. | N/A | Maintain reconstruction and evidence for the exact tested images/emulator. |
| TRS-80 Model II | P1 | a-griff third-party port reported; integration and qualification pending. Not an integrated or qualified mainline target. | Not validated | Obtain and review the port source, provenance, build instructions and emulator/image identity; integrate through the shared platform boundary and retain test evidence. |
| TRS-80 Model 4D | P1 | Preliminary emulator boot success reported; no separate Model 4D qualification established. | Not validated | Reproduce with identified emulator, ROM, drive configuration and image, then run applicable platform checks. |
| TRS-80 Model 4P | P1 | ROM/boot failure reported in emulation; cause unresolved. | Not validated | Record and reproduce the boot failure before choosing a bootstrap/adapter change. |
| Kaypro | P1 | Future targeted platform; no port work has started. No BetterCP/M boot or qualification claimed. | Not validated | Select the exact Kaypro model and emulator configuration when port work is taken up. |
| MyZ80 1.24 under DOSBox-X | P2 | Planned emulator-native target; no BetterCP/M boot or qualification claimed. | N/A | Pin MyZ80 1.24, DOSBox-X and guest configuration; examine boot, disk and console interfaces and establish reproducible tests. |
| z80pack IMSAI, Z80 configuration | P2 | Planned. Upstream source supports Z80 CPU selection, subject to build configuration; no BetterCP/M boot or qualification claimed. | Not validated | Pin a Z80-capable build and explicit CPU selection, ROM, memory, console and FIF disk setup; verify the configuration before porting. |
| z80pack Altair, Z80 configuration | P2 | Planned. Z80 mode is supported in upstream source; the existing assessment proposes `altairsim -z -F -M1` with Tarbell. No BetterCP/M boot or qualification claimed. | Not validated | Pin and verify the Z80 build/configuration, boot ROM, memory map, console and chosen disk controller; do not assume a default 8080 setup is suitable. |
| RomWBW / HBIOS | P3 | Exploratory. An emulator candidate has been found; suitability and BetterCP/M operation are untested. | Not validated | Evaluate the candidate below and select a bounded HBIOS target before implementation. |
| TRS-80 Model 12 | P3 | Exploratory. The Model II system image failed to boot on an emulated Model 12 with a reported ROM-level error. Exact message and cause are not established. | Not validated | Retain the observation; defer boot-protocol investigation until an actual Model 12 port is undertaken. |
| TRS-80 Model 16 | P3 | Exploratory; no BetterCP/M boot or qualification evidence established. | Not validated | Select the Z80-side CP/M environment and emulator configuration when this port is taken up. |

Kaypro, MyZ80, z80pack IMSAI and Altair, RomWBW, Model 12 and Model 16 are
future targets with no BetterCP/M port work started. The Model 12 image trial
was a compatibility experiment, not the start of a port. Model 4D and Model 4P
have preliminary boot observations only; no dedicated port effort or
qualification is established. Model II is the third-party-port exception,
with mainline integration still pending.

The Model II, Model 4D, Model 4P and Model 12 observations above are
maintainer-reported planning inputs from the design discussion, not newly
reproduced results or repository qualification receipts. Their recording here
does not establish that a BIOS, disk format or boot ROM is the cause of a failure.

## Evidence and configuration notes

The current baseline evidence is the
[release conformance record of 2 November 2026](engineering/Release-Conformance-2026-11-02.md).
It distinguishes suite passes, controlled/external checks, observations,
exclusions and profile differences; it does not claim 627 passes, physical-device
qualification or final release acceptance. See also the
[Model 4 installation notes](platform/MODEL4-INSTALLATION.md),
[cpmsim installation notes](platform/CPMSIM-INSTALLATION.md) and
[cpmsim adapter documentation](../src/platform/z80pack/README.md).
The [baseline platform specification](platform/Baseline%20Platform%20Specification.txt)
explains why cpmsim success alone does not establish hardware portability.

The [September third-platform assessment](engineering/POST-1.0-THIRD-PLATFORM-ASSESSMENT.md)
is source-level feasibility work, not a port validation record. It favored
Cromemco as a conventional third platform and discussed Altair/Tarbell and
IMSAI/FIF tradeoffs. That assessment remains useful background; this provisional
inventory does not silently promote Cromemco into an active port or adopt the
assessment's proposed release numbers for RomWBW.

For Z80 capability, upstream z80pack
[IMSAI I/O source](https://github.com/udo-munk/z80pack/blob/bb92b240c4c8ff0fda7d80dc23ab5ad0b0077f33/imsaisim/srcsim/simio.c)
and [Altair I/O source](https://github.com/udo-munk/z80pack/blob/bb92b240c4c8ff0fda7d80dc23ab5ad0b0077f33/altairsim/srcsim/simio.c)
include CPU switching to Z80, with build-time exclusions affecting availability.
This verifies a source capability, not a tested launch configuration. Record the
selected build options and CPU mode explicitly; historical machine names and
stock CP/M disk boot success are insufficient evidence for running BetterCP/M.

A RomWBW emulator candidate is
[avwohl/romwbw_emu](https://github.com/avwohl/romwbw_emu).
Its documentation describes banked ROM/RAM emulation and a C++ implementation
of HBIOS. Evaluate which firmware paths it actually exercises, select and pin
the emulator and ROM/disk versions, and retain reproducible boot/test records
before treating it as a BetterCP/M validation environment. This candidate
does not establish a port, real-hardware compatibility or full firmware coverage.

## Shared core and advancement criteria

Maintain one shared BetterCP/M core across ports. Keep machine-specific
bootstrap, console, disk/controller, memory-map and optional clock behavior
behind the existing platform/BIOS interfaces. Integrating a third-party port
must not create a separate CCP/BDOS/core fork. Any required common-interface
change needs its own justified design and regression evidence.

Before advancing a platform from a report or plan to emulator-validated status,
retain the source revision, emulator build/options, ROM identity, image hashes,
drive/controller setup, commands, expected results and actual transcripts.
Cover cold/warm boot, console and transient execution, file read/write and
integrity, applicable disk configuration/media/error behavior, and relevant
compatibility/regression checks. State exclusions explicitly and keep boot-only,
bounded functional validation and release qualification distinct. Physical
hardware results, if later supplied, must be recorded separately.

This document records future work. Open an actionable issue only when a bounded
piece of port work is selected; the inventory itself does not require speculative
issues or changes to the shared core.
