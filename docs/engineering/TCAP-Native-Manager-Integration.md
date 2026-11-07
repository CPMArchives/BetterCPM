# TCAP native-reference manager and loader integration

Status: privately staged implementation and CPU qualification, 7 November 2026.
Follows [matching-system/validity qualification](TCAP-Matching-Validity-Results.md),
PR #658. Production `src/`, installed systems and distribution media are unchanged.
The public TCAP request ABI remains a proposal. Utility migrations, HELP delivery
and release assignment remain deferred.

## What is now integrated

The native Model 4 reference path no longer depends on the campaign supplying a
prepared validity record or manually admitting the manager's component buffers.
The campaign runs the actual native reloader, native selector path, file-backed
manager entry/reader, context producers, finalizer, scheduler, mover, persistent
publisher and resolver. Disk services are controlled; the CPU executes the
manager and loader instructions themselves.

The complete sequence installs SCRN, installs the private TCAP owner, begins and
ends a scope, rejects mutations while active, unloads/reloads at the same address,
changes an unrelated profile member, and reconstructs retained members from
manager-owned caches after the original carriers are removed. The manager issues
and publishes validity itself. A reservation burned by a late commit-read error
cannot become the validity of a later successful request.

Native warm reconstruction invokes owned-session recovery, checks the CCP before
relocation/publication, and preserves the boot-global namespace and resident
owner. A normal ANSI MCON 1.2 profile also installs, writes through its backend,
survives warm reconstruction and unloads without consuming TCAP validity. Removing
the last provider restores the unloaded TPA ceiling.

This closes the **manual preparation and explicit gate invocation** seams from
#658 for this bounded native reference candidate. It does not qualify production
installation, the checked cpmsim profile, native assembly parity or hardware.

## Manager preparation and publication

The private durable profile context grows from 31 to **33 bytes**. Its new word
at +31 contains the validated prospective owner's validity destination, or zero
when no TCAP owner remains. Append, retained-context and removal producers reserve
and initialize the larger context. Distinct internal markers 5Ch/5Dh replace
5Ah/5Bh, and every corresponding consumer changes together. The finalizer rejects
old markers rather than interpreting a shorter record as the new representation.

Monitor preparation now treats private **MCON 1.3 as requiring SCRN 1.1**. The
old arithmetic `minor - 1` would incorrectly require SCRN 1.2. The preparer also
computes the validity destination from the final movement plan; it does not
write a validity value into the live owner during preparation. Legacy MCON
selection remains on its existing rules.

The finalizer reserves a **49-byte** commit request:

| Offset | Private field |
| --- | --- |
| 0–40 | Existing prepared commit fields |
| 41 | Pointer to the request's four-byte reservation at +45 |
| 43 | Final owner-validity destination, or zero |
| 45 | Root-issued validity value, unused when destination is zero |

After all scratch bounds and preceding preparation checks pass, the finalizer
prefetches the resolver and move image. A helper in the unused portion of the
publisher slot constructs the new fields and asks the permanent allocator to
write only into durable transaction scratch. It skips reservation when no TCAP
owner remains. Exhaustion aborts before movement. The public profile-control
request still reports its existing generic failure; this does not allocate a new
public error ABI.

The actual persistent publisher copies the reserved value, publishes the Monitor
binding, and returns to commit's final generation store. CPU checkpoints at the
publisher and `RC_GENWRITE` verify that validity and binding are complete while
the generation still has its previous value. No fallible display callback or
late file operation is added inside movement/publication.

The complete pipeline also uses production's snapshot/cache-footer and mover
bound hooks. The commit image is linked for its actual manager execution address;
the earlier 7C00h fixture link is retained only for component tests. The removal
producer clears both bytes of the absent validity destination, preventing a stale
word from being treated as a publication target.

## Loading and matching-system admission

The private inventory now covers **22 roles**: BIOS, CCP, native reloader, stage 2,
transaction entry, cache worker, staged reader, and all fifteen manager slots.
A four-byte admission mask replaces the earlier one-byte mask. This native
profile requires every role except stage 2, which it does not execute. The BIOS
role belongs to the trusted, sealed resident image; it is not re-hashed after
normal BIOS state has changed. Initial resident-image installation remains outside
this campaign's qualified boundary.

The root pins each role's length and CRC. A raw-object entry validates the bounded
logical payload before code installation/execution; padded physical blocks may
contain a longer available buffer. The source-closure identity and sealed manifest
bind the private build. CRC compatibility checks are not protection against
hostile software with arbitrary CP/M memory access.

The executable front doors enforce the following order:

- **Native reloader:** BIOS still fetches the two physical sectors, but transfers
  to the permanent gate before executing their contents. Failed verification stops
  at the named fatal disposition, before command reconstruction/publication.
- **Native selector:** selection executes from the trusted permanent root. Both
  sectors of a requested bootstrap helper are quarantined in BUF, checked, then
  copied while preserving the manager's return-frame band and fixed gateway.
  No selector code is executed from an unchecked reloader-block tail.
- **Worker bootstrap:** the entire 2,560-byte worker is checked before interpreting
  its relocation metadata. Its trailing staged reader is separately checked before
  being installed as an executable front door.
- **Manager reader:** before first admission it reads and checks all fifteen slots.
  Every requested slot is checked again immediately before installation, including
  after initial admission. A changed file cannot rely on a previously set bit.
  Once the required inventory has passed, later requests omit the redundant full
  preflight but retain their per-copy check.
- **CCP:** the reloader checks its raw linked payload before relocation and before
  publishing the new command environment. It does not compare a relocated or
  stack-mutated image with the raw-image pin.

Ordinary profile queries remain available while a portable session is active.
LOAD, UNLOAD and self-retirement reject before filesystem preparation. The
finalizer and commit retain their independent busy guards as well.

## Placement and measured costs

| Item | #658 candidate | Integrated native candidate |
| --- | ---: | ---: |
| Added permanent reservation versus original reference | 512 bytes | 1,024 bytes |
| Measured root portion | 512 bytes | 868 bytes |
| Gateway plus root | 760 bytes | 1,116 bytes in a 1,272-byte region |
| Fixed resident image | 7,100 bytes | 7,612 bytes |
| Unloaded, record-aligned TPA | 53,760 bytes | 53,248 bytes |
| Resident boot sectors | 14 | 15 |
| Boot-volume OFF / DSM | 3 / 384 | 3 / 384 |
| Manager workspace band | 0F00h bytes | 1000h bytes |
| Staged reader private code capacity | 256 bytes | 512 bytes |
| Native reloader logical bytes / capacity | 932 / 932 | 960 / 960 |
| CCP logical bytes / allocation | 5,610 / 5,632 | 5,626 / 5,632 |

The private bases are SYS=D1C4h, history=D104h, TPA=D101h and RSX=CD04h.
BDOS and the higher components retain their addresses. COM handoff offsets,
protected history/PDS size, packed-image reservations and overlay limits remain
checked. The extra boot sector ends the command area at sector 42, still within
the private three-track reservation. The boot volume remains 10,240 bytes smaller
than the original OFF=2 volume; this PR does not take a second 10 KB reduction.

The standalone owner still declares 2,304 bytes. The real manager charges its
existing extra 256-byte cache-footer page, so its measured live allocation is
**2,560 bytes**. That page preserves provider-owned allocation/padding; it is not
new TCAP permanent state. The root survives unload of every optional provider.

Growing the reader exposed a real overlap with its old state/stack area. Its
private state moves from entry+100h to entry+200h; scratch-frame, saved-CFG and
prefetched-resolver offsets and bounds move together. The old nine-byte manager
return-frame band remains protected. No global BDOS stack is enlarged or reduced.

The expanded pin table is emitted in bounded data lines. An additional build
assertion checks all 88 pin bytes and disjoint four-byte mask/counter storage;
otherwise this assembler can silently truncate an overlong data directive.

## Executed evidence

Run the [integration campaign](../../tools/prototypes/tcap/README.md#native-manager-and-load-front-door-integration).
It uses the pinned monitor-test environment and the repository's existing
z80pack C CPU/drive-user-aware filesystem fixture. It also requires the fixture's
local z80pack source checkout and a C compiler. No sources are downloaded.

This campaign is also checked against the merged Model II work. It uses the
current shared `crt80x24.mac` renderer with Model 4 bindings and `M2BANK=0`.
A compatibility filename is confined to its generated reference-input view;
no deleted production file is restored. Reference conditionals are resolved
explicitly, and prepared checked/Model II contexts are rejected by this command.

The [report](evidence/tcap-manager-integration/report.json),
[artifact manifest](evidence/tcap-manager-integration/manifest.json),
[core/loader patch](evidence/tcap-manager-integration/integrated-core.patch) and
[context/preparer patch](evidence/tcap-manager-integration/manager-context.patch)
record sizes, source/assembler/emulator hashes and cases. These patches are review
artifacts, not production installation patches. Generated binaries/listings and
reader/publisher assembly remain under `build/tcap-manager-integration/`.

The campaign executes the named manager/native success checks and 62 returning
failure cases, plus **412 earlier real-BDOS/owner/command-entry checks** across two
backends and two owner origins. Failures cover every manager slot during initial
preflight, every slot changed after admission, pack length, worker/header/reader
corruption, worker and pack read failures, native selector/reloader/CCP rejection,
old context markers, insufficient workspace and allocator exhaustion. A late
commit-read failure specifically verifies a burned reservation, unchanged live
profile and successful retry with a fresh identity.

The C CPU executes the complete manager path. File, drive/user, login/reset and
physical-sector services are controlled, including destructive CFG reads. The
warm integration check models cooked CR/LF at the BDOS boundary; the separate
412 component checks execute real BDOS for column/routing/stack behavior. Their
observed private-stack depths remain 26/40 bytes for Model 4 and 34/40 for the
ANSI-host fixture. Whole-filesystem/manager stack maxima and hardware timing are
not claimed.

## Remaining boundary

This is not an installable distribution. The existing native image builder still
expects a selector appended to the reloader block; a future matching package must
omit that obsolete tail and package the new layout consistently. Existing OFF=2
disks remain incompatible. Initial boot-sector/stage-one verification, actual disk
construction/installation, native assembly parity and live Model 4 behavior remain
unqualified. Checked cpmsim/stage-2 and other maintained platforms need their own
required-role policy and complete integration qualification.

The proposed full public request ABI, broader display-policy admission and final
activation/release decisions remain separate work. TYPE, TED and HELP remain
unmigrated; HELP delivery and release assignment remain deferred.
