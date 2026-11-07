# TCAP carrier and resident-placement results

Status: second bounded feasibility campaign, 7 November 2026. Source baseline
is the PR #655 merge, `d1c493c537a85ecef4ea88ffb78265af00982eb1`.
This addresses the two measured blockers from the
[first campaign](TCAP-Feasibility-Results.md). Utility migrations and release
assignment remain deferred. No public TCAP ABI is allocated or delivered.

## Outcome

Both gates are resolved **in the reproducible private reference build**:

- The ordinary BRSX-v2 builder emits a valid experimental carrier with **228
  relocation words**, within the unchanged 232-word limit and 512-byte header.
  The real carrier validator, metadata validator and snapshot constructor accept
  it; corrupt payload checksums are rejected.
- The larger coordinator/guard lives in the optional personality allocation.
  A seven-byte routing hook fits in the reference Model 4 BIOS by recovering
  seven bytes elsewhere in that same BIOS. The actual packed-image builder
  passes its region, overlap and reservation checks. BIOS size stays **757
  bytes**, the fixed resident span stays 6,588 bytes and record-aligned unloaded
  TPA stays **54,272 bytes** under the existing Model 4 exception.

The [machine-readable report](evidence/tcap-placement/report.json) records cases,
hashes, costs and limits. The [private core source patch](evidence/tcap-placement/packed-core.patch)
shows exactly which staged BIOS/platform instructions change. Production `src/`,
layout files, distribution images and utility implementations are unchanged.

## Carrier pressure and loaded cost

The private owner template is rewritten to access its small state region through
a saved/restored IX. Address helpers are specialized for the current owner, not
a general instruction optimizer; a hash gate rejects an unreviewed owner-template
change. They use scratch DE/BC and arithmetic flags only at sites where the owner
resets or does not consume them. Public experimental calls still preserve IX.

An iterative assembler-backed pass replaces 34 absolute jumps with relative
jumps only where the supported condition and signed displacement permit it.
Each pass is assembled and a separately assembled third origin verifies the
relocation list. No relocation entry is omitted merely to satisfy the header.

| Quantity | First campaign | Placed candidate |
| --- | --- | --- |
| Relocation words | 292, rejected | 228, accepted; four spare |
| Carrier format/header | BRSX v2 / 512 bytes | Unchanged |
| Raw personality payload | 2,028 bytes | 2,205 bytes, including resident bridge |
| Runtime service descriptors | Two proposed experimental advertisements | MCON 1.2 and private XTCP 0.2, validated by existing metadata code |
| Actual accepted allocation | None for rejected experiment | 2,304 bytes |
| Current ANSI baseline allocation | 1,536 bytes | Same baseline; candidate adds **768 loaded bytes** |
| Coordinator/guards | 93 bytes at a fixture-only address | 85 bytes inside the optional allocation |

The accepted allocation includes two runtime service descriptors and page
rounding. It does not add a separate owner RSX or enlarge the carrier format.
It is larger than the first campaign's *projected* 2,048 bytes; that rejected
image never had an actual installed allocation. Full public request handling
has not been added, and only four relocation entries remain available. Future
work must budget its reference pressure rather than assume unlimited growth.

## Fixed placement without lowering unloaded TPA

| Staged BIOS change | Bytes |
| --- | --- |
| Normalize status using ADD 255 / SBC A,A, retaining exact A=00h/FFh | −1 |
| Put LIST immediately after the console BAT route, removing a jump | −2 |
| Reuse post-LDIR register values for the Model 4 final-row blank fill | −4 |
| Save BC and invoke the private Monitor route probe before destination dispatch | +7 |
| Net fixed BIOS growth | **0** |

The status change preserves the public result, not unspecified arithmetic flags.
The scroll fill relies on the completed LDIR's DE at the final row, HL at
VIDEOEND and B=0; independent video modeling checks the result after each
character. The route hook preserves the caller's C even when an unknown-operation
callback clobbers scratch registers. It covers bypass/sink routes before normal
BIOS dispatch rather than relying on a personality seeing those routes later.

The staged system is rebuilt with matching internal BIOS links and a matching
Model 4 SCRN backend, since internal cursor/state addresses move. Public vectors,
the MONCALL/MONRAW/MONBASE entries and the published binding at EC84h remain in
place. Layout symbols, PDS, stacks and their boundaries are not shortened or
reassigned to conceal growth. The bridge is not left at 4000h or hidden in a
transient/workspace hole: execution uses its optional resident copy.

The route probe uses **private experimental MCON operation 25**. This is not a
public allocation. The actual current ADM3A, VT52 and ANSI frontends reject the
unknown probe without changing parser/backend state or emitting output; 36
checks cover six pending-parser values on both backends. Basic-console fallback
is compared across every IOBYTE. Before production activation, the private probe
needs a reviewed version/capability/coordinator admission contract. Arbitrary
third-party providers and other layouts are not certified by these checks.

## Executed checks

- All 168 owner/recovery behavioral case executions pass again: 42 cases on
  each backend at each of two origins, now using the resident bridge and the
  staged BIOS route hook. The fixture-only bridge address is cleared.
- Parser state, canonical rendition, cooked-column state and rendered/wire
  output match the original at **1,588 differential checkpoints**. The corpus
  includes partial/malformed sequences, large numeric parameters, margins,
  save/restore, visibility, colors, wrapping and deterministic random commands.
- The actual STATEFUL mover executes all 228 repair words in both directions.
  The fixture explicitly publishes the new binding and validity, wipes the old
  allocation, then successfully invokes emphasis/text/cleanup through the moved
  copy. This demonstrates movement and declared repair, not automatic real-manager
  owner publication or a boot-global identity allocator.
- **5,120** synthetic legacy routing/status cases cover every IOBYTE, including
  a probe handler that clobbers BC/DE/HL. All 256 returned status values are
  normalized independently. **512** basic-console output/LIST route comparisons
  match the baseline.
- An independent video model checks **4,448 characters**, including bottom-row
  scrolling, CR/LF, backspace and clear, against both original and staged BIOSes.
  Existing CAPS/noise and physical-fetch/selector compaction regressions pass.
- The production carrier/metadata/snapshot validators accept the generated
  carrier and materialize its two descriptors, including the deliberately
  rewritten loader-owned header. A corrupt checksum fails without publishing
  facts.

These counts describe executed cases/checkpoints, not independent requirements
or live/native qualification. The host screen is independently rendered by pyte;
Model 4 is CPU/video-memory evidence.

| Observed maximum | Client stack | Safe warm stack | BDOS private stack |
| --- | --- | --- | --- |
| Model 4 path | 14 bytes | 12 bytes | 26/40 bytes |
| ANSI-host path | 28 bytes | 20 bytes | 34/40 bytes |

Every SP assignment remains bounded by the fixture's explicit stack regions.
The host path has six bytes of observed private-stack margin. These are not
whole-system worst cases; filesystem-error and live/native paths still require
qualification before activation. No stack size was reduced or grown.

## Remaining work and scope

This closes the specific rejected-carrier and unplaced-bridge gates from PR #655
for the private Model 4 reference candidate. It does **not** close complete TCAP
production admission: the global non-reusing validity allocator, full candidate
request ABI, real finalizer/coordinator version admission and actual command-return
wiring remain incomplete. In particular, the fixed image's zero growth here does
not assert zero permanent cost for those missing components.

The host fixture retains the shared reference BIOS/router with a substituted
host-output leaf; it is not a full-RAM cpmsim build. Protected-ROM, native assembly
parity, live reloader/media behavior, maintained Model II and native display/timing
qualification are not claimed. The extra Monitor callback's hardware timing is
unmeasured. Third-party providers need the reviewed compatibility contract.

Generated source and binaries stay under `build/tcap-placement/`; the valid private
carrier must not be installed into production profiles. Continue system admission
and return-path integration before any TYPE/TED/HELP migration. HELP stays held.
There is no release assignment or public ABI freeze.

Reproduce with the [placement campaign](../../tools/prototypes/tcap/README.md#carrier-and-packed-placement-follow-up).
