# Bounded monitor memory and efficiency review

Measured 2026-10-12. BIOS/BDOS implementation audit with isolated assembly and
behavioral probes. No production BIOS, BDOS, disk source or memory layout changed.

## Finding

**Accepted 1.0 disposition:** use a loadable monitor RSX with compact BIOS hooks,
loaded through the existing cold-start SUBMIT mechanism. The general target is
VT52; the Model 4 target is MM-style ADM-3A. Loaded RSX memory cost is accepted,
while the unloaded core retains 53K TPA. See the
[terminal-monitor decision](../architecture/31%20Terminal%20Monitor%20RSX.md).
The implementation and qualification are pending; the measurements below remain
evidence for budgeting, not installed monitor behavior.

There are **119 bytes of measured implementation savings** in the current
BDOS and Model 4 disk support, with the existing emulated behavioral campaigns
passing. These are credible qualification candidates, not installed changes.

A straightforward integration of the reconstructed MM output engine adds
**290 bytes**. After the 119-byte saving and three existing spare bytes, that
particular implementation still needs **168 bytes**. This is not a lower bound:
a fresh compact monitor may be smaller. It is also not a qualified MM port.
Do not remove features or reduce TPA on the strength of an unoptimized reference.

The smaller cursor-addressing pilot adds 104 bytes and is affordable against the
new candidate budget. It is not a complete terminal and must not be presented as
meeting the full MM compatibility goal.

## Ground rules and scope

Maintain at least 53K core-system TPA. Loaded RSXs may reduce TPA under the
existing extension policy; the user explicitly reaffirmed this during the
monitor-hook discussion. An RSX monitor is therefore not disqualified because
the loaded system reports less than 53K. Report unloaded and loaded footprints
separately rather than quietly counting its allocation as free. Seek smaller
implementations and shared code in BIOS
first, then BDOS when necessary. Propose feature removal/deferral or optional RSX
placement only after implementation savings have been evaluated; no existing
contract is removed by this audit. Recovering 54K is desirable.

Include execution cost, persistent state and qualification cost alongside size.
A smaller routine is not automatically faster. Only non-overlapping lifetimes
permit shared scratch memory; sequential command execution alone is not proof.

The Model 4 BIOS scope includes the separate **960-byte resident disk engine**,
not just the **636-byte BIOS wrapper**. Together they occupy 1,596 emitted bytes.
The configuration/format control overlay is already outside permanent storage.

MM-style ADM-3A is the Model 4 target; VT52 is the generic BetterCP/M monitor
target. The initial review costed only MM, an omission corrected by the profile
comparison below. Neither complete monitor is qualified yet. See the
[compatibility audit](Model%204%20ADM-3A%20Compatibility%20Audit.md) for the recovered
MM reference and its provenance.

## Baseline and whole-system budget

| Region | Emitted / allocation | Spare |
| --- | ---: | ---: |
| Gateway | 248 / 248 | 0 |
| BDOS | 3555 / 3555 | 0 |
| Extension services | 424 / 425 | 1 |
| Model 4 disk engine | 960 / 960 | 0 |
| BIOS wrapper/platform console | 636 / 638 | 2 |
| File loader | 145 / 145 | 0 |
| Disk tables | 576 / 576 | 0 |

Current TPA is 0100h through D500h: 54,273 bytes. Reaching 54 * 1024 bytes
requires another 1,023 bytes of usable contiguous TPA. No such recovery is
established. Reclaimable CCP/CPX code does not supply permanent monitor storage.

The budget assumes a future checked repack can make component savings usable
for BIOS. Savings inside BDOS are not automatically a larger BIOS region.
Every dependent platform image, private symbol import, ROM relocation inventory,
initialization template and loader must be rebuilt and qualified if addresses move.
Existing public entry-vector structure and calling interfaces can remain intact;
this does not mean private absolute addresses remain unchanged.

## Measured efficiency candidates

Cumulative variants assemble from the unchanged production source. Each row
includes helper setup, calls, returns and state; it is not a count of repeated
instructions removed in isolation.

| Component | Candidate | Incremental saving | Cumulative size |
| --- | --- | ---: | ---: |
| BDOS | One unsigned allocation-block bound comparison | 7 | 3548 |
| BDOS | Shared login/read-only vector mask preparation | 6 | 3542 |
| BDOS | Shared normal public-function return address | 45 | 3497 |
| BDOS | Shared REN/attribute completion path | 12 | 3485 |
| BDOS | Compact divide-by-eight loops at two ALV sites | 8 | 3477 |
| BDOS | Compact record-to-track division loop | 2 | 3475 |
| BDOS | Shared exact-name wildcard rejection | 15 | 3460 |
| BDOS | Shared name/attribute bit merge | 6 | 3454 |
| Disk engine | One loop for sector quotient and quarter mask | 9 | 951 |
| Disk engine | Shared physical-transfer length calculation | 9 | 942 |
| **Total** | **No feature removal** | **119** | **101 BDOS + 18 disk** |

Important invariants:

- The allocation-bound comparison preserves rejected-block carry and successful
  address/mask results. Scratch registers/flags on rejection are not promised.
- Only public-function normal returns use the shared return address. Nonlocal
  error exits, disk-full exits and invalid random-record exits retain their
  existing unwind path and caller-register restoration.
- The shared normal return and some helpers add temporary stack use. The observed
  maximum was 26 bytes in the filesystem campaign and 28 with injected errors,
  inside the retained 40-byte stack. This is campaign evidence, not a proof for
  every possible extension chain or hardware path.
- Exact-name rejection still masks attribute bits and rejects `?` in Make,
  Size, and both Rename names. Bad Rename input still exits before mutation.
- The merge helper takes low name bits from the Rename source while retaining
  destination attribute bits; Set Attributes does the opposite. Neither operation
  gains permission to change the other bit group.
- Geometry mapping still computes the same physical sector, side, cylinder,
  transfer size and logical-sector slot. All physical sizes 128–1024 remain.
- Buffer inversion, retry count, write protection and drive/head-position policy
  remain present. Transfer-length sharing does not combine or remove transfers.

The mask helper and compact fixed-count shifts trade some execution work for
bytes. The division-loop rewrite removes repeated carry clearing/branch work.
Geometry sharing reduces duplicated shift work. No whole-system speedup is claimed
without profiling. In particular, this audit does not establish the cause of the
previous long COPY run.

## Already shared and rejected shortcuts

READ/WRITE already share preparation; cold/warm/control reconstruction already
share physical fetch; bootstrap and runtime disk operations already use one disk
engine; sequential/random filesystem transfers share mapping, allocation, extent
and transfer paths. These remain useful foundations for the monitor review.

The first BIOS/BDOS branch scan found no safe local JP-to-JR savings outside fixed
vectors. The separate disk engine contains a few possible short branches; they
are not counted in the 119-byte candidate set. Public BIOS vector JPs stay three
bytes long. An alternative aligned sector-slot calculation assembled to the
same byte count and is not counted as a saving.

Zero-filled disk-binding tails are part of the 64-byte serialization contract,
not free memory. ALV/CSV capacity, keyboard pending state, private stacks and live
buffers are retained. No scratch overlay is claimed without lifetime evidence.
Off-screen video memory and writable ROM-profile code are not assumed available.

## Monitor prototypes and compatibility limits

| Isolated sample | BIOS bytes | Growth from 636 |
| --- | ---: | ---: |
| ESC `=` addressing pilot, including state/reset | 740 | 104 |
| Recovered MM engine integrated with existing keyboard/reloader | 926 | 290 |

The addressing pilot passed 2,465 coordinate/clamping sequences. It lacks the
other MM controls and cursor/reverse behavior. Both samples deliberately exceed
the current 638-byte BIOS region in isolated assembly; neither was published or
installed in a system image.

The fuller sample retains reference control dispatch, line operations, reverse
state, cursor visibility and bell, supplies the external fill helper, initializes
state and retains the private cursor entry. It removes MM bank switching because
BetterCP/M has its own memory ownership. It is a **size sample**, not a behavioral
qualification or specification of a new screen driver.

The recovered source itself requires verification: insert-line loads DE with
`-127` (FF81h), while the intended final screen cell is FF7Fh. Its reverse-video
0Fh routine toggles despite a comment saying on. Do not copy these details into
a promised compatibility contract without checking the chosen MM binary or the
intended safe semantics. The synced archive contains reconstructed source, not
proof of identical behavior in every MM release.

There is also a real existing-contract conflict: BetterCP/M uses 1Ch for
clear/home, while MM uses it for insert-line and 1Ah for clear/home. A memory
optimization cannot resolve that. A compatibility migration or profile decision
must be made explicitly before production integration.

## Generic VT52 and shared profile comparison

The current target decisions are **generic VT52** and **Model 4 MM/ADM-3A**.
These can be alternative build profiles using shared screen-operation source;
they do not by themselves require both parsers to be resident simultaneously,
runtime terminal configuration, new public vectors, or a TCAP service. The earlier
private-VIEW-only proposal has been overtaken by the decision to review the OS
monitor itself. This audit does not install a new public terminal contract.

DEC's [VT50/VT52 operator guide](https://vt100.net/dec/ek-vt5x-op-001.pdf)
describes the VT52 command family, including cursor motion, direct addressing,
erasure, reverse line feed, graphics, identification, alternate keypad and
hold-screen modes. The [DEC VT100 user guide's VT52-mode section](https://www.vintagecomputer.net/digital/VT100/vt100_manual/chapter3.html)
also documents motion stopping at screen margins. A compatible screen-control
subset is useful evidence, but is not complete terminal emulation. VT100's special
graphics differ from original VT52 graphics; those profiles must not be conflated.

Fresh isolated assemblies retain the current BIOS vectors, keyboard and reload
support. The video samples share the recovered coordinate calculation, cursor
presentation, fill and scrolling primitives. VT52 dispatch is deliberately simple,
with conditional branches rather than an optimized compact command table.

| Profile sample | BIOS bytes | Comparison |
| --- | ---: | --- |
| Current Model 4 | 636 | Production baseline |
| MM reference integration | 926 | +290 from Model 4 baseline |
| VT52 screen-control subset on Model 4 video backend | 959 | +323 from Model 4 baseline |
| Both parsers with one video backend and mode byte | 1111 | +475 from baseline; +185 over MM sample |
| Current cpmsim host/ANSI binding | 372 | Within existing 638-byte allocation |
| cpmsim passthrough with VT52 clear/home sequence | 369 | -3 from current cpmsim binding |

The Model 4 video backend is a costing fixture for a software-rendered generic
monitor, not a decision to replace Model 4's ADM-3A profile with VT52. The
combined sample has one renderer and one cursor/parser state area; it does not
contain two complete copies. Its mode byte and dispatch instructions are counted.
Its sample flag is not a production configuration interface. Mode changes would
need explicit escape-state reset and a defined initialization/lifetime policy.

The VT52 screen sample includes ESC A/B/C/D/H/I/J/K/Y, ordinary BEL/BS/TAB/LF/CR,
margin-clamped movement and text advance, and BetterCP/M's existing 1Ch clear/home
alias. Coordinates reuse the MM sample's unsigned-subtraction/clamping policy;
this is a prototype policy, not a settled claim about malformed DEC sequences.
Reverse scrolling uses a safe VIDEOEND-1 destination instead of the reconstructed
MM insert-line anomaly. The sample does **not** implement graphics glyphs,
identification replies, alternate-keypad input or hold-screen/flow-control modes.
These omissions are not proposed feature removals or an approved compatibility
boundary. No complete VT52 size or minimum implementation cost is established.

The simple combined sample demonstrates feasibility of code sharing, not its
best achievable size. Against the provisional 122-byte recovery budget, the
MM sample is 168 bytes short, the VT52 screen sample 201 bytes short, and the
combined sample 353 bytes short. This comparison applies to the Model 4 packed
layout; it must not be applied to cpmsim's much smaller host binding.

For cpmsim, PL_CONOT presently forwards host output bytes and expands BetterCP/M
1Ch into ANSI clear/home. The 369-byte sample changes that expansion to ESC H,
ESC J and otherwise passes bytes through. **It needs a VT52-capable host terminal**
and correctly configured geometry/input. It is not a VT52-to-ANSI translator and
does not make an ordinary ANSI-only terminal accept VT52. The 269 unused bytes
in that sample's BIOS allocation are platform-specific, not transferable spare
space in the Model 4 allocation. A translator, host-side terminal implementation,
or selected VT52 host environment must be evaluated before cpmsim can advertise
the generic monitor contract. Terminal-input and graphics requirements remain
part of that evaluation.

Parser probes passed all 65,536 row/column byte pairs for each video sample,
plus control/escape routing and unknown-command consumption. Screen primitives
were substituted with routing markers: these probes do not prove rendered screen,
scrolling, glyph, bell timing or keyboard-mode behavior. Host probes verified
emitted bytes and clear/home expansion; they did not test a host display.

Reproduce these size/routing samples with the read-only reference archive:

```sh
python3 tools/audit_monitor_profiles.py --mm-reference /path/to/mmcpm232.zip
python3 tools/test_monitor_profiles.py
```

All sources, listings, binaries and measurements remain under
`build/audit/monitor-efficiency/`. Production images and layout are unchanged.

## BIOS hooks with a protected monitor RSX

This is a viable bounded alternative to compiling the complete monitor into
permanent BIOS. It uses the established policy that installed RSXs consume TPA.
The core retains a basic console usable during boot, recovery and provider
absence; a loaded platform-specific monitor supplies richer terminal behavior.
Generic VT52 and Model 4 MM/ADM-3A remain alternative provider profiles.

The hook belongs behind the fixed BIOS entry vectors. BDOS already calls those
vectors, so both BDOS-mediated and direct BIOS callers can reach the provider.
Output interception alone is insufficient for identification replies, keypad
translation and other input-related behavior: status and input need corresponding
hooks. The private cursor-character service also needs an explicit ownership
decision so that its writes do not bypass the active monitor's cursor state.

Isolated assemblies of fixed trampolines, mutable target words and inline
cold-boot fallback initialization give these **hook-only** measurements:

| Hook set | BIOS bytes | Growth from 636 |
| --- | ---: | ---: |
| Output | 648 | 12 |
| Output, status, input | 672 | 36 |
| Those three plus private cursor service | 684 | 48 |

Each hook costs four dispatch bytes, two pointer bytes and six cold-init bytes.
The 17-entry public vector layout is unchanged. These samples preserve the basic
console and do not grow BDOS. They exceed the current two-byte BIOS reserve;
the previously measured recovery candidates would cover their size after a
qualified repack. They do not include loader integration, registration validation,
failure rollback, additional backend exports or monitor payload. Reproduce with
`python3 tools/audit_monitor_hooks.py`; outputs remain isolated under the audit
directory. These are size probes, not a qualified install/unload implementation.

The difficult part is provider lifetime, not the indirect jump. Current STATEFUL
movement repairs pointer slots **inside the RSX allocation**. It cannot repair a
BIOS-owned pointer to the provider. STATEFUL reconstruction intentionally does not
rerun ordinary initialization, so an initialization-only binding would become stale.
The existing service registry derives addresses from active provider bases and
offsets; it supplies an identity model worth reusing, but it is not already a BIOS
console-hook facility. BIOS must not recursively call BDOS just to find its monitor.

A correct contract must cover:

- complete provider publication after successful load, with the fallback active
  until then;
- retained parser/cursor state and safe rebinding after movement;
- restoration of fallback targets before unload or retirement;
- fallback or suspended binding during reconstruction, followed by publication
  consistent with the committed chain; failed preparation leaves the old binding
  usable;
- warm-boot persistence and cold-boot default reset; and
- calls made through the private cursor entry, direct BIOS and BDOS device routing.

Immutable BIOS vectors can jump to fixed trampolines; mutable targets belong in
protected RAM with ownership and initialization entries. This avoids instruction
patching, but needs layout/inventory and ROM-profile qualification. A COLD_ONLY
provider can simplify movement by rejecting transactions that would move it; that
also restricts otherwise valid RSX changes and still does not solve unload cleanup.
It must be an explicit stopgap choice, not an assumed free implementation.

Loaded memory includes the page-rounded module allocation (256-byte granularity),
its runtime header/descriptors/state and, for the first active RSX profile, the
current common 1,024-byte manager/resolver reservation. For example, a provider
allocated 512 bytes would charge 1,536 bytes when it is the first RSX, versus
512 incremental bytes when the common reservation is already charged. This is an
allocation example, not a measured monitor carrier size. Any permanent hook and
backend growth is additional. Reusing BIOS screen primitives may reduce the RSX
payload; retaining a complete renderer in both locations would duplicate cost.

Accepted direction: cost a **single active monitor provider with a bounded console
hook contract**, preserving normal RSX movement through safe publication/rebinding.
Keep general terminal-capability discovery and a broad hook/plugin framework
outside this proposal. The user selected the RSX approach for 1.0; loaded TPA
reduction is an accepted tradeoff, not a rejection criterion.

## Verification and reproducibility

Run after the baseline resident components have been built:

```sh
python3 tools/audit_monitor_memory.py
python3 tools/test_monitor_memory_audit.py
```

Outputs stay under `build/audit/monitor-efficiency/`. Baseline assemblies must
match current production binaries before candidates are measured. The test harness
redirects both image and symbol inputs; the recovery campaign's re-executed source
is also redirected, so it cannot silently retest the baseline.

The combined candidates passed:

- 17 BIOS-vector contracts, keyboard/transport, scrolling, all 80 default-drive
  logical reads/writes, sector translation and error cases;
- the unified filesystem foundation, including public return aliases, stack/IX
  restoration, file operations, allocation, extents, sequential/random I/O,
  protection and shared allocation rebuilding;
- 480 grouped-extent activation cases;
- 24 read/write success/ignore/abort combinations and the complete foundation
  with injected final I/O errors;
- 112 retry/polarity/size/write-protection cases;
- 8,400 differential baseline/candidate geometry cases across all four physical
  sizes, cylinder/alternating-track conventions, drive/track/sector limits and an
  unavailable drive;
- four real transfer-setup calculations, checking the derived block count before
  data transfer rather than relying only on the substituted retry outcomes.

The earlier bounds probe compared every 16-bit block against eight DSM boundaries
(524,288 cases); the vector probe compared 4,096 set/test combinations. These
supplement the public campaigns. The small test CPU gained XOR-(HL) execution
support needed by the merge candidate; no production instruction stream changed.

Still required for adoption: native-assembler parity, packed layouts on both
platforms, ROM ownership/relocation checks, cold/warm reconstruction, broader
stack paths and real emulator/controller regression. WD byte-transfer timing is
not proven by the small runner or the injected-outcome retry test.

## Architectural choices and recommendation

Implement the accepted bounded monitor-RSX design: compact permanent BIOS hooks,
one active provider, shared backend primitives where practical, basic-console
fallback and safe binding throughout the RSX lifecycle. Use the existing saved
cold-start command and a SUBMIT script for loading; warm boot must retain the
provider without rerunning startup. No general TCAP format or discovery API is
implied by this de facto loadable terminal-personality layer.

The available no-TPA-growth target from the measured saving candidates is
**122 additional BIOS bytes**, subject to repack and qualification. Permanent
hooks/backend changes must fit the qualified core budget; the RSX payload is
charged separately to loaded TPA. The 926-byte built-in reference integration
does not fit that permanent budget and is not a minimum-size result. Qualification
of the savings is still required before adopting any of them.

Do not remove CP/M core features to force this unoptimized sample to fit. For
example, the 258-byte buffered-line-input/echo region is a possible relocation
subject, but it implements the standard Function-10 contract and depends on core
console services and error unwinding. Making it optional would break compatibility;
making it a required RSX consumes protected memory and introduces loading/lifetime
requirements. It is not a free 258-byte saving.

Likewise, a terminal RSX intercepting BDOS output alone does not cover direct BIOS
CONOUT callers. Fixed BIOS trampolines with protected mutable targets can provide
that coverage without patching immutable vectors, subject to the lifecycle
contract above. Loaded protected-memory cost must be reported separately from
the 53K core baseline; that reduction follows the accepted RSX policy.

No lower-priority feature removal has yet been demonstrated to supply the remaining
space while preserving the agreed contracts. The bounded review has established
useful savings and a concrete monitor budget, but **has not established that the
complete built-in monitor fits at 53K**. The selected loaded monitor RSX may reduce
TPA as other RSXs do; unloading the last RSX must restore the core baseline.
Feature cuts, reductions to the unloaded core baseline, a
new general RSX architecture and a 54K claim remain unapproved.


## Follow-through: single-entry monitor binding

The [hook and lifecycle contract](Monitor%20RSX%20Hook%20and%20Lifecycle%20Contract.md)
selects a single multiplexed entry and prepared rebind. Isolated assembly adds
64 BIOS bytes; scheduler detach fits its 496-byte region and publisher rebind
fits existing padding. Dispatch tests pass with a fake provider. Metadata
selection, real transaction integration, warm-return reset and packed/ROM
qualification remain pending; these results do not install a monitor.
