# BetterCP/M core 1.0 baseline

Status: accepted by the maintainer on 23 October 2026.

## Decision

The completed **BetterCP/M core OS version 1.0** is identified by commit
`3b2d2d7f4fe0472438465165f11fb550d79c8662` (short form `3b2d2d7`),
whose repository tree is `c08f35045d02e5d0b5de3f0c0914176438c1163e`.

This is the agreed source baseline for the first post-1.0 engineering
assessment. Later commits do not silently replace it. This decision does not
announce completion of the full 1.0 distribution or stop separate documentation
and utility development.

## Core and configuration scope

The baseline includes the implemented resident BDOS, BIOS/disk services,
gateway, extension services, file loader, tables, live state, persistent
command history and reserved workspaces; the reclaimable CCP/reloader and
required RCP.CPX command package; platform boot and reconstruction machinery;
and CPX/RSX management, selectors, CONFIG control overlay and R3PACK.RSX.

Selected optional terminal backends/personalities and clock providers belong
to the OS comparison where applicable. Their memory is charged only in the
profiles where they are loaded. Existing System Disk membership is defined by
[the distribution manifest](DISTRIBUTION-MANIFEST.md) and its machine-readable
projection, `metadata/distribution.json`, at the pinned revision. Development
build outputs are not distribution membership.

Keep these runtime profiles distinct:

- cpmsim RAM System Disk startup: `:VER /BANNER`, with no optional RSX loaded;
- Model 4 RAM System Disk startup: M4SCRN followed by ADM3A, then CLS and
  `:VER /BANNER`;
- unloaded RAM control on each platform, with no optional RSX;
- explicitly selected clock/terminal variants; and
- the existing cpmsim ROM execution-in-place profile, with separate ROM/RAM
  resource accounting.

The unloaded RAM address span is 54,273 bytes (`0100h` through `D500h`),
with a 54,272-byte record-aligned COM ceiling. These are not a claim that the
supplied Model 4 startup retains that TPA after loading its two RSXs.

## Acceptance evidence

V052 accepted revision `408560d528e353288c903289c1a799015331dc30` and its exact
System Disk images remain the historical acceptance reference; see
[the final validation record](SYSTEM-VALIDATION-FINAL-2026-10-20.md).
They are not relabeled as a new whole-release acceptance run for this baseline.

Baseline reconciliation rebuilt the pinned current source. Its BDOS, CCP,
RCP.CPX, CONFIG control overlay, RSX loader/resolver and R3PACK.RSX match the
accepted-reference artifacts byte for byte. The resident changes are the
[Model 4 keyboard correction](../engineering/Model%204%20Keyboard%20Modifier%20Qualification.md)
and BIOS implementation-version text. Current common/Model 4 and cpmsim
system-track builds, ROM generation/ownership checks and focused compiled BIOS
regressions passed during reconciliation. No new live emulator or physical
hardware qualification was performed by that reconciliation.

## Release identity and remaining work

The displayed `0.90` identifies the complete distribution under the adopted
[subsystem versioning convention](../../specifications/SUBSYSTEM-VERSIONING.md).
The maintainer chose it informally to mean close to release; it is not a
specified milestone or evidence that the core remains unfinished. Leave that
label unchanged until the complete 1.0 release is ready. Existing subsystem
interface and implementation versions remain independently meaningful.

Documentation and completion/qualification of the Utilities and CP/M Tools
disks remain separate release work. The standalone USQ utility development at
local commit `9771e488caf1e0c28323d8c20c460eb15cde07d6` is not included merely
because copies exist in an older local working tree. Diagnostic/test modules
and other unselected development artifacts are likewise not promoted into
this baseline.

Future core corrections must be recorded against a new explicit commit and
receive appropriate regression checks; the assessment must retain the original
baseline and identify any later comparison revision separately.
