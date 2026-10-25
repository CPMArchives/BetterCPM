# NOAH codec and production overlay integration

Status: NOAH 1.0 revision 7, bounded command-line increment, 2026-10-25.
The [behavioral specification](NOAH%20Specification.md) remains normative.
This increment implements standalone SQ/CR/EXPAND, compressed LBR ADD and
one-layer expanded LBR extraction. It replaces the monolithic development
image with production phase overlays. It does not complete NOAH: ARK handlers,
`/Q`, the remaining recovery interface, interactive browser and Utilities Disk
packaging remain outside this increment. No OS services or third-party
ZSM4/LINK versions are changed.

## Supported additions

```text
NOAH /SQ sources [destination] [ordinary authorization options]
NOAH /CR sources [destination] [ordinary authorization options]
NOAH /EXPAND sources [destination] [ordinary authorization options]
NOAH /ADD /SQ archive sources [existing LBR ADD options]
NOAH /ADD /CR archive sources [existing LBR ADD options]
NOAH /X /EXPAND archives [member] [destination] [ordinary authorization options]
```

Sources retain the shared frozen selection and DU/attribute grammar; destination
is one DU, without an output rename. Existing Y/N/All/Cancel and protected-file
policies remain in force. Conflicting operations and irrelevant options fail
before mutation. Existing LBR LIST/TEST, ordinary extraction, ADD/replacement,
REMOVE, COMPACT and capacity handling continue through the same controller.

SQ and CR use the existing codec library implementations and their conventional
Q/Z extension transformations. Explicit compression remains compression even
when output grows. EXPAND recognizes headers, not extensions; it decodes exactly
one SQ or CR layer. Recognized unsupported encodings fail explicitly. Ordinary
input copies unchanged; ordinary same-file expansion reports no change. Embedded
output names must be plain valid CP/M 8.3 names, without DU, paths or wildcards.

LBR ADD stores the complete standalone stream under its transformed name.
Collisions therefore use stored names. Existing accepted/replaced/deleted-member
rules remain in force. LBR entry padding describes the codec stream's logical
end; CRC16 still covers physical stored records. `/X /EXPAND` first verifies the
stored LBR member into an owned spool, then decodes through the standalone
machinery. Ordinary members use ordinary extraction. Expansion never implies
recursive archive processing. Nonzero archive timestamps retain the existing
explicit warning when the filesystem cannot restore them.

## Overlay and memory contract

The builder emits `NOAH.COM` and its exact matching `NOAH.OVL`. VER, HELP and
no-argument usage run resident without overlay access. Actual commands locate
the companion at invocation DU, then A0 only if absent. An invalid present file
does not silently fall back. Outputs cannot replace the resolved active companion.

The companion begins with a 128-byte header: NHOV magic, format 2, ABI 1,
eight-byte build identity, physical record count and five bounded descriptors
for the controller, SQ, USQ, CR and UNCR. A descriptor records module identity,
ABI, record range, code length, required memory end and entry addresses. CRC32
covers the complete file with its own header field zeroed. Every load checks
the entire expected header, CRC, exact physical length and EOF before executing
new code. This detects corruption and mismatched builds; it is not authentication.

Resident callbacks, mutable command state and the private stack survive swaps.
The resident trampoline reloads and verifies the controller before returning to
its caller. No replaced-module callback or return address is left active.
Writer plans and transformed identities occupy codec workspace only after
precompression is complete; codec swaps are refused while writer plans are live.

Measured layout (exclusive upper bounds):

| Region or phase | Address / size |
| --- | --- |
| Resident COM | 17,494 bytes, loaded at 0100h |
| Shared phase window | 4580h |
| Controller code | 16,723 bytes |
| Codec context | 4D80h |
| Writer plans | 8700h–9F00h, 6,144 bytes |
| Transformed identities | 9F00h–B900h, 6,656 bytes |
| Private stack | 3EEFh–40EFh, 512 bytes |
| Controller/writer required end | B900h |
| SQ / USQ required end | 5B44h / 5320h |
| CR / UNCR required end | AFF7h / B556h |
| Active ceiling with z80pack terminal providers loaded | C501h |
| Active ceiling with Model 4 terminal providers loaded | CA01h |

Each requested phase checks the active BDOS ceiling before loading or using its
workspace. The maximum B900h fits both measured configurations (3,073 bytes
below the lower ceiling). These measurements qualify the recorded systems and
provider combinations, not every possible RSX stack. The older 19,674-byte
reservation proof and revision 6 monolithic writer evidence remain historical.

## Publication and input stability

Standalone work first hashes the physical source and performs a complete codec
preflight without destination mutation. After authorization it writes an owned,
collision-checked stage, closes/reopens it, and reruns the codec to compare every
intended output byte, deterministic final-record padding and exact EOF against
that stage. Counts, digests, header names and source size must remain consistent.
The original source is rehashed before publication. A stage's own checksum alone
is never accepted as proof of intended output.

Compressed ADD preprocesses sources before allocating writer plans. Verified
encoded stages are copied into a private aggregate spool with independently
checked record writes and row metadata. Each row binds original DU/name,
original physical-source digest, encoded length/padding, payload offset and
independent encoded digest. Metadata CRC16 and readback protect the row. The
writer checks the encoded source digest and applies its usual full intended-byte
replay. Accepted originals are rehashed before archive publication, without
swapping over live writer plans.

All paths reuse checked TMP/BAK publication and rollback. Failed overlay reload
uses resident cleanup: close owned handles, restore caller state and identify
retained staging names rather than execute an unavailable controller. Close
uncertainty retains recovery artifacts. There is no in-place failure fallback,
filesystem lock or claim of power-loss atomicity. CRCs detect accidental changes;
they do not provide a cryptographic concurrency guarantee.

Physical CP/M source bytes, including all Ctrl-Z values, remain data. Decoder
logical ends and LBR padding determine encoded length; no text EOF guessing is
introduced. Ordinary ADD remains byte-preserving with zero new padding metadata.

## Qualification and evidence

- `python3 tools/test_noah_codecs.py`: 51 focused assembled-code transactions,
  independent SQ/CR byte oracles, codec round trips, transformed-name replacement,
  memory ceilings, malformed names/streams, source changes, stage corruption,
  I/O failures, missing/changed companions, exact recovery names and DU restoration.
- Existing NOAH adapter suite: 137 cases; existing LBR-write CLI suite: 38 cases.
  The separate assembled LBR writer suite retains its independent CRC and byte
  oracles. Intercepted-BDOS stack measurements are not native BDOS stack proofs.
- `tools/qualify_noah_codecs.py` assembles and links all six source modules with
  unmodified native ZSM4/LINK on both platforms. Native bytes, record padding and
  reconstructed whole companion match the cross build. Runtime commands use
  loaded terminal providers and verify the actual active ceiling.
- The retained full campaign covers codec round trips and independent fixtures,
  compressed ADD and expanded extraction, all prior LBR-write operations, missing
  and corrupt companions, plus a separate 20,480-byte Crunch/LBR extent case on
  each platform. Original system/tool disks remain unchanged.
- Final review fixed one JP target so expanded extraction reaches the existing
  unavailable-timestamp warning. The final campaign explicitly checks that only
  that jump operand and the derived companion identity/header changed, with all
  codec modules byte-identical. It rebuilds native boot/controller modules on
  both platforms and tests stamped expansion with loaded providers. It reuses
  the previously parity-checked codec modules; it does not claim a second full
  runtime campaign for that diagnostic-only delta.

See [machine-readable receipts](NOAH-Codec-Overlay-Qualification.json) and the
[portable evidence bundle](NOAH-Codec-Overlay-evidence.tar.gz). The full baseline
and final delta receipts are distinct. Their source exports, native products,
console traces, filesystem reports and hashes are retained together.

Reproduce the full native campaign with:

```text
python3 tools/qualify_noah_codecs.py --system VERIFIED_SYSTEM_PAIR --output NEW_OUTPUT
```

The system pair must pass source/image provenance verification. The former
`qualify_noah_write.py` entry point delegates to this production campaign;
revision 6 receipts remain frozen. Final Utilities media acceptance remains a
separate future gate and is not implied by component qualification.
