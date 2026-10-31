# Post-1.0 STAT MEM Presentation Expansion Specification

## Status and release target

Draft recorded 2026-10-31 for post-1.0 consideration. Implementation is deferred;
this specification authorizes no implementation or locked-core changes.
Scope: STAT utility only.

Related documents: [existing STAT specification](128%20STAT%20Utility.md) and
[later 1.x roadmap candidates](../releases/1.0-ROADMAP.md#later-1x-candidates).

## Purpose

Expand `STAT MEM` with a compact visual overview and a clearer capacity summary
while retaining its existing detailed ownership map.

The report must describe BetterCP/M's known address-space layout accurately,
using existing layout definitions and live system metadata. It must not attempt
to discover physical memory or hardware through probing.

## Compatibility and constraints

- Preserve `STAT MEM` as the command.
- Retain the existing detailed range report and maximum loadable COM calculation.
- Require no changes to BIOS, BDOS, CCP, RSX, or CPX.
- Add no resident code, state, or memory overhead.
- Preserve existing Extension Control Block validation and applicable
  system-profile compatibility checks.
- Leave ordinary STAT disk, file, user, and device operations unchanged.
- Restore the caller's drive, user, and other system settings if any report
  operation changes them.

The expanded output is a human-readable report. Existing automated checks that
inspect its text must be updated deliberately.

## Report structure

Successful `STAT MEM` output shall contain, in order:

1. Compact address-space map and legend.
2. Existing detailed ownership ranges.
3. Capacity summary.

The default command shall display all three sections. No additional command
switches are required for this expansion.

## Authoritative region model

The compact map, detailed ranges, and summary shall derive from one consistent
set of region boundaries.

Use the existing sources:

- Canonical build-time layout definitions for fixed system regions.
- Validated live Extension Control Block fields for movable command components
  and allocations.
- The conventional word at `0006h` for the current COM loading ceiling,
  following the existing calculation.

Do not introduce a second set of approximate boundaries for the visual map.

Each address from `0000h` through `FFFFh` shall belong to exactly one reported
region. Empty regions shall be omitted. Region lengths and summary arithmetic
must represent 65,536 bytes without wrapping.

Loaded RSX and CPX allocations may remain aggregate regions; identifying
individual modules is outside this expansion.

## Compact address-space map

Display a 64-character map, with one character representing 1,024 bytes.
Addresses increase from left to right, beginning at `0000h`.

Provide a scale marked from 0 through 64 KiB at 8 KiB intervals. The complete
display must fit an 80-column terminal using ordinary printable characters.

Use these categories:

| Symbol | Meaning |
|---|---|
| `Z` | CP/M page zero |
| `T` | Transient area below the CCP |
| `C` | CCP image |
| `X` | Loaded CPX allocation |
| `G` | Dynamic CP/M gateway |
| `R` | Loaded RSX allocation |
| `S` | Protected system code, state, tables, and buffers |
| `P` | Platform-reserved address space |
| `*` | KiB containing more than one category |

A cell shall show a category symbol only when every address in that cell belongs
to that category. Otherwise, show `*`.

Several adjacent detailed regions may share one category. For example, a cell
spanning BIOS and protected disk-support regions may display `S` if both regions
are classified as protected system space.

The legend shall explain that `*` denotes a mixed ownership cell and that exact
boundaries appear below. A small region may therefore appear only within a mixed
cell; it must remain visible in the detailed report.

This map represents ownership of the current 64 KiB address space. It does not
certify installed RAM, ROM, or banked-memory capacity.

## Detailed ownership report

Retain the existing descending-address report, including:

- Inclusive high and low addresses.
- Byte count.
- Owner description.
- Distinct fixed system regions.
- Loaded RSX and CPX allocations when present.
- Dynamic gateway.
- CCP image.
- Transient area below the CCP.
- Page zero and platform-reserved regions.

Do not collapse useful detailed system rows merely because the compact map
groups them under `S`.

The detailed ranges remain the authoritative explanation of exact ownership.

## Capacity summary

Display the following values in decimal bytes:

| Field | Definition |
|---|---|
| Transient area below CCP | Size of the currently mapped region from `0100h` to the byte immediately below the CCP image |
| CCP image | Size of the currently mapped CCP image |
| Loaded CPX allocation | Size of the currently mapped aggregate CPX region; zero when absent |
| Loaded RSX allocation | Size of the currently mapped aggregate RSX region; zero when absent |
| Maximum loadable COM | Existing load capacity, rounded down to complete 128-byte records |

Preserve the existing maximum COM formula:

`floor((word_at_0006h - 0100h) / 128) * 128`

Apply it only after validating that the ceiling is within the supported layout.

Include a brief explanation:

> Maximum loadable COM includes reclaimable command memory and may exceed the
> transient area below the CCP.

These figures describe layout and loading capacity. They must not be labelled
"free RAM." Maximum loadable COM is a derived capability, not another ownership
region, and must not be added to region totals.

## Validation and failure behavior

Before printing any map or capacity values, perform existing compatibility
checks and validate the boundaries needed by the expanded report.

Reject metadata that would produce:

- Reversed or out-of-range regions.
- Overlapping ownership.
- Gaps in the complete address-space partition.
- Invalid ordering of movable components.
- A COM ceiling below `0100h` or inconsistent with the supported layout.

On failure, print a concise diagnostic and return normally. Do not print a
partial map or plausible-looking capacity figures.

Retain existing diagnostics for unsupported ECB versions and incompatible system
profiles. Additional structural validation belongs entirely in STAT.

## Operational behavior

The expanded report shall:

- Read existing layout and system metadata.
- Write only its normal transient workspace and console output.
- Perform no write-and-restore memory tests.
- Perform no arbitrary I/O-port reads or writes.
- Perform no bank switching or hardware discovery.
- Make no allocation or configuration changes.

Platform-reserved space must remain labelled as reserved; its physical memory
type must not be inferred.

## Verification and acceptance

Verify the report against supported system profiles and representative live
layouts:

- No loaded extensions.
- Loaded RSX allocation.
- Loaded CPX allocation.
- Both allocations present.
- Relocated gateway and CCP boundaries.
- Platform-reserved upper address space where applicable.

Acceptance requires:

1. Detailed ranges cover exactly 65,536 addresses without overlap.
2. Every compact-map cell agrees with the detailed region model.
3. Mixed boundary cells display `*`; empty allocations introduce no cells or
   invalid ranges.
4. Summary allocation sizes agree with their detailed ranges.
5. Maximum loadable COM preserves the established calculation and record rounding.
6. Unsupported, incompatible, and malformed metadata produce diagnostics without
   a partial report.
7. Output fits an 80-column terminal.
8. Ordinary STAT functions retain their existing behavior.
9. No locked core changes or resident-memory cost are introduced.

Use focused checks for boundary arithmetic and map rendering, together with
existing platform-level STAT qualification.

## Exclusions

This proposal does not include:

- A separate `MEM` command or extraction of `STAT MEM`.
- RAM reliability testing or ROM/empty-memory detection.
- I/O-port scanning or device identification.
- Banked-memory inventory.
- Changes to disk accounting or file counting.
- New core interfaces or ECB fields.
- Machine-readable output or additional report modes.

Any later need for broader memory diagnostics should receive a separate
specification.
