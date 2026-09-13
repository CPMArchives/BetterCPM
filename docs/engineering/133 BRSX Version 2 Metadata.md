# Engineering Specification 133: BRSX Version 2 Metadata

## Status

Stage 2 implementation is complete; target-system qualification remains. The carrier format, validation, reconstruction,
descriptor publication, central Function 208 resolver, provider conversion,
and system-track orchestration are present on both supported targets.

## Compatibility

BRSX version 2 preserves the fixed 48-byte version-1 carrier prefix where its
meaning remains applicable. Byte 4 is 2. Flags bits 0-1 contain the
reconstruction class: 0 STATELESS, 1 STATEFUL, 2 STATE_PRESERVING, and 3
COLD_ONLY. Version-1 images retain their existing untyped numeric-service tail
and are treated as legacy stateless numeric interceptors.

## Typed metadata stream

The word at carrier offset 30 points to a metadata envelope following the
linked payload. The envelope is little-endian:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 4 | `BMET` signature |
| 4 | 1 | metadata major version: 1 |
| 5 | 1 | metadata minor version: 0 |
| 6 | 1 | envelope header length: 12 |
| 7 | 1 | record count |
| 8 | 2 | total metadata length including envelope |
| 10 | 2 | reserved; zero |
| 12 | variable | typed records |

Each record begins with a one-byte type and one-byte payload length. Zero
length records are invalid. Metadata version 1 defines:

| Type | Payload |
|---:|---|
| 1 | one byte per intercepted numeric BDOS service |
| 2 | one 10-byte callable-service advertisement |
| 3 | sorted, unique 16-bit runtime-pointer slot offsets |

A callable advertisement is a four-byte service ID, ABI major, ABI minor,
16-bit entry offset from the RSX base, and 16-bit capability flags. Stage 2
allows at most two callable advertisements per provider.

## Runtime provider descriptor

Validated advertisements must be available without disk I/O while Function
208 executes. They are not duplicated in the PDS. A BRSX-v2 provider reserves
this loader-owned header at the beginning of its live allocation:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 2 | next dispatch address |
| 2 | 2 | this module's dispatch address |
| 4 | 1 | callable-service count |
| 5 | 1 | reserved; zero |
| 6 | 2 | offset of materialized service descriptors |

The loader materializes each validated 10-byte advertisement at the top of the
provider's allocation and sets the offset at +6. That range is loader-owned
and excluded from module workspace and STATEFUL pointer slots. Function 208
walks active RSX headers and these descriptors, deriving each callable address
as provider base plus entry offset. This retains no flat absolute-address table
in the PDS and charges metadata to the provider that supplies it.

The resolver is a separate on-demand overlay sharing the manager's 1 KiB slot.
It occupies 779 bytes and performs no disk access during lookup or enumeration.

## Loader integration constraint

The current version-1 manager already occupies all 893 bytes available below
its 128-byte control stack and the fixed three-byte gateway. A first complete
version-2 parsing/materialization pass measured 1,186 bytes before optimization.
It was not retained because reducing validation or leaving an inadequately
sized stack would make RSX reconstruction unsafe.

Loader publication therefore uses four mutually exclusive system-track images
in the existing 1 KiB manager slot:

1. a validator checks the complete proposed profile, including all version-2
   metadata, reconstruction classes, entry bounds, capacities and duplicate
   service IDs;
2. the compact rebuilder reloads and relocates the already validated profile;
3. a materializer rereads validated metadata, clears provider allocation tails,
   and publishes the callable descriptors;
4. the disk-free resolver replaces the materializer only after publication.

The fixed Function 202 bridge orchestrates those phases. No phase calls code
after replacing its own image. Validation failure leaves the published profile
unchanged. The validator may reopen earlier carriers to detect duplicates rather
than reserving a flat scratch registry in the PDS; reconstruction is rare and
the extra disk reads cost no resident RAM. The existing four RSTSERV words serve
as transient validation checksums and are restored to their legacy enumeration
meaning during publication.

This arrangement keeps noninteractive Function 202 users such as XSUB working,
adds no permanent protected code, and does not reduce command history or other
PDS allocations. Once a profile is active, the same one-kilobyte charge that
formerly held the manager contains the resolver instead.

The validator occupies 933 bytes. Its focused tests cover valid
version-1 and version-2 carriers, unsupported reconstruction classes, metadata
bounds and framing, callable entry bounds, duplicate IDs within one provider,
duplicate IDs across the live profile, and sorted, unique runtime-pointer slots.

The rebuilder accepts both carrier versions and occupies 935 bytes, retaining
an 86-byte control stack below the fixed gateway. Descriptor publication is
isolated in a 457-byte overlay; its focused test verifies allocation-tail
clearing, descriptor copying, and runtime-header publication. Separating these
operations avoids weakening either validation or stack safety.

The TRS-80 BIOS remains within its original protected allocation. A 65-byte
transient selector and the four physical-sector tables occupy unused padding in
the existing command-reloader system-track block. z80pack selects the four raw
record ranges directly and reserves seven boot tracks. Each stored overlay ends
with the correct dynamic BDOS gateway, so phase changes never expose a damaged
CALL 5 target.

The carrier builder includes the descriptor bytes when calculating the minimum
page-rounded allocation. BRSX-v2 dispatch and callable entries must lie beyond
the eight-byte runtime header and within the emitted payload.
