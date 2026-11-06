# BetterCP/M 1.0 interface reference

This is the BetterCP/M-specific API part of the [Programmer's Guide](../manuals/Programmers-Guide.md). The [CP/M 2.2 reference](CPM22-API.md) defines the compatibility baseline. Here, a selector assignment means an implemented service boundary; it does not promote every private implementation detail to a stable third-party ABI. Observe the stability and caller-precondition notes below.

Original prose is CC BY 4.0; original reusable code examples are GPL-2.0-or-later. See [licensing](../LICENSING.md).

## Contents

- [Authority, namespace and stability](#authority-namespace-and-stability)
- [176 — CPX profile](#function-176)
- [177 — RSX profile and reconstruction](#function-177)
- [178 — Cursor presentation](#function-178)
- [179 — Printer echo](#function-179)
- [180 — Version descriptor](#function-180)
- [181 — Disk configuration](#function-181)
- [182 — Resident services](#function-182)
- [183 — Optional FDF mapper](#function-183)
- [TIME and P2DOS](#time-and-p2dos)
- [Carrier formats and lifetime](#carrier-formats-and-lifetime)
- [MCON, SCRN and SCX](#mcon-scrn-and-scx)
- [Private BIOS and PDS boundaries](#bios-private-boundary)

## Authority, namespace and stability

The software baseline is `30b24a021cc3a90eb725cc3d1760dfe0dc31daa8`; accepted qualification merge is `2842d0eb0732683d9280a38d576c3dba423cb893`. The [non-documentation lock](../releases/non-documentation-lock-1.0/README.md) governs supplied artifacts and later dispositions. The inspected main core/BIOS/extension/platform source matches that locked source; current FDB development and metadata are a separate matter.

| Range | Meaning |
| --- | --- |
| 176–183 | Assigned production BetterCP/M service selectors below. |
| 184–196 | Unassigned production space. No callable contract. |
| 197 | Reserved, undefined future escape. No request layout or dispatcher operation. |
| 198–199 | Non-public proof/conformance selectors. HELLO/ECHO examples are not application APIs. |
| 200–201 | Inherited optional P2DOS compatibility calls, outside the private namespace. |

Provisional assignments 200/202/204/205/206/207/208/209 for private services were replaced by 176/177/178/179/180/181/182/183. They are not aliases. In particular, 200 now means P2DOS GET when that frontend is installed; it never means CPX control. Historical engineering logs retain their original numbers.

Call assigned selectors through `CALL 0005h` with C=selector. Little-endian words, reserved-zero fields, explicit versions, caller-owned nonwrapping memory and balanced SP are the general convention. **Flags have no universal success meaning**: use the specified A/HL result. Other registers are scratch unless the individual contract preserves them. Request layouts do not prove that a callee authenticates memory ownership: callers must supply complete, accessible blocks and all required workspace.

Functions 176/177 and raw disk/monitor integration expose current, bounded implementation contracts. Use the supplied management utilities for ordinary management; new binary-compatibility promises require their own review. Registry/TIME have explicit versioned contracts. A service ABI, carrier format, module version and OS version are independent.

<a id="function-176"></a>

## 176 — CPX profile control

Input: C=176, DE=12-byte version-1 request. DE is preserved. Normal extension epilogue restores SP/IX; do not rely on other working registers/flags. Operations manipulate the ordered reconstruction profile, not an already executing command chain.

| Offset | Size | Input/output |
| --- | ---: | --- |
| 0 | 1 | Version=1. |
| 1 | 1 | Operation 0 enumerate, 1 load/append, 2 unload/remove. |
| 2 | 1 | Zero-based enumeration index; ignored for mutation. |
| 3 | 1 | Reserved=0. |
| 4 | 8 | Uppercase, space-padded carrier stem; copied out on enumeration. No extension or drive prefix. |

Enumerate returns A=1 with a name, A=0 at end. Mutation returns A=0 on success/no-op; unsupported version/operation or capacity failure returns FFh. The profile holds four names including normal RCP, preserving insertion order. Duplicate LOAD and absent UNLOAD are no-ops. Mutation callers must normalize valid filenames themselves; the protected handler rejects a blank name but does not replace CPX.COM's full parser.

A successful append does not certify a carrier. Reconstruction reads `A0:stem.CPX`. Missing optional carriers can be skipped; opened invalid carriers produce `CPX?`, roll back their allocation and are omitted while configured names remain. A configured record therefore consumes capacity even when its commands are unavailable. Valid carriers are initialized in order; failure invokes the defined reverse cleanup and empty-chain recovery. End a management transient through WBOOT so the protected code reconstructs CCP/CPXs; never relocate an executing CPX in place.

## 177 — RSX profile and reconstruction

<a id="function-177"></a>

Input: C=177, DE=18-byte version-2 request, or a 20-byte version-3 request for explicit carrier locations. This is the production BRSX-v2 transaction gateway. Treat all scratch/workspace as owned by the manager for the call. Supplied callers compute bounds around live code, buffers and their stack; supplying the entire apparent TPA indiscriminately can overwrite the caller.

| Offset | Size | Field |
| --- | ---: | --- |
| 0 | 1 | Request version=2 (18 bytes) or 3 (20 bytes). |
| 1 | 1 | 0 enumerate, 1 LOAD, 2 UNLOAD, 3 QUERY, 4 self-retirement. |
| 2 | 1 | Enumeration ordinal for operation 0; v3 LOAD search mode (0 exact, 1 current source then A0). |
| 3 | 1 | Flags/private result state; write zero. |
| 4 | 8 | Uppercase space-padded filename stem; enumeration output. |
| 12 | 2 | Enumerated primary numeric service word; FFFFh can mean no numeric service. Not a callable-service identifier. |
| 14 | 2 | Caller workspace lower address for mutations. |
| 16 | 2 | Caller workspace exclusive upper address. The manager can lower it to its effective ceiling. |

Enumeration/QUERY return A=1 when present, A=0 when absent/end. LOAD/UNLOAD return zero on success/no-op; nonzero, commonly FFh, means failure. Test by operation, since 1 is a valid enumeration success. There are four profile entries. Version 2 retains fixed-A0 source lookup. Version 3 appends zero-based drive (0–15) at +18 and user (0–31) at +19. For LOAD only, +2 is 0 for that exact location or 1 to retry A0 after an unsuccessful open; an opened invalid carrier never falls through. ENUMERATE and successful QUERY return the retained source DU in +18/+19. Keep the matching R3PACK.RSX and R3CACHE.RSX manager runtimes in A0. Successful LOAD of an existing name and UNLOAD of an absent name are idempotent.

LOAD/UNLOAD prepare the complete prospective profile, carriers, metadata, placement, snapshots and pointer repairs before live mutation. During preparation, the old published profile remains usable. The locked normal path clamps transaction workspace to at most 7000h and reserves its overlay/stack band (0F00h in that path); these are implementation facts, not workspace a client can reclaim. A request can fail for insufficient scratch despite apparently sufficient resident allocation. Use the supplied `RSX.COM` implementation as the exact transient-call pattern.

Operation 4 is a tightly coupled provider self-retirement path which can reclaim the caller and warm boot. It is not a general returning UNLOAD convenience. Do not invoke it from arbitrary callbacks or assume execution resumes at the next instruction.

Retained STATEFUL RSXs survive ordinary WBOOT without reloading disk defaults. Commit is bounded memory work followed by final publication; an invariant violation after movement starts is not a recoverable disk error and must not be reported as a successful rollback. Version-2 A0 lookup, four-entry capacity, explicit ordering and specific monitor/clock conflict rules do not constitute a general declarative dependency framework.

After successful installation, neither warm boot nor later profile changes reopen that provider's carrier. The manager retains a compact carrier capsule in its charged allocation, preserving pristine STATELESS templates and STATEFUL relocation/metadata facts. Runtime pointer repair retains the provider's original allocation boundary; capsule addresses are not provider-owned relocation targets. A shared 1 KiB capsule reader is charged while any provider is installed, in addition to the existing 1 KiB manager. Per-provider capsule storage is page-rounded and reclaimed on unload. The last unload restores the no-RSX TPA. This is RAM residency across WBOOT, not persistent installation across cold boot; the System manager runtime remains a separate disk dependency.

Implementation anchors: [transaction entry](../../src/system/r3entry.mac), [coordinator](../../src/system/r3coord.mac), [supplied caller](../../src/utilities/rsx.mac), [prepared commit record](../engineering/151%20Stage%203%20Prepared%20Profile%20Commit.md). The record's historical 202/208 numbers are superseded by 177/182.

<a id="function-178"></a>

## 178 — Optional cursor presentation

C=178, E=0 queries support; a nonzero E draws that character using the active private cursor presentation. A=0 means unsupported; a nonzero query result means available. Drawing **advances** the physical/personality cursor and cooked BDOS column once; it is not a write-and-hold primitive. Use the current monitor/backend, not direct video-memory writes. The extension epilogue restores SP/IX; other working registers and flags are not a portable application contract. Query first and supply a visible fallback when unavailable.

The old reverse-cursor engineering record calls this 204; that assignment is historical. A terminal personality's operation 3 uses C for the character, while this top-level BDOS call takes E. Confusing those two entry conventions produces incorrect drawing.

<a id="function-179"></a>

## 179 — Command-environment printer echo toggle

C=179 toggles the shared cooked-console printer-echo byte. It has no input request and no separate get/set operation. The locked return A/L reflects the complemented state; do not interpret it as a general success status or assume zero means failure. It belongs to command-environment integration. Ordinary programs should avoid toggling a global state without an explicit user policy. It does not print a string or select an IOBYTE route. SP/IX are restored by the extension wrapper; other scratch/flags remain unspecified.

<a id="function-180"></a>

## 180 — Protected subsystem version descriptor

C=180, no parameter. HL points to immutable resident data; A=L and B=H are provided by this extension return path. SP/IX are restored. Validate the signature/format before reading records. The pointer describes fixed resident strings for this running system; it is read-only and must not be persisted for use after another boot/build.

| Offset | Size | Meaning |
| --- | ---: | --- |
| 0 | 2 | ASCII `BV`. |
| 2 | 1 | Descriptor format=1. |
| 3 | 1 | Component count. |
| 4 | 2 | `$`-terminated system identity pointer. |
| 6 | 2 | `$`-terminated release string pointer. |
| 8 onward | 6 per component | Identity pointer, API-version pointer, implementation-version pointer. |

The fixed component records cover CCP, BDOS and BIOS. CPX/RSX facility identities have their own tools/descriptors. Validate BIOS API compatibility before using appended private vectors; Function 12 returning 22h is not enough to establish BetterCP/M BIOS extensions. Normative assignments come from the matching software's subsystem metadata, not a current-main development table.

<a id="function-181"></a>

## 181 — Runtime disk configuration, ABI 5

C=181, B=operation, DE=request except discovery. For operations requiring a request, reserve a complete 80-byte block wholly within owned TPA at or above 0100h. HL=0 success, 1 invalid/error, 2 unsupported or a controller-specific nonzero error; A mirrors L. Discovery instead returns a descriptor pointer in HL. IX and caller SP are preserved; other registers/flags are scratch. Error codes overlap validation/controller domains, so retain the operation context.

| B | Operation | Request content |
| --- | --- | --- |
| 0 | Discover | No request. HL points to BDCF descriptor. Validate signature and ABI before further calls. |
| 1 | Read physical profile | +0 physical index; +1..6 receives profile. |
| 2 | Set physical profile | +0 physical index; +1..6 proposed profile. |
| 3 | Read logical binding | +0 logical index; +1..64 receives normalized binding. |
| 4 | Set logical binding | +0 logical index; +1..64 proposed binding. |
| 5 | Format one cylinder/side | +0 logical, +1 cylinder, +2 side, word +3 stream length, word +5 stream address. |

Discovery is 16 bytes: `BDCF` at +0; ABI=5 at +4; logical count at +5; physical count at +6; binding length at +7; pointers at +8 physical table, +10 logical table, +12 last physical-read buffer, +14 optional cached-format entry. Locked counts are four/four and binding length 64. Do not use normal status interpretation on discovery's returned pointer.

Physical-profile fields are size in inches, cylinders, sides, WD step-rate code, spin-up quarter-seconds, settle milliseconds. Proposed capabilities cannot be reduced below an attached format's requirements. Reject unsupported geometry rather than silently choosing another format. These are platform profiles, not universal controller timings.

### Normalized 64-byte binding

| Offset | Size | Meaning |
| --- | ---: | --- |
| 0 | 1 | Physical selector 0–3; FFh unbinds supported B–D. |
| 1 | 15 | Standard DPB; little-endian words. |
| 16 | 1 | Cylinder count. |
| 17 | 1 | Physical sectors per side. |
| 18 | 1 | Maximum sector-size code: 0=128, 1=256, 2=512, 3=1024. |
| 19 | 1 | Format flags, including MFM 80h, double-side 40h, inversion 10h; special mapper/internal bits require their defined normalization path. |
| 20 | 32 | Sector IDs in logical skew order; unused bytes zero. |
| 52 | 1 | 0 uniform or 1 explicit mixed-size map. |
| 53 | 8 | Four two-bit size codes per byte, low bits first. |
| 61 | 3 | Reserved=0. |

Use the validated format construction/normalization path for cylinder-based BCPM780 and mapper-dependent formats. Do not fabricate internal 20h semantics merely because an old document calls them a “790K default.” BCPM780 is the locked Model 4 System layout; optional MMI012 historical 790K is distinct. The named binding and runtime SPT/OFF conversion are implemented, not a pending redesign.

Active records are BIOS authority. FDF/FDB is construction input, not runtime indirection; replacing a catalogue cannot reinterpret a saved/active binding. Commit invalidates derived login/cache context. Close files first, and reset before using aliases after media changes or writes through another alias. No background detector makes arbitrary disk swapping safe. A is the protected bootstrap binding, and physical drive 0 cannot be a destructive-format destination through an alias.

Logical storage has an implementation stride of 80 bytes (DPH then binding); table/ALV/CSV pointers are inspection-only and transient across context changes. Ordinary clients use operations 2/4, not writes through returned table addresses. Warm boot preserves supported active bindings; cold boot loads saved defaults. Persistence belongs to CONFIG/SYSGEN's implemented saved-state path, not a hidden Function-181 save opcode.

### Physical buffer and cached formatter

A nonzero +12 descriptor pointer exposes the complete last physical sector after a successful standard READ where the adapter supplies it. Copy immediately; later disk/overlay operations can overwrite it. Zero means unavailable. The sector length comes from the selected binding, not an assumed 1024-byte result.

A nonzero +14 pointer is the optional transient cached-format entry. After successful GET LOGICAL, an integrating utility copies the 1024-byte control image from the advertised buffer to private TPA. Immediately before a direct cached call, restore that image to the same BIOS-owned buffer, with no intervening disk I/O. Pass the valid 80-byte operation-5 request in DE. IX is preserved and A/HL carry ordinary formatter status; test A explicitly, not carry. The snapshot is valid only within this transient and BIOS image. Never save it as a persistent API object. Platforms without this capability use ordinary operation 5.

Timed controller loops and write-track streams are porter/utility work. The BIOS bounds the stream but does not certify its internal CRC/address-mark content. DUP owns stream construction, user confirmation, progress and verification. A successful per-track formatter does not install an OS or prove a whole-media interchange format.

<a id="function-182"></a>

## 182 — Callable resident-service registry, ABI 1

C=182, DE=accessible caller-owned 20-byte request. A=status; HL=callable address after successful LOOKUP, zero otherwise. DE, SP, IX and IY are preserved; other general registers/flags are undefined. The caller must supply the full request even when probing for absent services. The gateway does not retain its address.

| Offset | Size | Input/output |
| --- | ---: | --- |
| 0 | 1 | Structure version=1. |
| 1 | 1 | Length=20. |
| 2 | 1 | Operation 0 LOOKUP, 1 ENUMERATE, 2 DESCRIBE_REGISTRY. |
| 3 | 1 | Flags=0. |
| 4 | 4 | Exact uppercase space-padded service ID. |
| 8 | 1 | Required ABI major. |
| 9 | 1 | Minimum ABI minor. |
| 10 | 2 | Required capabilities. |
| 12 | 2 | Returned entry address. |
| 14 | 1 | Returned ABI major. |
| 15 | 1 | Returned ABI minor. |
| 16 | 2 | Returned capabilities. |
| 18 | 1 | Enumeration ordinal on input; provider index on successful output. |
| 19 | 1 | Returned status. |

LOOKUP requires exact ID/major, sufficient minor and every required capability. On failed lookup output fields are zero except documented diagnostic exceptions. A successful ENUMERATE describes an entry in the request, with HL=0; do not mistake HL=0 for enumeration failure. DESCRIBE uses +12 for active service count, +14 provider capacity, +15 per-provider capacity, +16 total capacity. Locked capacities are 4, 2 and 8; discover rather than hard-code them.

| Status hex | Meaning | Status hex | Meaning |
| --- | --- | --- | --- |
| 00 | Success | 01 | Service not found |
| 02 | ABI major unavailable | 03 | Minor too old |
| 04 | Missing required capability | 05 | Bad request version |
| 06 | Bad request length | 07 | Bad operation |
| 08 | Bad service ID | 09 | Registry corrupt |
| 0A | End enumeration | 0B | Capacity exceeded |
| 0C | Duplicate service | 0D | Unsupported provider |

Only one provider per service ID may be active, irrespective of major version. The registry is derived from validated advertisements in loaded BRSX allocations; clients cannot register by writing a table. Provider indexes and enumeration order are valid only for the current layout. A resolved address expires when its resident layout changes. A transient can call it immediately while reconstruction is excluded beneath ordinary application code. A surviving/reconstructed client must rediscover or follow an explicit rebinding contract. New private/experimental IDs begin with X until a stable allocation policy is established.

<a id="function-183"></a>

## 183 — Optional FDF service

This selector is provided by optional FDF.RSX, which is **not selected System Disk content**. C=183, B=0 queries the mapper: HL=4644h (`FD`) identifies it. A zero fallback without the module is not success. B=1 is the private BIOS mapping path: IX must identify a live BIOS binding, DE is logical track and HL the 128-byte logical-sector position. Arbitrary client buffers are deliberately rejected. B=2 performs the defined extended validation/normalization path. These are hardware/filesystem integration operations, not a general public catalogue parser.

For B=1 success, A=0; C/L identify the mechanical cylinder, H the sector-ID track value, D the side, E the sector ID, and B packs `(sector-size-code << 3) | 128-byte-quarter-index`. It validates a real live binding and bounded logical position before mapping. Failure uses A=FFh/HL=FFFFh/B=0; other registers and flags are operation scratch. These are integration results for the matching adapter, not a disk-read operation.
+
+For B=2, IX points to the setter's owned 80-byte request (binding begins at +1), not a live table to patch. The helper recognizes cylinder-SPT and explicit/legacy mixed-size geometry and can rewrite candidate flag/map fields. HL=4644h identifies accepted normalization; do not infer A=0 from the query signature or assume a rejected candidate buffer was unchanged. No disk I/O or live publication occurs here: the setter must finish its ordinary validation before committing a binding. Preserve the candidate until that owner completes. General registers/flags are scratch unless specified by this matched private path.
+
+Use [FDF source](../../src/rsx/fdf.mac), the [disk configuration reference](BIOS-DISK-CONFIG.md#optional-format-mapper) and [FDF/FDB specification](../engineering/DISK-FORMAT-DEFINITION-SPECIFICATION.md) for its operation-specific binding, mapping outputs and flags. There is no generalized preservation/error convention inferred from B=0; error paths can return A=FFh, HL=FFFFh and an operation-specific result. A client must not use an unverified mapper result as a physical address. A porter choosing this optional path must qualify it with the matching module, not assume its presence in a release startup.

Unloading mapper support selects A and detaches dependent B–D aliases before memory release, under its specific contract. This is not a general dependency graph. Direct catalogue parsing belongs to the transient compiler/reader; the BIOS does not open FDB files.

## TIME and P2DOS

Resolve exact service ID `TIME`, major 1/minor 0, through Function 182. Capability 0001h means SET; the supplied FREHDCLK and ZPRTC providers are read-only. No provider or P2DOS frontend is loaded by default. Neither clock-call support nor loading P2DOS implies filesystem timestamps.

| TIME request offset | Size | Meaning |
| --- | ---: | --- |
| 0 | 1 | Version=1. |
| 1 | 1 | Length=10. |
| 2 | 1 | 0 GET or 1 SET. |
| 3 | 1 | Flags=0. |
| 4 | 5 | Clock record. |
| 9 | 1 | Reserved=0. |

Pass DE=request to the resolved entry. GET success: A=0, HL=request+4. SET success: A=0 after completed update. Failure: A=status, HL=0. DE, SP, IX and IY are preserved. Statuses are 00 success, 01 bad version, 02 bad length, 03 bad operation, 04 flags/reserved invalid, 05 unavailable/hardware failure, 06 invalid clock record, 08 SET unsupported; 07 is unassigned. A failed GET must not be presented as a valid new sample.

Record layout is little-endian day count at +0/+1, packed BCD hour/minute/second at +2/+3/+4. Day 1=1 January 1978; hour 00–23h and minute/second 00–59h. It represents local civil time with no timezone/DST/subsecond field. Validate complete BCD/range semantics before SET; zero capability does not permit guessing a hardware write path.

Optional P2DOS.RSX owns Functions 200 GET and 201 SET, DE pointing to the five-byte record directly. It resolves native TIME anew through the lower path for every request and discards the address. Results: A=00h/HL=0000h success; A=FEh/HL=00FEh installed-but-failed; A=FFh/HL=00FFh unhandled frontend absent. DE/SP/IX/IY are preserved. Failed GET leaves all five caller bytes unchanged. Read-only SET maps to FEh, not absence or chaining. Native fine-grained failures collapse to FEh; this is BetterCP/M's defined result, not an asserted historical P2DOS taxonomy.

Load the platform provider before P2DOS for ordinary use. A frontend can remain installed without a provider and return FEh. The 104/105 T104C3/T104Z8 adapters discussed in older clock architecture paragraphs are deferred from locked distribution; do not describe them as supplied optional files. See the [release lock](../releases/non-documentation-lock-1.0/README.md).

## Carrier formats and lifetime

### CPX execution and BCPX v1

Live CPX header: +0 next live base, +2 command entry, +4 initialization, +6 shutdown; each word is loader-owned. Command entry receives DE=uppercase command text and B=length; carry set means handled, clear means declined. Preserve SP/IX/IY and the **buffer contents**. Scratch registers are otherwise available; do not infer that B or DE remains unchanged on return. Match command boundaries, not just a keyword prefix. The dispatcher handles core navigation/memory commands first, then CPXs in profile order, then transients; CPX is not a universal command observer.

Initialization is called with HL=module runtime base; return A=0 success or nonzero local failure, preserving SP/IX/IY. It may use documented services, but not recursively dispatch commands. Initialize in profile order, publish only after all succeed. On failure, shut down already initialized instances in reverse order and use the defined recovery path. Shutdown also receives HL=base and must return with SP/IX/IY preserved; it cannot veto reclaiming the command environment.

The CCP calls shutdown in reverse order before any transient reclaims command code, including CPX.COM itself. WBOOT initializes fresh reconstructed instances; it does not call shutdown on overwritten bytes. State required while a transient runs belongs behind an appropriate protected service, not in CPX data or a private CCP pointer.

BCPX prefix (48 bytes): magic +0 (4), format +4=1, class +5=1, required ABI +6/+7=1/0, flags word +8, link base +10, payload size +12, page-rounded allocation +14, command/init/shutdown offsets +16/+18/+20, relocation count +22, header size +24, payload offset +26, relocation directory +28, command metadata +30, padded name +32 (8), module major/minor +40/+41, command count +42, reserved +43, payload checksum +44 (2), reserved +46 (2). All offsets are decimal. Absent init/shutdown is FFFFh in the carrier and zero in the live header.

Header/payload boundary is 512-byte aligned; the locked builder supports 512/1024/1536-byte headers for relocation capacity. Command metadata is padded eight-byte names after payload and does not consume live command memory. Relocation slots are little-endian offsets into the complete executable image. Every byte-changing address dependency must be explained by relocation; two-origin assembly must reproduce the alternate bytes. [Carrier specification 119](../engineering/119%20BCPX%20Version%201%20Module%20Format.md) and [builder](../../tools/build_cpx_module.py) define full validation. Its later handoff-policy discussion is explicitly post-1.0.

### RSX execution and BRSX v2

The first eight live bytes are next dispatch address +0, own dispatch address +2, callable count +4, reserved +5, service-descriptor offset +6. The ordinary chain entry begins at +8 or later; unclaimed BDOS calls tail-chain through the loader's next pointer. Do not capture all high selectors or treat unknown calls as owned. Calling 0005h from an interceptor for the same request can recurse. Follow an explicit lower-chain path, preserving original parameters where required. Monitor callbacks have stricter no-BDOS rules below.

BRSX prefix shares field offsets through +41 with the CPX prefix, but format +4=2, class +5=2, required ABI +6/+7=1/0, +16 is dispatch offset, +30 metadata-envelope offset, +42 numeric-service count and +46 primary numeric service word. Builder header is 512 bytes with relocation directory at +48. Allocation includes the page-rounded payload, owned state and loader materialized descriptors. BRSX v1 and checked-profile v3 are not production 1.0 carrier alternatives.

At the metadata offset, BMET envelope: +0 signature (4); +4/+5 major/minor=1/0; +6 header length=12; +7 record count; +8 total length word; +10 reserved zero word. Each record has type byte and nonzero payload-length byte. Type 1 contains numeric selectors; type 2 contains one 10-byte callable advertisement (ID4, major1, minor1, entry offset2, capability2); type 3 contains sorted unique runtime-pointer slot words. **Every unknown metadata-1.0 type is rejected**, not silently skipped.

Flags bits 0–1 encode reconstruction class: STATELESS=0, STATEFUL=1, STATE_PRESERVING=2, COLD_ONLY=3. Other bits are reserved zero. STATELESS reconstructs fresh; STATEFUL copies the full live allocation and repairs the union of static/runtime pointer slots. Add the movement delta only if the current word points into the old allocation; leave null, sentinels and fixed external addresses unchanged. Loader-owned chain/descriptor fields are not module pointer slots. The locked builder requires declared runtime slots inside payload after its eight-byte header; do not assume a broader architecture description permits an out-of-payload slot.

STATE_PRESERVING export/import is reserved, not a usable 1.0 migration API. COLD_ONLY cannot be moved by an ordinary runtime layout change; unsupported cases are rejected before mutation. Do not infer general fallible RSX init/shutdown callbacks from CPX lifecycle fields. Production monitor/STATEFUL installation must have valid initial payload state before disk-free commit; no arbitrary provider callback runs after detach/movement begins. The final prepared transaction, not an early transitional rebuilder, controls failure/publication behavior.

Callable advertisements materialize at the top of provider allocation: exclude those bytes from module workspace and pointer slots. At most two advertisements per provider are accepted in this profile. Entry offsets must be inside emitted executable payload and beyond the runtime header. Service identity is not filename or address. Read [specification 133](../engineering/133%20BRSX%20Version%202%20Metadata.md), [reconstruction contract](../architecture/21%20Stateful%20RSX%20Reconstruction%20ABI.txt) with its final-stage reconciliation, [unknown-record correction](../engineering/172%20BRSX%20Unknown%20Metadata%20Rejection.md) and [production builder](../../tools/build_rsx_module.py).

## MCON, SCRN and SCX

These are callable-service identities, not extra numeric BDOS assignments. MCON personality interprets application protocols; SCRN backend renders physical output. Both are STATEFUL. Portable MCON 1.1 uses capability 0004h and requires SCRN 1.0; full-control MCON 1.2 requires SCRN 1.1, which promises SCX 1.0 operations 17–24. Legacy MCON 1.0 is platform-bound, using Model 4/cpmsim capability 0001h/0002h directly.

Portable personality layout keeps ordinary chain entry +8, initially zero **manager-owned backend word +12**, callable callback +14 or later. Exclude the +12 word and overlapping +11/+13 words from both static and runtime self-pointer metadata. The manager binds/rebinds it after movement. Do not turn a legacy host template into a portable personality by changing its capability word.

MCON A=operation, C=character: 0 output, 1 non-consuming status (00h/FFh), 2 blocking input, 3 cursor query/draw, 4 clear/home plus parser reset, 5 parser-continuation reset retaining display/modes. HL is entry scratch. Honor the BIOS route's register requirements and balanced stack. Callbacks are sequential/non-reentrant: **no BDOS, routed-console recursion, allocation, overlay load or profile mutation**. Internal raw bypass is separate. One personality/backend role each; backend must precede the personality and cannot unload first.

| SCRN A | Operation | Key arguments/result |
| --- | --- | --- |
| 0–5 | Basic transport | MCON/basic convention. |
| 6 | Position fixed grid | B=row 0–23, C=column 0–79. |
| 7 | Write fixed cell | C=display byte including supported reverse bit; advance, clamped at right edge. |
| 8/9 | Erase suffix line/screen | C=20h normal or A0h reverse fill; retain cursor. |
| 10/11 | Scroll up/down | One line, same fill convention. |
| 12 | Fixed-grid query | HL points to `SCR`, version1/0, rows24, columns80, operation mask word. |
| 13/14 | Insert/delete line | Fill/cursor rules from screen contract. |
| 15 | Visibility | C=0 hidden, 1 visible. |
| 16 | SCX discovery | A=0/HL=descriptor on success; FFh unsupported. Check descriptor length/version/masks before use. |
| 17 | Relative movement | B=up/down/right/left (0–3), HL=count. |
| 18 | Absolute movement | HL=row, DE=column, one-based. |
| 19 | Erase | B=line/screen (0/1); C=suffix/prefix/all (0/1/2). |
| 20 | Rendition | HL=canonical nine-byte rendition record. |
| 21 | Styled glyph | C=printable ASCII; uses rendition and delayed wrapping. |
| 22 | Margins | HL=top, DE=bottom, one-based; zero selects defaults. |
| 23 | Cursor/rendition slot | B=0 save, 1 restore; restore-before-save fails. |
| 24 | Index | B=0 index, 1 next line, 2 reverse index. |

The full assigned SCX operation mask is 00FFh. Fixed-cell operation 7's clamped advance differs from styled operation 21's delayed wrap. Synchronize through operation 6 before returning from control/raw output to fixed-cell rendering. Model 4 and host backends have different style/color/geometry capabilities. Check masks rather than assuming a host's RGB or scrolling behavior on Model 4.

SCX discovery's twelve bytes are `SCX` at +0 (3), major/minor +3/+4, length +5, rows/columns +6/+7, operation-mask word +8, rendition mask +10 and color mask +11. Zero host rows/columns mean host-managed geometry, not detected dimensions. The nine-byte rendition record is flags +0; foreground kind +1 and three color bytes +2; background kind +5 and three color bytes +6. Kind 0=default, 1=palette index, 2=RGB. Flag bits 0–7 are bold/faint/italic/underline/blink/reverse/conceal/strike. Check actual masks: Model 4 advertises reverse/conceal (60h), no color; the host backend encodes FFh styles and color mask7, whose visible effect still depends on the endpoint. The backend copies/validates the record before changing state. Invalid operations/arguments return FFh; successful SCX controls return zero. General registers/flags are scratch and the stack must remain balanced.
+
+This summary locates the complete [screen backend contract](../engineering/Unloadable%20Screen%20Backend%20ABI.md), including SCX descriptor, rendition/color records, validation, cursor/wrap/margin semantics and preservation limits. Its historical checkpoints are superseded by the final full-control admission section. Personality/backend development is covered in the [guide](../manuals/Programmers-Guide.md#terminal-and-clock-providers), not a general TCAP interface. ANSISCRN requires a host terminal at least 80×24 with normal full-screen scrolling; the frozen launcher does not enforce it.

<a id="bios-private-boundary"></a>

## Private BIOS and PDS boundaries

Private vectors follow the standard 17 BIOS entries without changing their offsets. +51 physical read, +54 cursor, +57 control-overlay load and +60 RSX overlay load are platform/system integration, not ordinary application APIs. +63 is the version-gated character capability query: returns HL mask while preserving A/BC/DE/IX, with no I/O/allocation. Four nibbles describe CON/RDR/PUN/LST implemented selector bits; locked Model 4=2002h, cpmsim=7337h. Capability is not readiness. Establish BIOS API 1.6+ through Function 180 before calling +63.

MONCALL +66 routes A/C through the current monitor; MONRAW +69 bypasses it to the basic backend; MONBASE +72 restores basic binding and is manager/cold-init owned. A callback must not recursively route into itself. The versioned [monitor contract](Monitor%20RSX%20Development.md) and platform source define operation details; adding a new machine is not permission to reorder vectors.

The version-1 Extension Control Block is fixed gateway-owned discovery data, not a new BDOS selector. Its `BM`, version and flags must be validated before using fields or generation values; current placement is a generated-map fact. Use matching [gateway source](../../src/system/gateway.mac) and [memory ownership](../architecture/27%20ROM%20and%20RAM%20Ownership.txt) rather than copying a historical absolute address into an application. No unsupported generic ECB search API is invented here.

The only 1.0 PDS owner is built-in history: fixed 192 bytes, `BH`, structure version1, count, used length, four private work bytes, then 182 packed-record bytes. Cold entry invalidates its signature; the reconstructed CCP initializes empty history. Supported warm/reconstruction paths preserve it. Fixed RSX/CPX profiles, disk state, service descriptors, stacks and workspaces are not PDS allocations. No allocator, migration, expansion or HISTORY.RSX API is supplied. Signature/version validation does not fully validate malformed packed records: BCPM-AUD-003 retains its deferred disposition. See [bounded PDS contract](../architecture/29%20Bounded%201.0%20PDS.txt).
