# BetterCP/M 1.2 Programmer's Guide

Original prose/illustrations are CC BY 4.0; original reusable examples are GPL-2.0-or-later. Third-party works retain their terms. See [licensing and example boundaries](../LICENSING.md).

This guide is for programmers writing CP/M applications, BetterCP/M command extensions and resident services. It assumes familiarity with Z80 assembly, registers, memory and ordinary CP/M operation. For command syntax use the [Command and Utilities Reference](Command-and-Utilities-Reference.md); for hardware adaptation use the [Practical Porting Guide](Practical-Porting-Guide.md).

This edition describes BetterCP/M 1.2 for patched cpmsim, TRS-80 Model 4 and the 64 KiB Model II under trs80gp 2.5.8. Use matching System and Utilities downloads from the same release. Package identity and exact source/image hashes come from RELEASE.json and the release index. The prior 1.0 and 1.0.1 downloads and locks remain unchanged. See the [1.2 scope](../releases/1.2-SCOPE-AND-ACCEPTANCE.md) and [platform boundaries](../platform/SUPPORT-1.2.md); engineering receipts are not acceptance of differently hashed final media.

## 1.2 operating profile

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

BetterCP/M 1.2 supplies integrated ADM3A, VT52 and ANSI personality/renderers implementing the independently versioned TCAP 2.0 direct API. Load one with `RSX LOAD ANSI`, unload it with `RSX UNLOAD ANSI`, and rediscover services after every layout mutation. No standalone screen backend is required by these integrated modules. Model 4 startup selects ADM3A; cpmsim and Model II start with the basic console. Separate ANSISCRN, M4SCRN and M2SCRN modules remain available to clients of SCRN/SCX, such as TED and DUMP paging. HELP and its topic library are shipped and use the TCAP 2.0 direct API. TYPE and TED retain their existing display interfaces; see the [full impact audit](../engineering/TCAP-Utility-Impact-Audit.md). The abandoned, unreleased TCAP 1.0/template designs are historical, not compatibility modes. The supported protocols are fixed 80x24 seven-bit paths, not arbitrary host geometry. See the [direct ABI and caller helper contract](../engineering/TCAP-Direct-ABI.md).

Unqualified commands search the invocation drive/user first. Numeric PATH adds up to six ordered drive/user entries, default `$$: A0:`. `$$` tracks the caller; `$0` uses user 0 on the current drive and `A$` uses the current user on A. `.` is not a PATH entry. Use `PATH /H`, `/HELP` or `/VER`; `A0:PATH /DEFAULT` recovers the default. PATH is volatile: use the existing startup script to apply a preferred list after cold boot. NDR supplies named directories and PATH annotates matching numeric entries. Extended scripting remains outside 1.2.

## Contents

1. [Choose an interface and build a program](#choose-an-interface-and-build-a-program)
2. [Manage execution and memory](#manage-execution-and-memory)
3. [Use console services deliberately](#use-console-services-deliberately)
4. [Create, read and close files](#create-read-and-close-files)
5. [Use random records and handle failure](#use-random-records-and-handle-failure)
6. [Find the complete API reference](#find-the-complete-api-reference)
7. [Develop a CPX](#develop-a-cpx)
8. [Develop an RSX](#develop-an-rsx)
9. [Discover and call a service](#discover-and-call-a-service)
10. [Terminal and clock providers](#terminal-and-clock-providers)
11. [Reuse input and archive libraries](#reuse-input-and-archive-libraries)
12. [Diagnose and qualify your program](#diagnose-and-qualify-your-program)

## Choose an interface and build a program

Start with the narrowest interface that meets the program's purpose:

| Requirement | Interface | Consequence |
| --- | --- | --- |
| Ordinary file/character application | Standard CP/M 2.2 BDOS | Portable across compatible systems; keep terminal/hardware assumptions separate. |
| Inspect the machine's disk/character capabilities | Version-gated BetterCP/M interfaces | Requires explicit discovery and unavailable behavior. |
| Add a command used at the prompt | CPX | Command code is reclaimable while transients run. |
| Supply a service during application execution | RSX, usually callable metadata | Protected allocation reduces TPA; relocation/lifetime rules apply. |
| Add a terminal protocol | MCON personality | Parse into typed backend operations; no hardware assumption in a portable personality. |
| Add a controller/display/boot target | Platform/BIOS support | Follow the porting guide and qualify a separate target. |

The native toolchain supplies ZSM4 4.7 and Digital Research LINK 1.3. Keep sources and outputs on writable work media. With primary Utilities in B, change to your chosen work DU before building the [HELLO.MAC example](../programmers/examples/HELLO.MAC):

```text
D0:
B0:ZSM4 HELLO=HELLO
B0:LINK HELLO[A]
HELLO
```

Require `Errors: 0`, no undefined symbols and a successful linker report. A COM file can exist after a failed link; its presence is not success. Includes follow ZSM4's output-drive rules. These examples use CSEG with `.PHASE 0100H` for CP/M execution addresses, following the in-tree native style. Do not replace that with an unexamined ORG that creates a leading 256-byte gap. See [ZSM4](Command-and-Utilities-Reference.md#zsm4), [LINK](Command-and-Utilities-Reference.md#link) and [native build material](../programmers/BUILD-DISK.md).

Cross-development can assemble the same source after the established ASEG/ORG conversion and should reproduce the declared executable interval. Native/cross equality does not prove execution. CP/M rounds output to 128-byte records; record padding is distinct from a source program's logical end and may be interpreted differently by tools. Keep every required byte, buffer and stack below the active ceiling, including uninitialized reservations represented in the load/run model.

## Manage execution and memory

A normal COM image begins at 0100h. The word at 0006h is the exclusive upper boundary of transient memory, not necessarily the core BDOS address. Page-zero 0005h routes through the current RSX chain. The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

The CCP and CPX code below the protected gateway may be overwritten by a transient. Fixed core/BIOS state, installed RSXs and the bounded history object are protected. On ordinary warm return the command environment is reconstructed from its carriers; RSXs/history retain their supported live state. Cold entry starts a new lifetime. An application cannot borrow a CCP string buffer merely because it happens to be readable before loading a larger image.

Allocate an owned stack and keep a measured margin. If you change SP, either restore the original return frame before RET or intentionally take a documented warm-return path. HELLO uses JP 0000h after an owned stack. Save the counted command tail at 0080h before directory or record operations reuse the default DMA area. Copy both parsed filenames to independent full FCBs before opening two files: the standard page-zero FCBs overlap.

A routine called by another program needs a stronger cleanup policy than a top-level warm-returning demonstration. Record which drive, user, DMA and IOBYTE state it may change; restore them on every normal-return path. Standard CP/M has setters for some state without universal getters for everything, so a reusable routine can require its caller to pass the expected DMA address instead of pretending it can discover it.

## Use console services deliberately

Function 9 is convenient for `$`-terminated messages. It is unsuitable for binary buffers, counted command tails or terminal sequences containing 24h. Function 2 performs cooked output with column/TAB/printer/flow behavior. Function 6 supplies direct byte output and input polling, while Function 11 checks readiness without consuming a byte. Distinguish “not ready” from a real NUL where required; direct input's A=0 alone cannot represent that distinction.

Function 10 offers the conventional counted line buffer. It is not the CCP's history editor and must not silently acquire its key assignments. XSUB can feed this buffered input when its matching BATCHIO companion has been copied from Utilities to A0, but does not supply arbitrary raw hardware/Function-6 input. [The 1.0 XSUB erratum](../releases/1.0-ERRATA.md#xsub-companion-must-be-copied-to-a0) is part of the actual environment, not a change to fix in examples.

For a full-screen application, declare the expected terminal personality and screen prerequisites. TED, for example, requires its documented ANSI/backend setup; this does not imply every console program needs a backend. ANSISCRN requires an ANSI host at least 80×24 with normal scrolling. Use readiness checks that do not consume replies. Direct video writes and manufacturer-private keyboard codes reduce portability even when file access uses standard BDOS.

## Create, read and close files

The [RECORDS.MAC example](../programmers/examples/RECORDS.MAC) creates one exact fresh `DEMO.DAT` in the caller's current DU, writes a known record, closes it, reopens and verifies the bytes. Run it on disposable work media with that name unused. It deliberately refuses a successfully opened pre-existing file; it does not erase or replace one.

The sequence is:

1. Construct a zeroed 36-byte exact FCB with padded name/type.
2. Check the name; choose a different one if it exists. Handle a failed Make rather than assuming absence guarantees creation.
3. Set a private 128-byte DMA buffer with Function 26.
4. Make with Function 22, accepting all directory success values 0–3.
5. Write with Function 21 and check zero. On failure, attempt Close if control returns and preserve the partial file for inspection.
6. Close with Function 16 and require a non-FFh result before reporting write completion.
7. Reinitialize extent/CR state, Open, then read through the same private DMA buffer and verify only after a successful transfer.
8. Close, restore default DMA and warm return. The demonstration does not delete its output, including a partial/error output.

There are three separate success conditions: accepted transfer, successful metadata close, and any application-level verification. A completed console message must come after those checks. Directory-full can occur with data blocks free. Never erase the original first to make a replacement easy; create/stage a new name, validate it, close it and then follow an explicit backup/publication policy. Renaming several files is not a power-loss-atomic transaction.

For an actual copier, give source and destination their own FCB and preserve a dedicated transfer buffer. Close output on every returning failure path. Keep source/destination identity separate from spelling, including DU and any physical alias policy. The higher-level COPY utility performs selector/preflight work which ordinary BDOS Open/Make does not provide automatically.

## Use random records and handle failure

Random positions are little-endian R0/R1/R2 record numbers, not byte addresses. To address byte offset `p`, use record `p / 128` and an in-record offset `p % 128`; a partial-byte update requires reading/modifying the complete record and an explicit EOF policy. Functions 33/34 read/write one selected record. Function 36 converts sequential position; Function 35 returns the exclusive record end, not original host byte length.

Random I/O updates the FCB's sequential position to the selected record without incrementing the random number. If looping through random records, increment R0/R1/R2 explicitly and check overflow. Sequential I/O has its own advance/extent behavior. Preserve the populated FCB; a close/open shortcut can lose live extent/map state in cases specifically covered by Function-40 compatibility work.

Function 40 initializes a newly allocated block to zero before the requested write. It does not promise a zero-filled byte stream for every logical hole between old EOF and an arbitrary seek. Treat all nonzero transfer results as failure; the locked implementation can collapse historical detailed seek codes into FFh. A read-only violation can take a nonreturning warm-boot path, so normal-return cleanup is not a universal guarantee.

### A cleanup checklist for a returning routine

| State/resource | Success | Returning failure | Nonlocal warm boot |
| --- | --- | --- | --- |
| Output FCB | Close and check | Attempt safe Close; retain original error and close error separately | Cannot assume local cleanup runs |
| DMA | Restore caller's agreed address | Restore it | System warm path supplies its own defaults |
| Drive/user/IOBYTE | Restore if promised | Restore if promised | Document exceptions instead of claiming restoration |
| Staged output | Publish only after validation | Retain/remove only under stated policy | Caller needs recoverable names and instructions |
| Borrowed pointers | Discard before lifetime ends | Discard | Never reuse after reconstructed environment |

## Find the complete API reference

The API part is split into two linked reference chapters so the common calling/structure rules have one owner:

| Reference | Coverage |
| --- | --- |
| [CP/M 2.2 API](../programmers/CPM22-API.md) | Page zero, FCB/DMA, BDOS 0–40 including 37/40 and reserved 38/39, all 17 BIOS vectors, IOBYTE, DPH/DPB, errors and BetterCP/M differences. |
| [BetterCP/M API](../programmers/BETTERCPM-API.md) | Selectors 176–183, reserved/test boundaries, version/profile/disk/service request structures, TIME/P2DOS, carrier and monitor lifecycles, private BIOS/PDS boundaries. |
| [Reference status](../programmers/REFERENCE-STATUS.md) | Stability, retained-document conflicts, evidence limits and expansion backlog. |

A register-level summary is not permission to bypass ownership. The per-interface source and focused contracts supply integration details such as controller write-track streams, SCX rendition records and archive callbacks. Links to those contracts are explicit reference continuations, not a claim that every chronological paragraph is current.

## Develop a CPX

Use a CPX for a command that runs in the prompt environment. [PING.MAC](../programmers/examples/PING.MAC) is a small worked handler with an eight-byte live header. It recognizes exactly PING, prints one reply and returns carry set; it returns carry clear for every other command. It preserves the input buffer and SP/IX/IY. Its scratch registers may change. Matching the length prevents PINGMORE from becoming PING accidentally.

The source is linked at 8000h solely to generate relocation data, not to choose its runtime address. Build a second image at 8101h, derive/validate every changed absolute word and use `tools/build_cpx_module.py`'s `relocation_offsets` and `make_module` with name PING, version (0,1), commands [PING], entry_offset=8 and absent lifecycle offsets FFFFh. The builder requires matching tooling modules from the Source snapshot. Do not package an unconverted raw binary by renaming it .CPX.

The existing `tools/build_hello_cpx.py` demonstrates the complete source conversion, two-origin comparison and carrier creation. `tools/build_native_hello_cpx.py` supplies the corresponding native path. For PING, substitute source/module/output identities in a private builder rather than editing a release artifact or running a builder into the frozen output tree. A builder's checked-profile option is not the production BCPX v1 path.

On disposable work/System media, copy the carrier to A0, confirm profile capacity with `CPX LIST`, load it, run PING and an unrelated command, run a transient and invoke PING again. Remove it and verify the command disappears. Test invalid/missing carrier and initialization failure separately. Ordinary CPX code does not remain protected during a transient; never store indispensable state only in the live PING image.

For lifecycle-enabled modules, initialize in configured order with HL=base and A=0 success, preserving SP/IX/IY. Shutdown is called in reverse before transient reclamation and cannot veto it. Do not confuse removal of a configured package with shutdown of each reclaimable instance. See the [carrier/lifecycle reference](../programmers/BETTERCPM-API.md#carrier-formats-and-lifetime).

## Develop an RSX

Use an RSX when service code must survive application execution. Begin with an ordinary chain entry that handles only its owned requests and passes unowned calls through the loader's next pointer. A callable service usually avoids allocating another top-level numeric selector. Experimental/private service IDs start with X; do not adopt the TEST/STAT fixture identities as public allocations.

The in-tree `src/rsx/testsvc.mac` plus its builder demonstrates a callable provider; `src/rsx/stateful.mac` demonstrates a counter, buffer and runtime-created pointer surviving movement. `HELLO.RSX` intercepts non-public Function 198 as a chain proof and is **not** a production application API or supplied everyday module. Its fixed link origin, proof selector and deliberately large allocation are test inputs rather than design defaults for your service.

A production BRSX v2 carrier includes numeric/callable advertisements, static relocations and any mutable runtime self-pointer slots. Declare the reconstruction class. For STATEFUL, all surviving module state must be inside its allocation or behind an explicit external lifetime contract. Do not retain pointers to CCP data, transients, another movable provider or preparation scratch. Prefer self-relative offsets for internal data. Any mutable absolute self-pointer must be declared; static link relocation does not discover it later.

During a STATEFUL move, the manager copies the complete allocation and adjusts declared values pointing into the old image. Null/sentinel/fixed addresses remain unchanged. Loader-owned chain and descriptor fields are rewritten separately. The [stateful example](../../src/rsx/stateful.mac) deliberately contains all these cases; a counter-only preservation test is insufficient.

Prepare all fallible disk reads, validation, snapshots and placement before commit. A monitor's payload must start with valid empty parser/queue state; do not depend on a fallible callback after the live image begins moving. STATE_PRESERVING export/import is reserved; COLD_ONLY movement must be rejected. Explicit unload discards private state under its contract. No 1.0 general dependency graph or persistent allocator is implied.

To qualify a new provider, test load, call, unknown-call chaining, duplicate rejection, forced movement both directions, state/pointer preservation, lookup rediscovery, WBOOT, unload and a preparation failure preserving the old profile. Keep test carriers outside locked distribution membership. The [prepared transaction record](../engineering/151%20Stage%203%20Prepared%20Profile%20Commit.md) documents the final path; earlier staged callbacks/rebuilders are historical.

## Named-directory service (1.2 development)

NDR.RSX owns the 32-entry live map in a 512-byte STATEFUL allocation; it does
not use PDS storage. Discover service `NDR `, ABI 1.0, through Function 182 and
use the returned entry immediately. Rediscover after every manager mutation;
reverse-lookup pointers are borrowed. Operations provide forward/reverse
lookup, a 320-byte snapshot and complete-table replacement. Replacement is a
trusted management interface: the caller must validate names, duplicates,
padding and DU ranges before publishing. It is not a security boundary.
See the [exact register contract and saved-set format](../engineering/NDR-1.2.md).
Transient tools can use [the existing discovery helper](../../src/utilities/common/ndr-client.inc).

## Discover and call a service

The [TIMEQ.MAC example](../programmers/examples/TIMEQ.MAC) makes a 20-byte Function-182 LOOKUP for TIME ABI 1.0, then invokes its entry with a ten-byte native request. It distinguishes absent/incompatible service from failed GET and prints the five returned bytes as hexadecimal. The hour/minute/second bytes are packed BCD, so valid BCD bytes have a familiar decimal appearance without performing calendar conversion. The day count remains hexadecimal low/high bytes, not a Gregorian date string.

The indirect call helper uses `JP (HL)` after an ordinary CALL, so the service RET returns to the application's caller. Test A explicitly; do not assume carry. A successful LOOKUP does not prove SET capability; require bit 0001h if you intend SET. The returned pointer is used immediately and not saved for another process or resident-layout generation.

Before running TIMEQ on cpmsim, load `RSX LOAD ZPRTC`; on a suitable Model 4/FreHD setup use FREHDCLK. P2DOS is unnecessary for native TIME. With no provider loaded, TIMEQ should take its unavailable path without dereferencing zero or inventing a plausible date. The supplied providers reject SET; no example writes a hardware clock.

A resident frontend needs a lower-service call path which avoids reintercepting its own request. P2DOS resolves TIME on every call, translates its result and discards the address. It can remain installed without a provider and return FEh. Service absence, frontend absence, ABI mismatch and unsupported capability are different states; do not collapse them into “hardware missing” in diagnostics.

## Terminal and clock providers

BetterCP/M 1.2 supplies integrated ADM3A, VT52 and ANSI personality/renderers implementing the independently versioned TCAP 2.0 direct API. Load one with `RSX LOAD ANSI`, unload it with `RSX UNLOAD ANSI`, and rediscover services after every layout mutation. No standalone screen backend is required by these integrated modules. Model 4 startup selects ADM3A; cpmsim and Model II start with the basic console. Separate ANSISCRN, M4SCRN and M2SCRN modules remain available to clients of SCRN/SCX, such as TED and DUMP paging. HELP and its topic library are shipped and use the TCAP 2.0 direct API. TYPE and TED retain their existing display interfaces; see the [full impact audit](../engineering/TCAP-Utility-Impact-Audit.md). The abandoned, unreleased TCAP 1.0/template designs are historical, not compatibility modes. The supported protocols are fixed 80x24 seven-bit paths, not arbitrary host geometry. See the [direct ABI and caller helper contract](../engineering/TCAP-Direct-ABI.md). The old split MCON/SCRN descriptions below remain relevant to standalone backends and historical implementations; do not treat their backend-pointer requirements as prerequisites for the integrated 1.1 modules.

Callbacks are non-reentrant and must not call BDOS, load overlays, allocate, change profiles or recurse through routed console output. Return status without consuming input. Keep incomplete sequences and replies bounded; command return resets parser continuation while retaining normal display/modes and keyboard semantics. Load backend first and unload personality first. A private host MCON 1.0 table template is not portable scaffolding merely after changing one capability bit.

Use [monitor development](../programmers/Monitor%20RSX%20Development.md) for editable examples and the [final MCON/SCRN/SCX summary](../programmers/BETTERCPM-API.md#mcon-scrn-and-scx) for version relationships. Provider/operation versions are different identities. A fixed-grid renderer and SCX delayed-wrap renderer must resynchronize explicitly. A synthetic callback test does not prove terminal rendering, audio, keyboard mappings or original application compatibility.

For a clock provider, advertise TIME and translate hardware into one coherent validated five-byte sample. Bound retries across rollover and reject torn/invalid data. Preserve caller output on failed sampling as defined by the service. Optional SET capability requires full-record validation and a verified hardware update; a read-only implementation omits the bit and returns SET_UNSUPPORTED. Keep Gregorian formatting in transient consumers and historical selector translation in optional frontends. No clock module should impersonate another whole operating system or add timestamp semantics implicitly.

## Reuse input and archive libraries

These are build-time reusable code, not new resident APIs. Include the same selected sources for native and cross builds and keep storage caller-owned. Do not alter a shipped utility's input behavior merely because a newer library profile is more convenient.

### Single-line input

The standard engine requires EDITBUF, EDITLEN, EDITCUR, EDITSTART, EDITMAX and EDITPROMPT. `UE_INIT` takes A=capacity (1–255), B=initial length, HL=prompt; invalid initialization returns carry/UI_BAD without changing state. `UE_KEY` takes one logical byte and returns an event, not an inferred condition flag. It does no input/output.

| Event | Value | Caller action |
| --- | ---: | --- |
| UI_MORE | 0 | Redraw after recognized editing, even a clamped movement. |
| UI_SEND | 1 | Validate/accept counted candidate. |
| UI_ABORT | 2 | Cancel; do not commit application data. |
| UI_DEF | 3 | Controller selected separate default. |
| Reserved | 4 | Not an event to invent. |
| UI_LIMIT | 5 | Capacity refused insertion; preserve editability. |
| UI_SKIP | 6 | Unassigned key; preserve current message. |
| UI_BAD | 7 | Invalid initialization/controller configuration. |

The standard controller's accepted candidate returns HL pointer and **B byte length**, not BC. Empty accepted input is distinct from cancellation. A separate default is read-only and is not copied into EDITBUF. Validation should inspect without modifying the candidate or application state; normalize into owned application storage when committing. No automatic keyboard flush occurs, so a choice consumes only its chosen byte, not a queued Enter.

Use `tools/shared_ui.py` source selection, preserving include order/flags. Pick standard, words, text-controller and choice-controller components according to need. Render through hooks rather than hard-code another utility's screen. [Shared Input Library](../programmers/Shared%20Input%20Library.md) contains the complete hooks, return contracts and compatibility consumer bindings. ED, Function 10 and CCP editing remain distinct interfaces.

### Archives

Archive parsing separates exact-byte callbacks, directory/member interpretation, optional codec/integrity work and CP/M file ownership/publication. A listing is not an integrity test. AS_END is ordinary member/directory completion; I/O/truncation errors must never become a clean EOF. Bytes 00h/1Ah/high-bit data remain ordinary bytes unless an explicit format length or codec says otherwise.

The initial reusable LBR reader uses caller-owned context and READ callbacks with exact transfer accounting. OPEN validates the directory envelope, NEXT selects members, READ consumes bounded member data and CLOSE ends state without owning a caller's external stream. Its CP/M adapter owns its own FCB/DMA workspace and must be closed even after a partially successful open. Restore DMA after use. Public entries preserve IX/IY/alternate registers/SP under that library's contract; general registers are scratch unless returned.

[Archive Read Library](../programmers/Archive%20Read%20Library.md) is explicitly the initial implementation record, not a complete final NOAH API. The current [archive includes](../../src/archive) and focused [NOAH specification](../engineering/NOAH%20Specification.md) define later reader/writer/codec interfaces. Treat them as source-level/provisional reuse with matching includes, not a new stable binary SDK. The documentation expansion does not require freezing every internal archive interface for 1.0.

## Diagnose and qualify your program

First separate failure layers: command lookup, operand parsing, file/record service, device/terminal binding, service discovery, provider operation, or program memory. Preserve the actual result/status before printing diagnostics; console output calls may destroy scratch registers. Check exact DU and image identity rather than assuming the program's location is its input directory.

| Stage | Useful evidence |
| --- | --- |
| Assembly/link | Tool identity, Errors: 0, no undefined symbols, executable interval and map. |
| Determinism/parity | Same selected inputs produce identical bytes; native/cross differences explained. |
| Controlled execution | Known data and expected results; owned buffers/stack; deliberate unavailable/error paths. |
| Lifecycle | Return, WBOOT, carrier reconstruction, provider movement and unload. |
| Platform integration | Real patched cpmsim/trs80gp setup, actual screen/input, current image hashes. |
| Distribution | Separate selection, companions, licenses and reproduction review; a local successful example does not enter locked media. |

Use DDT for controlled 8080 tracing, DASM for Z80 analysis and STAT MEM for the current memory map. A debugger's own resident footprint changes available debuggee memory. Do not infer the logical end of a binary by stripping 00h/1Ah/FFh; they can be instructions/data. When reproducing compatibility problems, compare equivalent environments and separate documented API behavior from undocumented hardware/private-address assumptions.

The examples' source/build checks are recorded in [REFERENCE-STATUS.md](../programmers/REFERENCE-STATUS.md). They are not new release-wide emulator or hardware qualification. Further tutorial breadth, complete archive SDK stabilization and a portable terminal starter are explicit expansion work, not hidden 1.0 blockers.
