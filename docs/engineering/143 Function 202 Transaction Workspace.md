# Engineering Specification 143: Function 202 Transaction Workspace

## Status

Stage 3 increment 9 defines and implements the caller-owned workspace contract
needed by the stateful reconstruction coordinator. It preserves the version-1
request and does not yet enable production `STATEFUL` loading.

## Request version 2

Function 202 request version 2 retains the complete 14-byte version-1 prefix:

| Offset | Size | Meaning |
|---:|---:|---|
| 0 | 1 | request version, 2 |
| 1 | 1 | operation |
| 2 | 1 | enumeration index |
| 3 | 1 | reserved zero; private phase markers are manager-owned |
| 4 | 8 | space-padded RSX filename stem |
| 12 | 2 | returned primary numeric service |
| 14 | 2 | caller-owned workspace low address, inclusive |
| 16 | 2 | caller-owned workspace high address, exclusive |

Version 1 remains accepted and continues through the existing stateless
reconstruction path. Version 2 is also accepted by that path, allowing the
public utility to move to the new request before stateful reconstruction is
selected.

The bounds must describe a nonempty range beginning at or above `0103h` and
ending at or below the current page-zero TPA ceiling. The legacy stateless path
does not consume the range. The transaction coordinator must reject invalid
bounds before changing the active profile and must also prove that its concrete
plan, slot unions, descriptors, and prepared snapshots fit without intersecting
the prospective live allocations.

## Utility ownership

`RSX.COM` sets the low bound to the end of its loaded image. Immediately before
calling BDOS it sets the high bound below its current stack, retaining 64 bytes
for the caller's live stack. Thus transaction scratch is memory the utility
actually owns; the operating system does not guess that an arbitrary fixed
TPA address is unused.

This adds no protected-memory allocation and does not reduce the default TPA.
Existing version-1 clients, including XSUB's BATCHIO control requests, remain
valid. The next increment uses this bounded workspace to construct the
prospective profile and prepared snapshots before invoking the disk-free
commit engine.
