# Unloadable monitor backend prototype and cost audit

2026-10-16. **Prototype evidence, not a production implementation or frozen ABI.**

## Finding

An unloadable hardware backend is a workable direction. Three assembled
personality prototypes run unchanged against both a Model 4 video backend and
an ANSI-host backend. Both backends reside in ordinary RSX allocations, not
permanent BIOS space. Actual production-manager allocation/removal tests return
to 54,273 bytes of TPA (53K + 1 byte) after removing the pair.

This fixes the architectural separation missing from the existing monitor work:

```
CP/M application -> terminal personality -> screen backend -> actual display
                   ADM3A / VT52 / ANSI    Model 4 / ANSI host
```

The personality interprets what the application means. The backend implements
screen operations on the actual display. An ANSI host backend may therefore
render any of these personalities, while the same ANSI personality can render
on Model 4 through its video backend. No application-specific terminal
translation is built into the emulator. Only one personality is active.

The existing BIOS hooks remain the route to the active personality and the raw
input/basic-console fallback. No second permanent BIOS pointer is needed by this
prototype: the personality owns a backend-reference word in its own allocation.

## What was built

`tools/prototype_monitor_backend.py` builds five audit-only BRSX v2 modules:

| Module | Role | Payload | Allocation including callable descriptor | Carrier file |
| --- | --- | ---: | ---: | ---: |
| PADM3A | Portable MM/ADM3A subset | 520 | 768 | 1,056 |
| PVT52 | Portable VT52 subset | 475 | 512 | 1,011 |
| PANSI | Portable ANSI subset | 465 | 512 | 1,001 |
| PM4SCR | Model 4 screen backend | 179 | 256 | 715 |
| PANSCR | ANSI-host screen backend | 292 | 512 | 828 |

All values are bytes. For each personality, **the same exact assembled payload
and carrier** are used on both backends. Tests additionally relocate the pair
from bases 6000h/6500h to 8101h/8701h. Artifact hashes and measurements are written
to `build/audit/unloadable-monitor-backend/result.json`.

These are new partial prototypes. Their sizes are not estimates of fully
converted shipping personalities. In particular, omitted controls/replies must
not be counted as optimization savings. The common prototype source retains
some unused routines to make the experiment easy to inspect.

The Model 4 backend contains the hardware video addresses and imports current
BIOS cursor variables from its listing. It is build-matched platform code;
those imports must be validated/versioned before production use. The portable
personality contains neither video addresses nor platform symbol imports.

## Proposed screen interface exercised

This private candidate interface is deliberately small. It is not yet a public
BetterCP/M ABI or a general TCAP/profile facility.

| Operation | Action |
| ---: | --- |
| 0..5 | Existing raw/basic console operations, delegated through MONRAW |
| 6 | Set cursor: B=row 0..23, C=column 0..79 |
| 7 | Write C at cursor without advancing; bit 7 requests reverse glyph |
| 8 | Erase cursor through end of line, preserving cursor |
| 9 | Erase cursor through end of screen, preserving cursor |
| 10 | Scroll the full screen up one row, preserving cursor |
| 11 | Scroll the full screen down one row, preserving cursor |
| 12 | Return candidate version/80x24/operation-mask descriptor |

Callers treat registers and flags as scratch and balance their stack. Backend
callbacks allocate nothing, perform no disk I/O and do not invoke BDOS. State is
owned by the appropriate RSX. Erasure currently uses normal spaces; MM reverse
fill semantics are an explicitly unimplemented interface requirement.

The personality owns cursor policy: MM wraps and backspaces across rows; VT52
holds at the right margin and clamps left movement. This distinction survives
backend sharing. The ANSI backend cancels host delayed wrap after writing a
cell. Its scrolling uses an 80x24 host region and restores full margins; custom
host margins are not preserved. It requires an ANSI-capable host endpoint.

## Executed evidence

Run with the existing monitor test environment (pyte 0.8.2):

```
/private/tmp/vt52-qualification-venv/bin/python tools/prototype_monitor_backend.py
```

A newly created environment can instead install `tools/requirements-monitor-tests.txt`.
The tool requires the existing Model 4 BIOS and the cpmsim BIOS audit build at
`build/audit/release-090-z80pack`, plus the production Stage-3 manager artifacts.

Twelve assembled personality/backend runs (3 personalities x 2 backends x 2
placements) pass addressing, printable output, differing right-margin policy,
erase-to-line/screen, bottom scrolling, interrupted-parser recovery, reverse
text for ADM3A/ANSI and reverse scrolling for VT52. The test compares Model 4
video memory with expected screen cells and ANSI output with an independent
pyte display. No physical-emulator or real-terminal display claim is made.

The earlier primitive-only `tools/audit_vt52_screen_backend.py` also executes
9,600 Model 4 operation cases across every screen position, checking cursor
preservation, erasure, scrolling and video-boundary sentinels. Its 167-byte
standalone candidate becomes a 179-byte RSX payload with the standard dispatch
header/chain. It does not need to be installed permanently in BIOS.

### Actual allocation and unload costs

The normal production manager loads these ordinary callable carriers and removes
them again, with controlled file I/O. It is not a host arithmetic simulation.
It includes existing RSX profile overhead and page-rounded allocations:

| Personality | Model 4 backend: loaded TPA | ANSI backend: loaded TPA |
| --- | ---: | ---: |
| PADM3A | 52,225 bytes (51K displayed) | 51,969 bytes (50K displayed) |
| PVT52 | 52,481 bytes (51K displayed) | 52,225 bytes (51K displayed) |
| PANSI | 52,481 bytes (51K displayed) | 52,225 bytes (51K displayed) |

Every combination restores **54,273 bytes / 53K displayed** after removal.
BIOS/BDOS/layout artifacts are unchanged. These numbers describe prototype
modules, not the eventual complete provider footprints.

## Binding and manager cost

The production manager does not currently understand a backend dependency.
The allocation probe deliberately confirms that removing the backend while
retaining the prototype personality succeeds. This is a demonstrated missing
safety check, not an acceptable production loading sequence.

The prototypes advertise ordinary `PMON` and `SCRN` services, avoiding the
reserved production `MCON` identity. They are never bound into BIOS monitor
routing. This prevents experimental modules from implying completed production
monitor compatibility.

An assembled **219-byte candidate binding preparer**, including private scratch,
processes normalized prospective-profile records. Fifteen tests cover matching
and reversed load order, backend-only/empty profiles, missing backend,
duplicates, incompatible platform/ABI, invalid slot/entry bounds and address
wrap. Failed preparations leave live payloads untouched. The twelve rendering
runs execute this preparer to obtain the final backend reference; the harness
then applies that reference before entering the personality.

That final store is host modeled. The prototype does **not** claim transaction
integration, rollback, actual manager-driven rebinding after movement, or a new
shipping metadata format. Ordinary internal runtime-pointer repair cannot
repair this cross-module reference: it must be rebound from the final plan.

Measured overlay headroom in the current artifacts:

| Component | Bytes / enforced slot | Spare |
| --- | ---: | ---: |
| RSX slot/service preparer | 669 / 1,024 | 355 |
| Metadata normalizer | 881 / 1,024 | 143 |
| Commit coordinator | 1,007 / 1,012 | 5 |
| Model 4 permanent BIOS | 757 / 757 | 0 |
| Permanent extension services | 425 / 425 | 0 |
| BDOS | 3,452 / 3,454 | 2 |

The 219-byte preparer is smaller than the slot preparer's 355-byte headroom.
That is a useful budgeting result, **not proof that a complete integration fits**:
normalizing dependency metadata, carrying the fixup through staging, applying it
after relocation and handling all failure paths still have to be costed. The
commit coordinator's five spare bytes make careless append-only integration
particularly unsuitable. Its code is already reloadable; a bounded refactor or
another management overlay is preferable to permanently enlarging the BIOS.

No permanent growth was needed by the experiment. Zero permanent growth remains
the production design target, not an already-qualified production guarantee.

## Required production rules

- Exactly one active personality; at most one selected compatible screen backend.
- Validate backend identity, ABI, geometry and required operations before detach.
- Reject a prospective profile leaving a dependent personality without a backend.
  Explicitly removing personality first, then backend, is valid.
- Re-resolve the reference on every profile reconstruction, including movement
  caused by unrelated RSXs. Never cache an untracked address from Function 182.
- Validate the frontend-owned reference slot and final target entry. Keep the
  cross-module word out of ordinary self-relative pointer repair.
- Prepare all fallible work before detach. Preserve the old binding and state
  when validation or preparation fails. Apply only validated stores during the
  existing disk-free commit, with the basic console selected until publication.
- Backend code survives application execution in RSX memory; CPX/CCP scratch
  cannot serve as its storage. Removal recovers its actual allocation.

A narrowly versioned dependency/binding metadata contract is required. Unknown
metadata records must remain rejected by old validators. Existing carrier
initialization/shutdown fields must not be assumed to provide callbacks that
production does not implement. One possibility is a monitor-specific frontend
binding declaration, rather than adding a general dependency framework for 1.0.

## Remaining implementation/qualification

The prototypes demonstrate the architecture and allocation policy, not complete
terminal compatibility. They omit large parts of the established contracts:
MM insert/delete, cursor visibility and reverse erase fill; VT52 identification
and its ordered reply queue; and most ANSI CSI/private modes, string containment,
queries and replies. ANSI parsing here only exercises explicit two-coordinate
addressing, selected erasure and single-parameter SGR. Tab, malformed sequences,
input routing and cursor presentation also need full contract coverage.

Production work should retain the settled parsers/reply queues and replace their
rendering targets with the shared operation boundary. Extend that boundary to
cover the actual required semantics before converting all three providers.
For example, reverse erasure and insert/delete cannot silently disappear because
the first prototype lacks an operation for them. Measure speed as well as size:
this simple prototype performs a position operation after each character.
The measured ANSI transport uses 1502, 1503 wire bytes to print an 80-character
line across the three personalities, because it redundantly emits positioning
and attributes. Model 4 writes cells directly with no transport bytes. The
serial path is deliberately unoptimized and needs batching/cached attributes
before production use; a smaller resident footprint must not hide that cost.

Recommended next step: freeze the bounded backend and monitor-specific binding
contract, prototype full transaction integration within management-overlay
budgets, then migrate the established personality implementations and qualify
both platforms. The 53K unloaded requirement remains unchanged. A general TCAP
database, automatic terminal discovery and multiple active personalities remain
outside this 1.0 proposal.
