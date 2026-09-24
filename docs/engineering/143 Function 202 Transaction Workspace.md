# Engineering Specification 143: Function 202 Transaction Workspace

## Status

Stage 3 increment 9 defines and implements the caller-owned workspace contract
needed by the stateful reconstruction coordinator. Request version 2 is the
sole BetterCP/M 1.0 public request and does not yet enable production
`STATEFUL` loading.

## Request version 2

Function 202 request version 2 uses the original 14-byte request prefix:

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

The transitional implementation can still recognize request version 1, but
no supplied caller emits it and it is not a BetterCP/M 1.0 compatibility
contract.

The bounds must describe a nonempty range beginning at or above `0103h` and
ending at or below the current page-zero TPA ceiling. The stateless path does
not consume the range. The transaction coordinator must reject invalid
bounds before changing the active profile and must also prove that its concrete
plan, slot unions, descriptors, and prepared snapshots fit without intersecting
the prospective live allocations.

## Utility ownership

`RSX.COM` and `XSUB.COM` set the low bound to the end of their loaded image.
Immediately before calling BDOS each sets the high bound below its transient
stack and at or below the current page-zero TPA ceiling. Thus transaction
scratch is memory the utility actually owns; the operating system does not
guess that an arbitrary fixed TPA address is unused.

The resident BATCHIO provider also emits request version 2 for deferred
retirement operation 4. That operation schedules removal for warm boot and
does not construct a transaction, so its workspace words remain zero and are
not consumed.

This adds no protected-memory allocation and does not reduce the default TPA.
The next increment uses this bounded workspace to construct the prospective
profile and prepared snapshots before invoking the disk-free commit engine.
