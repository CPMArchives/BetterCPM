# BetterCP/M 1.2 Practical Porting Guide

Original prose/illustrations are CC BY 4.0; original reusable examples are GPL-2.0-or-later. Third-party material retains its terms. See [licensing](../LICENSING.md).

This guide takes a system programmer from target assessment through first boot, disk and memory integration, optional services, media installation and qualification. Technical reference appears where it supports a porting task. It assumes Z80 programming and CP/M familiarity. For application programming and complete API coverage use the [Programmer's Guide](Programmers-Guide.md).

This edition describes BetterCP/M 1.2 for patched cpmsim, TRS-80 Model 4 and the 64 KiB Model II under trs80gp 2.5.8. Use matching System and Utilities downloads from the same release. Package identity and exact source/image hashes come from RELEASE.json and the release index. The prior 1.0 and 1.0.1 downloads and locks remain unchanged. See the [1.2 scope](../releases/1.2-SCOPE-AND-ACCEPTANCE.md) and [platform boundaries](../platform/SUPPORT-1.2.md); engineering receipts are not acceptance of differently hashed final media.

## 1.2 operating profile

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

BetterCP/M 1.2 supplies integrated ADM3A, VT52 and ANSI personality/renderers implementing the independently versioned TCAP 2.0 direct API. Load one with `RSX LOAD ANSI`, unload it with `RSX UNLOAD ANSI`, and rediscover services after every layout mutation. No standalone screen backend is required by these integrated modules. Model 4 startup selects ADM3A; cpmsim and Model II start with the basic console. Separate ANSISCRN, M4SCRN and M2SCRN modules remain available to clients of SCRN/SCX, such as TED and DUMP paging. HELP and its topic library are shipped and use the TCAP 2.0 direct API. TYPE and TED retain their existing display interfaces; see the [full impact audit](../engineering/TCAP-Utility-Impact-Audit.md). The abandoned, unreleased TCAP 1.0/template designs are historical, not compatibility modes. The supported protocols are fixed 80x24 seven-bit paths, not arbitrary host geometry. See the [direct ABI and caller helper contract](../engineering/TCAP-Direct-ABI.md).

Unqualified commands search the invocation drive/user first. Numeric PATH adds up to six ordered drive/user entries, default `$$: A0:`. `$$` tracks the caller; `$0` uses user 0 on the current drive and `A$` uses the current user on A. `.` is not a PATH entry. Use `PATH /H`, `/HELP` or `/VER`; `A0:PATH /DEFAULT` recovers the default. PATH is volatile: use the existing startup script to apply a preferred list after cold boot. NDR supplies named directories and PATH annotates matching numeric entries. Extended scripting remains outside 1.2.

## Contents

1. [Assess the target and define a first milestone](#assess-the-target)
2. [Reproduce the supported baseline](#reproduce-the-supported-baseline)
3. [Bring up boot and the basic console](#boot-and-basic-console)
4. [Implement the BIOS and hardware boundary](#bios-and-hardware-boundary)
5. [Integrate disks and configuration](#disk-integration)
6. [Integrate memory, overlays and reconstruction](#memory-and-reconstruction)
7. [Add screen and clock providers](#screen-and-clock-providers)
8. [Generate, install and cold-boot media](#generate-and-install-media)
9. [Qualify and document the port](#qualify-the-port)
10. [Technical reference and recovery](#technical-reference-and-recovery)

<a id="assess-the-target"></a>

## 1. Assess the target and define a first milestone

Before adapting code, create a target sheet. Separate the hardware you have from features you hope to support. A serial-console, one-boot-device milestone can be useful, but it is not permission to silently reduce the accepted 56 KiB ordinary flat-64K baseline and the explicit Model 4 exception or redefine a released target.

| Area | Record | Design consequence |
| --- | --- | --- |
| CPU | Z80 instruction support, clocks, reset and interrupt state | Core uses Z80 facilities; an 8080-only target is not a BIOS-only port. Timing-sensitive device loops need hardware measurement. |
| Address space | RAM/ROM/video/device map, reset mapping, writable areas | Fit the flat execution model and owned mutable state before adding services. No general bank-aware implementation is implied. |
| Boot source | ROM monitor, reset ROM, controller boot, removable image | Define exact entry state and loader stages; never depend on arbitrary initial register contents. |
| Console | Poll/read/write, flow control, terminal behavior, keyboard codes | Supply usable raw/basic input and output before a personality. Status must not consume a byte. |
| Storage | Controller model, sector sizes/IDs, sides, tracks, DMA, errors | Map logical records deliberately; do not assume cpmsim's simple I/O or Model 4's WD path. |
| Write protection | Hardware/protected ranges, failure reporting | Preserve software/physical protection distinctions. |
| Tools | Host assembler, native ZSM4/LINK, image tools, emulator/debug access | Reconstruct and compare coherent artifacts; record versions and dependency pins. |
| Optional devices | List/punch/reader routes, RTC, screen backend | Advertise only implemented capabilities, with explicit unavailable behavior. |
| Evidence | Emulator/hardware availability, trace/capture, media readback | Define what can actually be qualified. Boot alone is insufficient. |

Read [Hardware Abstraction](../architecture/08%20Hardware%20Abstraction.txt), [Architectural Boundaries](../architecture/03%20Architectural%20Boundaries.txt) and [Constraints](../architecture/13%20Architectural%20Constraints%20and%20Invariants.txt). The [Baseline Platform Specification](../platform/Baseline%20Platform%20Specification.txt) records the initial cpmsim development machine. Its reset/emulator details are a reference example, not universal hardware requirements or current dependency authority; use the pinned reconstruction kit for the actual release runtime.

Choose an observable first milestone: deterministic reset, a known diagnostic byte/string, a functioning non-consuming status and blocking input, then controlled transfer to the next stage. Record the expected addresses/bytes and a recovery method. Keep optional clocks, rich terminal personalities and alternate media formats out of this first checkpoint.

<a id="reproduce-the-supported-baseline"></a>

## 2. Reproduce the supported baseline

Start from an untouched copy of the matching Source ZIP, which includes the dependency tar, patches, metadata and builders needed for offline reconstruction. Automatic GitHub source archives do not contain all packaged dependency inputs. Preserve frozen archives; make a separate private working tree/output directory for experiments. A new target must have its own identity and cannot inherit the old qualification by retaining a filename.

Read the Source package README, [distribution build guidance](../releases/DISTRIBUTION-BUILD.md), [native build disk](../programmers/BUILD-DISK.md) and [pinned cpmsim reconstruction](../../third_party/z80pack/README.md). Establish Python, the expected assembler and cpmtools, plus the emulator/runtime needed by the chosen baseline. Several builders still use maintainer-local defaults; inspect the actual argument parser/`--help` where provided and replace documented path overrides deliberately. Do not copy a maintainer's absolute path into end-user instructions.

Typical existing entry points, run from the matching source root in private outputs, are:

```sh
python3 tools/build_complete_system.py
python3 tools/build_distribution.py --target z80pack
python3 tools/build_distribution.py --target trs80gp
python3 tools/build_source_disk.py
python3 tools/build_system_package.py
```

They have different purposes. `build_complete_system.py` rebuilds layout-dependent products in a coherent order; it is not an arbitrary new-platform selector. `build_distribution.py` constructs selected System media and executes its existing target validation. It does not by itself build the entire Utilities/release collection. `build_source_disk.py` creates native build/archive volumes. `build_system_package.py` composes the versioned system package. Consult the matching recipe before assuming a command replaces another.

Record source identity, selected metadata/profile, dependency/patch identities, exact commands, generated symbol maps, and output hashes. Rebuild the baseline before editing platform code. Native/cross comparison and deterministic output distinguish a source/tool mismatch from a hardware fault, but neither establishes runtime correctness on the new machine.

**Exit checkpoint:** you can rebuild and boot the unmodified supported baseline, identify which artifacts carry platform code, and explain every dependency needed to repeat it. If that fails, diagnose the reconstruction before adding a target; otherwise toolchain and porting failures become indistinguishable.

<a id="boot-and-basic-console"></a>

## 3. Bring up boot and the basic console

Create a boot contract before writing the loader: reset/entry address, memory currently mapped, interrupt state, available stack, source-device access, image units and the point at which the portable system may use its own services. A ROM monitor's temporary workspace or stack may disappear when mappings change. Load code/data into regions you have actually established as readable/writable, not an assumed CP/M map.

Use the two implemented platform families as worked references:

| Target family | Starting material | What to learn |
| --- | --- | --- |
| Model 4 | `src/platform/trs80m4/`, portable BIOS, boot/system builders | Native video/keyboard, WD-style transfer timing, DMK/media construction, reserved system area. |
| Patched cpmsim | `src/platform/z80pack/`, pinned runtime kit | Simple raw record I/O, explicit geometry interfaces, host-terminal backend and offline runtime reproduction. |

Do not transplant either family's port numbers, display addresses or disk conventions into the portable core. A new platform implementation supplies those differences behind the same boundary. Implement basic console output first; then input and readiness. Check repeated status calls with a pending byte, because consuming a key in CONST causes intermittent missing input even though a simple echo program works.

Bring up loading in increasing scope:

1. Emit a recognizable reset marker with a private bounded stack.
2. Read one known boot record, verify its destination and compare expected bytes.
3. Load the next stage without clobbering executing code, return frames or unread input.
4. Initialize resident mutable state and default disk interpretation.
5. Establish page zero only after the required context is valid.
6. Reconstruct CCP/RCP and reach a stable prompt on A0.

The cold path empties history and starts the cold extension profile. Warm boot preserves supported live RSXs/history while reconstructing reclaimable command code. They cannot share a “just reload everything” shortcut without violating state lifetime. If the prompt appears but the first transient return hangs, inspect reloader/overlay locations, system-media availability and stack ownership before changing application semantics.

**Exit checkpoint:** cold boot is deterministic; basic input/status/output work; the prompt accepts a simple command; warm return from a controlled transient reconstructs a usable command environment. Record the image and source hashes for this milestone without calling it full port qualification.

<a id="bios-and-hardware-boundary"></a>

## 4. Implement the BIOS and hardware boundary

Preserve the complete 17-vector CP/M table and three-byte JMP spacing. Keep ordinary application/BDOS semantics in portable code. The [BIOS reference](../programmers/CPM22-API.md#bios-vectors) specifies every entry and its inputs/results; the [private boundary](../programmers/BETTERCPM-API.md#bios-private-boundary) distinguishes appended BetterCP/M vectors.

Implement and test console routines independently of the CCP. A valid CONST reports 00h/FFh without consuming data; CONIN blocks and returns under the public 7-bit convention; output keeps basic backend state coherent. Routing through IOBYTE must agree with advertised character capabilities. An unsupported user-defined device should be explicitly unavailable rather than silently routed to an unrelated endpoint. The private BIOS+63 capability mask describes supported selectors, not whether data/media is ready.

For storage, separate setup from transfer: SELDSK chooses a DPH, SETTRK/SETSEC retain addresses in the adapter's declared units, SETDMA supplies the 128-byte transfer buffer, READ/WRITE complete the operation. Do not confuse BIOS SETDMA's BC argument with BDOS Function 26's DE. WRITE's C=0/1/2 hints distinguish ordinary, directory and first-new-block writes; they matter to blocking/write-through logic.

Device waits must end with a bounded error rather than hang forever. Capture the controller status and location before another command overwrites them. Never present a failed transfer's destination bytes as success. Timed loops must not gain unmeasured per-byte work; perform inversion/translation outside them where the adapter design requires it. Test adjacent record preservation when a 128-byte logical write updates part of a larger physical sector.

If you need private raw boot/overlay reads, implement the existing platform integration points rather than changing the standard vector order. Version-gate appended operations. Do not call BDOS recursively from a monitor callback or timed BIOS transfer. The portable filesystem's shared state is not a reentrant driver framework.

**Exit checkpoint:** direct-call tests cover all vectors, invalid drives, DMA handling on failures, read/write results, translation and implemented character routes. A hardware console and a disk-backed file operation must both use the production adapter, not only a mocked callback.

<a id="disk-integration"></a>

## 5. Integrate disks and configuration

Begin with one independently understood writable work format and the separate bootstrap format. Identify cylinder count, sides, sector sizes/IDs, skew, side order, encoding/inversion, reserved area, allocation blocks, directory entries and media/controller limits. Derive parameters from a reliable source or measured medium; do not guess missing physical fields from a cpmtools diskdef.

### Keep the units explicit

| Quantity | Unit | Common error |
| --- | --- | --- |
| BDOS record | 128 bytes | Treating it as a physical sector. |
| Physical sector | 128/256/512/1024 bytes in the bounded implementation | Failing to preserve other quarters on a record write. |
| Catalogue geometry | Declared format/cylinder/side conventions | Copying a cylinder count directly into a side-track field. |
| Runtime DPB SPT/OFF | Normalized filesystem interpretation | Applying an extra or missing factor of two for double-sided System geometry. |
| Allocation block | 128 × 2^BSH bytes | Confusing allocated space with logical byte length. |
| Directory capacity | DRM+1 entries | Treating DRM as the count or ignoring directory-full. |

Locked Model 4 System is BCPM780 with a 20 KiB reserved system area. Catalogue OFF=2 cylinders normalizes to four side-tracks in the accepted named binding. The optional historical MMI012 790K layout starts its directory at 10 KiB and is not an alternate name for this release boot disk. Ordinary Model 4 Work/Utilities use 800K DATA; cpmsim release images use CCS 332K. A file's extension .dsk/.img/.dmk does not establish sector order or geometry.

### Construct definitions, then validated bindings

Use [FDF/FDB format definition](../engineering/DISK-FORMAT-DEFINITION-SPECIFICATION.md) for catalogue syntax, binary framing, object/extension validation and normalization. Text FDF and compiled FDB are construction inputs. The BIOS does not open them at every transfer. BIOS-owned physical records and normalized 64-byte logical bindings are runtime authority; saved bindings contain sufficient semantics to cold boot without first reading the catalogue.

Use Function 181 discovery before reading/updating profiles. Its ABI-5 descriptor, 80-byte request and binding layouts are in the [API reference](../programmers/BETTERCPM-API.md#function-181). Four physical profiles and four logical drives are the locked implementation; expanding them is separate engineering, not a catalogue-only edit. Validate block/extent fields, directory reservations, capacity, sector-ID uniqueness, size maps and hardware capabilities before publication. Failed Set must preserve the old active binding.

Separate candidate edits, active bindings, saved defaults, observed media and derived state. Changing the active binding invalidates corresponding derived login/cache context; changing a catalogue does not mutate a live binding. Close every file first. After changing media or writing through an alias, reset before using another alias. There is no background media-change detector to rescue an unsafe swap.

The 108 admitted definitions are a compatibility catalogue, not physical qualification of every controller/format pairing. Five rejected historical records retain their validity exclusions. Preserve format provenance and “distribution rights undetermined” notices; the project's software/documentation licenses do not silently grant rights in historical data. Additional format/controller trials are independent work unless a failure affects locked release media.

### Formatting and optional mapping

DUP constructs write-track streams and owns confirmation/progress/verification. The BIOS checks supported geometry and bounds, but does not prove arbitrary stream contents are a valid disk format. Test full revolutions, address marks/CRCs, interleave, track transitions, inversion and partial-sector writes. A fast cached-format operation is an optional versioned capability, not a hard-coded hardware address; use normal operation 5 when absent.

FDF.RSX supplies optional extended mapping/normalization. It is buildable but not selected System content. If a new port requires it, include its exact lifecycle/alias tests and declare a different port's requirements explicitly. Do not make the locked 1.0 install depend on an unshipped carrier. Direct mapper operation 1 accepts only valid live BIOS bindings; it is not a general arbitrary-buffer service.

**Exit checkpoint:** independent media readback and filesystem checks agree with BIOS interpretation; ordinary files survive cross-extent/large-file and error tests; a rejected reconfiguration leaves old access intact; aliases/media changes follow a tested reset policy. Formatting a disposable track is not yet full-disk or system-install qualification.

<a id="memory-and-reconstruction"></a>

## 6. Integrate memory, overlays and reconstruction

Assign ownership and lifetime before addresses. Start from the matching generated layout and classify every byte: immutable code/template, mutable subsystem state, compatibility-visible page zero, protected RSX/gateway state, reclaimable CCP/CPX/transient memory, history, overlays and stacks. Fixed sample addresses in old milestones are not cross-platform APIs.

| Lifetime | Owner and porting obligation |
| --- | --- |
| During one transient | Application code/data/stack; do not retain a pointer after its return. |
| During one command-environment instance | CCP/CPXs; rebuild after reclamation and run CPX lifecycle correctly. |
| Installed RSX lifetime | Protected provider allocation; preserve/rebind through movement under its class. |
| Ordinary warm lifetime | Fixed bounded history and supported active state; preserve on WBOOT. |
| Cold defaults | Saved installed configuration and empty cold extension/history state. |
| One overlay phase | Shared control buffer/code/stack, with exclusive lifetime proven. |

The 1.0 PDS is only the fixed 192-byte built-in history object. It is not an allocator for your new platform state. Keep BIOS tables/stacks and manager records with their natural owners. Do not borrow history work bytes, padding in another subsystem or a former BASIC/RCP slot without an explicit ownership change. BCPM-AUD-003's malformed-history limitation remains documented; this porting work does not claim a fix.

The unloaded complete-record COM limit is 57,344 bytes on cpmsim and Model II. Model 4 retains a 54,272-byte exception because of its keyboard/video reservation. Optional RSXs consume TPA while loaded; complete unload restores the unloaded limit. Read STAT MEM and the current page-zero gateway boundary instead of assuming a hard-coded size. The first RSX also incurs 1,024 bytes of general manager overhead. TCAP full-path accounting includes the renderer, personality, facts, descriptors, cache/alignment, caller helper, shared BIOS state and call/stack allowances: at most 1,280 bytes for ADM3A/VT52 and 1,792 for ANSI; there is no additional permanent display reservation.

### Overlay discipline

Warm reconstruction and extension management read matching carriers/control images. Keep bootstrap media and A0 support files available. Never execute a return into an overlay after replacing it. Before a phase change, move needed facts and return frames to explicitly owned storage that the next phase will not overwrite. A shared physical-sector buffer is not a persistent cache or private scratch for an unrelated live operation.

LOAD/UNLOAD prepares every fallible carrier read, metadata validation, prospective layout, snapshot and pointer-repair plan before touching live allocations. The short commit phase detaches bindings, performs bounded memory work and publishes chain heads/gateway/generation last. Failure during preparation leaves the old environment. A violated commit invariant is a stop/recovery condition, not permission to invoke a moved stale provider or report an unproved rollback.

Test static relocation plus mutable runtime self-pointers. For STATEFUL, move the full allocation with overlap-safe semantics and adjust only declared current values pointing inside the old image. Null, sentinels and fixed external values remain unchanged. Rebind registry/monitor addresses from new bases. Reject unknown metadata types, unsupported classes and duplicate services before publication. Compare generations for equality only, since counters can wrap.

### ROM/XIP

For a ROM target, classify immutable executable/template bytes separately from mutable RAM state and ensure every mutable write has an owner/address. Initialize RAM from templates before use. Build/relocate matching ROM and overlays together; a RAM image that boots after copying ROM is not proof of execution from enforced immutable memory. Qualify CPU and DMA write protection, stack high-water/guards, overlay lifetime and dynamic RSX transactions under that actual map.

Locked cpmsim protected XIP has separately scoped evidence; it does not replace default RAM downloads. The 56K fullram and optional checked profiles remain deferred. A porter's optional ROM work cannot inherit those receipts for new addresses, hardware or protection mechanisms.

**Exit checkpoint:** cold/warm paths preserve their distinct state; maximum-TPA and overlay tests pass; RSX moves preserve state and repair/rebind pointers; stacks remain bounded; invalid carrier/low-memory requests preserve published state. Record unloaded and normally loaded memory separately.

<a id="screen-and-clock-providers"></a>

## 7. Add screen and clock providers

Add optional capabilities only after the basic console and disk-backed lifecycle are reliable. Keep a bootable recovery configuration with the basic console and without the new modules.

### A screen backend for new hardware

Implement SCRN on the hardware side, retaining the typed operations used by portable personalities. Model 4 provides a memory display; cpmsim's ANSI-host backend encodes host sequences. A new backend may have different glyph/style/color limits. Advertise only the appropriate compatible contract/capabilities; the two existing platform bits are not a generic discovery scheme for arbitrary hardware.

Keep basic transport status/input non-consuming/blocking as specified, then add fixed-cell position/write/erase/scroll/line/visibility operations. For full-control portable ANSI, SCRN 1.1 promises SCX discovery and all currently assigned operations 17–24. Validate descriptor length/version and capability masks. Fixed-cell clamping and styled delayed wrapping differ; synchronize trackers deliberately. A host-managed zero geometry field does not mean a zero-sized screen or successful terminal-size detection.

The manager owns monitor/backend binding and payload +12 external reference for portable personalities. Never include that word or overlapping words in self-relocation lists. Only one role instance each is allowed; load backend before personality and remove personality first. During movement detach to a safe basic binding before copying, then rebind before final publication.

Callbacks cannot call BDOS, load overlays, mutate profiles or recursively enter routed console operations. Preserve keyboard ordering and queued replies under the documented bounded model; status polling cannot invent physical arrival times. A new protocol needs its own parser/state/replies, not a list of fixed strings alone. The legacy host monitor template is MCON 1.0, not a portable replacement after a flag edit.

Use the [monitor development guide](../programmers/Monitor%20RSX%20Development.md), [screen ABI](../engineering/Unloadable%20Screen%20Backend%20ABI.md) and [current API summary](../programmers/BETTERCPM-API.md#mcon-scrn-and-scx). Qualify actual rendering, keyboard, wrapping, incomplete-sequence reset, clear, provider movement, unload, original applications and any ROM deployment separately. Dedicated ADMTST/VT52TST/ANSITST results do not certify another backend automatically.

### A clock provider for new hardware

Implement TIME ABI 1.0 once and publish it through BRSX callable metadata. Read hardware into private scratch, obtain a coherent sample across rollover, validate range/BCD and only then publish the five-byte day/hour/minute/second record. Bound waits and report unavailable/torn data rather than fabricate a plausible time.

A read-only provider is valid: omit SET capability and return SET_UNSUPPORTED. Writable support requires validating the full record before changing hardware and qualifying successful writes independently. Native clients use TIME without P2DOS. Optional historical frontends translate selectors/records without duplicating the hardware driver. T104C3/T104Z8 are deferred from locked distribution even though older architecture prose discusses them.

**Exit checkpoint:** unavailable hardware and read-only SET fail correctly; GET/lookup/version/capability contracts hold; a moved provider is rediscovered; unload removes its advertisements; ordinary warm boot preserves intended state. Neither a clock nor terminal provider expands the base filesystem or general TCAP scope.

<a id="generate-and-install-media"></a>

## 8. Generate, install and cold-boot media

Separate composition, filesystem construction, installation and execution verification. A bootable development image is not a selected release inventory. Generate from a coherent source/symbol snapshot; do not mix one BIOS with an earlier disk/control/CCP carrier simply because their filenames match.

The native System composer reads BOOT.BIN, STAGE1.BIN, RESIDENT.BIN, CCPRELOD.BIN, RSXSEL.BIN, CONFIG.BIN, RSXLOAD.BIN, RSXRESOL.BIN and CCP.RLM in its matching build environment. SYSBUILD constructs and rereads SYSTEM.SYS: one 128-byte metadata record plus 160 payload records (20 KiB), 161 records total. SYSGEN is the separate installer, so a composition failure should not write the destination system area. This is the current package model, not a generic promise that a new target's boot ROM already understands it.

Use the [native build guide](../programmers/BUILD-DISK.md) and current Source-package recipe for exact ordering and generated link definitions. The complete source archive spans companion volumes distinct from the executable native build kit. The qualified preparation workflow uses fresh A System, B build kit, C compatible work/installation target and D spare data where appropriate. Keep `A0:$$$.SUB` writable even when invoking the script from B. Scripts can change DU without relocating the authoritative queue. Do not format an output target between building SYSTEM.SYS and installing it.

For the existing Model 4 target, the concrete named-binding workflow is:

```text
CONFIG /LOGICAL=B /PHYSICAL=1 /FORMAT="BetterCP/M Model 4 System 780K"
DIR B:
SYSGEN A: B:INSTALL.SYS
SYSGEN B:INSTALL.SYS B:
```

This assumes physical 0 is a preserved writable source System copy and physical 1 is a **separate compatible System-layout target copy**, temporarily replacing normal B Utilities. It is not a command to install on an arbitrary 800K DATA disk. Review the target/confirmation and require export/install verification. The named binding performs the accepted cylinder-to-runtime normalization; do not substitute a private helper or historical manual /OFF workaround for current CONFIG.

Quit the emulator fully, mount the target alone as physical 0 and cold boot it. Verify banner, DIR, CONFIG /SHOW, RSX LIST and a known ordinary file present before installation. Verify both file bytes and directory membership, not only boot success. The known Model 4 installed bootstrap-binding byte difference at payload offset 7030 (E0→A0) belongs to its qualified normalization path; do not hide all payload differences under that one exception.

For cpmsim use its own [installation/reconstruction guide](../platform/CPMSIM-INSTALLATION.md), raw-image geometry and runtime helpers. The emulator's MOUNT changes an attachment, not the BIOS binding or running OS. Replacing A can immediately break warm-boot/overlay reads; it is not a cold boot. Model 4 .dmk and cpmtools logical .img representations are not interchangeable by suffix rename.

For interactive FDB on Model 4, unload ADM3A and any additional screen modules to recover the 54,272-byte unloaded limit. Keep FDB 1.01 and its matching viewer together. Restore the unmodified startup or cold boot after exit. Catalogue edits and live binding changes do not format media or save cold defaults.

**Exit checkpoint:** independent readback confirms image geometry, ordinary files and installed system; a cold boot of the installed target succeeds without the source/temporary helper environment; saved defaults are reconstructed without requiring catalogue reinterpretation. These results qualify the exact tested images and configuration only.

<a id="qualify-the-port"></a>

## 9. Qualify and document the port

Build an applicability matrix before running a compatibility suite. Every test is passed, failed, excluded with reason, unsupported or not run. Do not describe the number of considered cards as passes, or transfer one platform's result to another. Keep component, whole-system, media-installation and physical-hardware receipts separate.

| Layer | Minimum useful campaign | Evidence to preserve |
| --- | --- | --- |
| CPU/toolchain | Required instructions, assembler/link parity, deterministic products | Tool versions, source hashes, commands, byte comparisons. |
| BIOS | All standard vectors, readiness, routing, transfers and failures | Raw return values, DMA/adjacent-buffer checks, controller status. |
| Filesystem | Open/close, sequential/random/zero-fill, extents, full disk/directory, protection | Exact fixtures, record counts, contents and post-failure state. |
| Execution | Page zero/tail/FCBs, maximum/oversized image, return/WBOOT | Maps, guard bytes, observed boundaries and loaded modules. |
| Extensions | CPX init/shutdown, RSX move/rebind, rejection/rollback | Before/after profile, addresses/generation, state/pointer observations. |
| Console/providers | Cooked/direct, input ordering, rendering, optional unavailable devices | Captures/transcripts, host size/settings, keyboard/audio scope. |
| Media/install | Format/full readback, named binding, export/install, cold boot/file preservation | Source and installed hashes, independent directory/volume verification. |
| Optional ROM | Enforced immutable execution, CPU/DMA protection, stacks/overlays | Guard controls, actual map and matching overlay identities. |
| Distribution | Selected files, companions, notices/source and fresh-package instructions | Inventory, dependency provenance, extraction/rebuild receipts. |

The separately maintained [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite) supplies the compatibility framework. Existing tools/test and validation campaigns locate platform-specific fixtures; inspect their assumptions before reusing them on new hardware. Synthetic instruction/callback execution is useful for fault injection, but is not proof of controller timing or rendered terminal behavior.

Known baseline dispositions remain relevant: case-preserving command tails, some fixed-A0 extension lookup, XSUB's companion staging, bounded Caps Lock/CONST observations, BCPM-AUD-003 and AUD-007, deferred 104/105 adapters, and emulator-only release evidence. Do not silently “fix” those behaviors during a port and retain the old artifact identity. If a discovered defect requires changing locked software, explicitly reopen the affected lock and qualify new artifacts under that decision. This guide does not authorize such a replacement.

Write a port README describing supported hardware/revision, memory map, boot procedure, image types, console settings, drive bindings, normal startup, optional modules, recovery, tested configurations, limitations and exact source/artifact identities. Explain how an ordinary user can reconstruct/start it without your local paths. Retain source/permission notices for copied dependencies and format data. A promising boot report belongs on the platform roadmap with its bounded scope; it is not an extra qualified 1.0 platform.

**Exit checkpoint:** another person can reproduce the build and the claimed tests from the recorded inputs, and the published claim does not exceed the evidence. Remaining port/manual improvements are explicit work items, not retroactive 1.0 obligations.

<a id="technical-reference-and-recovery"></a>

## 10. Technical reference and recovery

| Symptom | Inspect first | Governing reference |
| --- | --- | --- |
| No reset marker | Boot mapping, output device, stack, entry/interrupt state | [Boot Architecture](../architecture/05%20Boot%20Architecture.txt) |
| Prompt, then hang after transient | System/A0 carriers, overlay return frames, map/stack overlap | [Memory/reconstruction](#memory-and-reconstruction), gateway/reloader source |
| Directory wrong by a fixed offset | Geometry, SPT/OFF units, BCPM780 versus 790K/data | [Disk normalization](../architecture/28%20Disk%20State%20Normalization.txt) |
| File writes damage neighboring data | Partial-sector preservation, DMA, C=WRITE hint, skew/inversion | [BIOS API](../programmers/CPM22-API.md#bios-vectors) |
| Configuration works until cold boot | Active versus saved defaults, self-contained binding | [Configuration architecture](../architecture/24%20Configuration%20Architecture.txt) and current CONFIG/SYSGEN entries |
| Provider works until moved | Undeclared self-pointer, stale callable/backend address, descriptor overlap | [BRSX/registry](../programmers/BETTERCPM-API.md#carrier-formats-and-lifetime) |
| Missing keys or duplicate replies | Consuming status, raw/cooked path, queue ordering | [Monitor development](../programmers/Monitor%20RSX%20Development.md) |
| Garbled menus after resize | ANSISCRN host minimum and redraw | [ANSI size erratum](../releases/1.0-ERRATA.md#ansi-host-terminal-size) |
| XSUB help works, activation fails | Matching BATCHIO in A0 and R3PACK | [XSUB erratum](../releases/1.0-ERRATA.md#xsub-companion-must-be-copied-to-a0) |
| Native and cross products differ | Generated symbols, phase/origin, snapshot/tool identities | [Build disk](../programmers/BUILD-DISK.md) |

Keep a known-good boot image and a way to restore/reset the target that does not depend on the damaged filesystem or optional provider. Stop writes when the format interpretation is uncertain. Preserve partial/work/backup files and controller/error records before retrying; an operation's earlier successful items may remain. Do not continue execution through a stale provider after failed reconstruction.

The technical details needed for a port are indexed here rather than repeated as another architectural catalogue:

- [Standard BDOS/BIOS, FCB/DPH/DPB reference](../programmers/CPM22-API.md).
- [Disk ABI, service registry, carrier and monitor reference](../programmers/BETTERCPM-API.md).
- [ROM/RAM ownership](../architecture/27%20ROM%20and%20RAM%20Ownership.txt), [bounded PDS](../architecture/29%20Bounded%201.0%20PDS.txt) and matching generated source map.
- [FDF/FDB definition](../engineering/DISK-FORMAT-DEFINITION-SPECIFICATION.md), [format support scope](../platform/FORMAT-SUPPORT-1.0.md), exact locked inventories and provenance.
- [Current command operation](Command-and-Utilities-Reference.md), particularly CONFIG, DUP, FDB, SYSGEN and STAT.
- [Reference status ledger](../programmers/REFERENCE-STATUS.md), which identifies stale staged material and future expansion explicitly.

Historical specifications preserve decisions and dated observations. Focused final contracts and the lock control on conflict. Extending this practical narrative with more hardware examples, a complete new-target template or controller-specific diagrams is documentation/development work for its own scope; it is not a hidden condition of announcing locked 1.0.
