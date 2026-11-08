# Compact public TCAP integration and qualification

This report qualifies the earlier portable-stack candidate. It does not meet
the subsequently clarified whole-display-path memory target. The
[integrated redesign](TCAP-Integrated-Display-Redesign.md) is the current work;
its TCAP 2.0 modules have separate CPU and full-machine qualification receipts.

Status: functional qualification passed, 8 November 2026. The compact public TCAP 1.0
service is integrated with the ordinary personality carriers and application
console path. cpmsim, Model 4 and Model II have passed source, installation and
installed-disk tests. Utility migrations, HELP delivery,
additional personalities and release assignment remain deferred.

The [public contract](TCAP-Template-ABI-Historical.md) replaces the unreleased transaction ABI.
This is an independent implementation following the measured Z-System allocation
model, not an implementation of the retired transaction contract and not a copy
of VLIB. Existing Monitor, MCON, SCRN, SCX and console routing retain their roles.
The ADM3A, ANSI and VT52 parser implementations and screen-backend design are
retained. The redesign replaces TCAP's discovery/data/lifetime machinery; it is
not a rewrite or size optimization of the complete existing console subsystem.
The 857-byte Z-System benchmark and this report's incremental TCAP figures
compare capability layers only. The underlying Z-System console implementation
was not included in that measurement. No whole-display-architecture size or
efficiency equivalence has been established; that requires a separate accounting
of both complete output paths and their supported behavior.
The later [Model 4 core display-path comparison](TCAP-Model4-Display-Cost-Comparison.md)
now includes the measured Montezuma native console: 1,314 bytes for the historical
path and 3,340 for BetterCP/M ADM3A, excluding general RSX machinery. It does not
establish equal coverage of every VLIB/SCX feature.

## Measured memory

The application helper contains **574 bytes of code and 203 bytes of working
data: 777 bytes**. Every figure below includes the added service advertisement,
allocation rounding and descriptor-page effects. The original personality and
rendering backend are reported separately as existing functionality.

| Personality | Description | Query | Original resident allocation | TCAP resident allocation | Added resident allocation | Added resident plus helper |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ADM3A | 33 | 10 | 768 | 1,024 | 256 | 1,033 |
| ANSI | 56 | 10 | 1,792 | 2,048 | 256 | 1,033 |
| VT52 | 29 | 10 | 1,024 | 1,024 | 0 | 777 |

All sizes are bytes. The maximum comparable static footprint is **1,033 bytes**.
Allowing another 32 bytes for call sites and 32 for helper stack gives 1,097.
The actual diagnostic application is 930 bytes including the helper, messages,
control flow and call sites; with the worst 256-byte resident increment and the
32-byte stack allowance it uses **1,218 bytes**, below the 1,280-byte ceiling.
CPU fixtures observed at most 16 bytes of helper/leaf-call stack, including the
entry return address. Existing BDOS/BIOS internal stack use is outside this
comparative layer, as are ordinary application text buffers and editor state.

There is no new permanent reservation, cache, recovery engine or counter.
Complete personality/backend unload must restore the exact original boundary
and maximum loadable COM size, not just a rounded RSX listing.

The earlier **799-byte** figure belongs to the private XTAB feasibility model;
it is not the size of this final public helper. Neither figure represents the
entire terminal emulator plus RSX support. For example, Model 4's existing RSX
resolver, M4SCRN backend and ANSI personality allocated 4,352 bytes without TCAP.
The public ANSI description raises that resident stack to 4,608 bytes, an extra
256. The 777-byte helper lives in the running application, not in that resident
stack. Do not describe 4,608 bytes as TCAP's incremental footprint, or claim the
whole loaded terminal-emulation stack fits inside 1,280 bytes.

Those components predate TCAP: the resolver was added on 12 September 2026
(`d294b579`), the monitor foundations on 15 October, and the unloadable backend
split on 16 October (`a4af2c65`, `d76151e1`, `05c0c643`, `32aa96eb`). The first
TCAP engineering proposal was added on 7 November (`fba0ad80`). Terminal emulation
interprets application protocol bytes and renders their effects; TCAP describes
which bytes a portable application should request. The compact facility does
not introduce a new emulator or make the existing emulator free.

| Model 4 resident component | Allocation with public TCAP |
| --- | ---: |
| Existing RSX resolver | 1,024 |
| Existing M4SCRN backend and descriptor | 1,536 |
| ANSI personality and descriptor, including 256 added for TCAP | 2,048 |
| Total resident console stack with ANSI | 4,608 |

These loaded allocations reduce the 54,272-byte unloaded COM capacity to 49,664
bytes with ANSI or 50,688 with ADM3A. They exclude the application's own helper,
code and data. Complete unload restores the original 54,272-byte capacity.

## Platform evidence

| Platform | Cold/warm source lifecycle | SYSGEN installation | Installed cold/warm lifecycle | Original/final boundary | Maximum COM before/after |
| --- | --- | --- | --- | --- | --- |
| cpmsim full RAM | PASS | PASS | PASS | E101h / E101h | 57,344 / 57,344 |
| Model 4 production layout | PASS | PASS | PASS | D501h / D501h | 54,272 / 54,272 |
| Model II full RAM | PASS | PASS | PASS | E101h / E101h | 57,344 / 57,344 |

The maintained [cpmsim receipt](evidence/tcap-public-integration/cpmsim.json)
contains each command, exact boundary, capability report, rendering check,
emulator hash and installation result. It verifies both invalid-package refusal
and declined installation leave the target untouched; successful installation
preserves files and matches the normalized build-bound protected payload.
The [Model 4 receipt](evidence/tcap-public-integration/model4.json) records the
native source and installed lifecycles and the intervening installation.
Its retained source campaign used the earlier valid 733-byte helper; the final
installed-disk campaign used the 777-byte helper with added strong-pair checks.
The core, public personality descriptions and query code are unchanged between
those campaigns. All reported final budgets use the 777-byte helper.
The [Model II receipt](evidence/tcap-public-integration/model2.json) records the
independent source, installation and installed-disk campaigns, all with the
777-byte helper. All three platforms report zero permanent TCAP memory loss.

Each lifecycle executes 42 commands: absent discovery and refusal; backend load;
ADM3A, ANSI, VT52 and ANSI again, each loaded, discovered, exercised through
ordinary BDOS output, returned through JP 0, rediscovered and unloaded; then
complete backend unload, exact boundary restoration and a maximum-size COM.
ADM3A/ANSI render reverse emphasis; VT52 renders plain text. Fixed profiles report
80 by 24. ANSI reports unknown stream dimensions on cpmsim and the backend's
80-by-24 stream on Model 4/II. Unknown dimensions are not replaced with defaults.

Native tests use explicit Model 4 or 64K Model II selection and disposable media.
They capture 47 raw screen checkpoints per lifecycle, including the exact
position and reverse/plain bits of `TCAP TEXT`. Model 4 installation explicitly
configures B: to the matching extended system-disk format before invoking the
ordinary SYSGEN installer. Model II uses its supported ImageDisk system format.

## Admission and compatibility evidence

- [72 CPU fixtures](evidence/tcap-public-integration/cpu.json) cover bounded
  descriptions, coordinate formatting and limits, strong-pair coherence,
  geometry, route eligibility, unavailable services, selected-owner matching,
  refusal without output, preserved registers and balanced stack.
- [31 real checked-guest commands](evidence/tcap-public-integration/admission.json)
  check damaged payload rejection, foreign private binding rejection, malformed
  tables, incompatible TCAP majors, orphan/foreign-owner descriptions, duplicate
  personality rejection and backend dependency refusal. HALT query fixtures
  prove incompatible and orphan descriptions are rejected without calling them.
  Complete unload again restores E101h and a 57,344-byte COM.
- [13 native assembler comparisons](evidence/tcap-public-integration/native-assembler.json)
  produce identical bytes with native ZSM4/LINK and the cross assembler for the
  three personalities, screen backends and resolver modules.
- The existing MCON/SCRN version, class and platform compatibility regression
  passes all 68 cases. This compact work adds a second ordinary advertisement;
  it does not introduce a new carrier or alternate loader.

## Scope and remaining work

The helper is an application-linked library and the example is a qualification
consumer. TYPE, TED and HELP are not migrated. Applications own paging, parsing,
editing, balanced emphasis and cleanup. Saved screens, arbitrary prior rendition,
nested ownership and abandoned-session restoration are not promised by TCAP.

The platform runs qualify emulated supported machines and installation media;
they do not constitute tests on physical hardware or arbitrary host terminals.
Future terminal descriptions remain a separate follow-up after this facility's
qualification, as recorded in the [personality backlog](TCAP-Future-Personalities.md).
