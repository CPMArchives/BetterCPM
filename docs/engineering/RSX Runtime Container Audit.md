# RSX runtime container audit — 1.0 feasibility

Date: 2026-10-11. Status: fixed-slot implementation complete; qualification results below.

## Finding

Combining the 15 distributed R3 helpers into one fixed-slot file is practical
without BDOS growth, protected-loader growth, new persistent state, or changed
memory boundaries. Recommend proceeding as a bounded 1.0 packaging/reader change,
subject to runtime qualification. This does not replace the post-1.0 review of
the manager architecture or its comparison with Z-System.

## Existing paths

`tools/build_rsx_runtime_overlays.py` emits each selected helper as exactly
1,024 bytes, including gateway trailers where required. The runtime helper
reader is RI_ENTRY in `src/system/r3entry.mac`. It is copied to transaction
scratch+0400h and is limited to 256 bytes; private state follows at +0500h.
It stages two 512-byte reads before installing the helper into CFG or RSX.

Other FLOPEN calls in coordinator/profile/retained/removal code open actual
extension carriers. Those calls must remain ordinary filename opens: only
internal helper descriptors passed to RI_ENTRY change to slot identifiers.
The protected loader at LY_FILE stays 145/145 bytes and its FCB stays at
LY_FILE+109. The normal CPX/RSX loader ABI stays unchanged.

## Proposed minimal layout

Working filename: `R3PACK.RSX`, an internal container, not a loadable extension.
Use the current manifest order, 15 fixed slots of 1,024 bytes; slot i starts at
sequential FCB record i*8. Offsets range from 0 to 112 records. The complete
file is 120 records / 15,360 bytes, below the 128-record logical-extent limit.
Thus no random-read interface, seek loop, archive directory, or decompressor
is needed. `UB_READCORE` reads FCB+32 and maps that record through the allocation
map already populated by OPEN.

RI_ENTRY opens the common filename, then stores the selected start record in
LY_FCB+32 before its existing two block reads. Internal eight-byte helper names
can become one-byte start-record descriptors. The existing six-byte handoff
request still points to a descriptor; its structure need not grow. Preserve
all payload bytes and gateway trailers exactly. Keep the ordinary extension
carrier open/reset path unchanged.

The container filename is copied position-independently from the reader's own
embedded constant, using IX-relative address arithmetic. Private scratch byte
IX+18 holds the start record across OPEN; it is within the existing reserved
256-byte scratch state/stack area. No additional reserved RAM is required.

## Measurement

An isolated assembly prototype changes only the copied RI_ENTRY reader:

| Measurement | Current | Prototype |
| --- | ---: | ---: |
| Reader bytes | 188 | 212 |
| Reader allocation | 256 | 256 |
| Remaining reader space | 68 | 44 |
| Embedded R3ENTRY image bytes | 620 | 644 (projected from reader delta) |
| BDOS growth | 0 | 0 |
| Protected file-loader growth | 0 | 0 |

The 24-byte delta includes the shared eight-character container stem, scratch
record storage, position-independent filename address calculation, and the
FCB record update. This is assembled size evidence, not runtime qualification.
Bounds/version/integrity guards are not included in that minimal measurement.

R3PROF is currently 1,012/1,012 bytes, but its four eight-byte helper names
can shrink to four one-byte descriptors, recovering 28 bytes. The reader
change belongs to R3ENTRY/copied scratch rather than R3PROF. Other caller
images similarly recover seven bytes per helper descriptor. R3COMIT's gateway
and resolver trailers must be retained, not repurposed.

With the current 2 KB allocation blocks, separate helpers occupy 30 KB;
one 15 KB container occupies 16 KB. Saving: 14 KB and fourteen filenames.
Directory-slot savings depend on DPB geometry; do not equate filenames with
physical extent-entry count on every format.

## Work and qualification required

- Generate the pack and descriptor constants from one explicit ordered table;
  reject missing, duplicate, oversized or changed-slot payloads at build time.
- Update helper descriptors and RI_ENTRY together. Never silently use an old
  pack with a new system. Decide the bounded version/short-container check;
  a full general container API is unnecessary.
- Preserve normal RSX/CPX carrier opens and resets. Internal helper requests
  must select only valid slots and must not be treated as normal filenames.
- Update native builds, host builds, boot/system assembly inputs, both
  distribution manifests and qualification tools. Existing per-helper build
  artifacts can remain for diagnostics while only the pack is distributed.
- Check exact slot reads on both DPBs, including the first and last slots;
  check missing/truncated pack failures without installing partial code.
  Existing FL_NEXT accepts some partial final blocks, so that behavior alone
  is insufficient as proof of an exact helper read.
- Exercise load, retained reload, unload, replacement, failure recovery, clock
  provider installation, warm-boot reconstruction and disk-free resolver use
  on cpmsim and Model 4. Verify original file-loader ABI, scratch bounds,
  gateway bytes and memory allocations remain unchanged.

## Recommendation

The narrow reader change is small enough for 1.0. Implementation touches several
callers and packaging/test paths, so qualification is the main cost. Proceed
with the fixed-slot approach, preserving the existing overlay architecture;
leave architectural redesign for the agreed post-1.0 review.

## Implemented cleanup

`R3PACK.RSX` contains the existing fifteen 1,024-byte slots in the fixed order
owned by `tools/rsx_container.py`. Host and native source expansion derive
record constants from that table. Eight-byte internal helper names become
one-byte slot descriptors; public extension carrier names and the handoff
request layout stay unchanged. Ordinary helper artifacts remain available
for diagnostics. Distribution media contain only the container. ROM-profile
media receive a pack constructed from their relocated helper payloads.

The final copied reader is **242/256 bytes**. It checks RC=120, slot range,
slot alignment and the final sequential record position before installing a
complete helper. This rejects missing, truncated and partially read input.
The reader's first slot is record 0 and its final slot is record 112.
The complete R3ENTRY image is 660 bytes; the reader delta plus smaller entry
descriptors leaves its existing allocation unchanged. BDOS, the 145-byte
protected file loader, its FCB ABI and ROM/RAM ownership totals are unchanged.
No runtime signature/version header was added: slots are fixed and the pack
is a build-matched system dependency, distributed atomically with that build,
as the former separate helpers were.

Focused qualification passes for all 15 slots through the production copied
reader and protected loader, scratch-stack restoration, invalid slots,
truncated length, first/last slot read failures and partially padded blocks.
The coordinator preparation, complete stateful Stage-3 transaction, gateway
frame preservation, loader safety and resolver checks pass. Native build-disk
validation and all seven distribution-builder tests pass.

Both clean distribution builds boot successfully. cpmsim contains 19 files
and 214 KB free; Model 4 contains 18 files and 662 KB free. Each saves 14 KB
and fourteen filenames. cpmsim's distribution clock-provider load also passes.
The architectural comparison with Z-System remains post-1.0 work.

Cross-platform lifecycle qualification also passes on cpmsim and trs80gp:
load HELLO and STATEFUL, initialize/mutate retained state, remove HELLO, check
retained state, warm boot, check again; then remove R3PACK and verify failed
unload preserves the live profile and state. Both platforms pass.
