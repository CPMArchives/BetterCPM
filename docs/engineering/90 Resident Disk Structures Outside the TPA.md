# Engineering Specification 90: Resident Disk Structures Outside the TPA

## Milestone

The four DPHs, shared MM 790K DPB, and all per-drive CSV/ALV workspaces now
reside above the BDOS code in protected resident memory. Their earlier
placements at `C080h` and below `C100h` were inside the transient program area
and therefore were not safe merely because the first resident programs did not
use those addresses.

## Corrected resident layout

The descriptor block now occupies `C900h..CA97h`:

- four 16-byte DPHs at `C900h..C93Fh`;
- the shared 15-byte DPB at `C940h`;
- independent 32-byte CSV and 50-byte ALV workspaces beginning at `C950h`.

The block is assembled as part of the BDOS resident component, with explicit
zero bytes so native CP/M and cross builds remain byte-identical. The gateway
no longer publishes structures below the BDOS entry. Stage one retains its
historical `BF00h` load address, but the sparse leading page is not treated as
resident-owned runtime storage.

## Live configuration boundary

Directory Services refreshes the active mapping fields from the live DPB at
filesystem entry boundaries. This preserves the intended future CONFIG model:
the DPH/DPB is authoritative, while cached arithmetic values are disposable.
The added code extends Directory Services through `E8D5h`; the CCP initially
moved to `E8E0h`, retaining a ten-byte guard. Specification 94 later consumes
that verified gap and starts the CCP immediately afterward at `E8D6h`.

## Verification and remaining work

All 17 BIOS contracts, all 39 BDOS function tests, Directory Services tests,
CCP tests, composed-system tests, and native/cross byte-identity checks pass.
The reproducible compatibility disks were regenerated from the corrected map.

Focused `BIOSTEST /0449` still reports failure at its traced Make lifecycle.
Therefore this milestone claims the resident-map correction, not completion of
items 0449, 0456, or 0458. Temporary instrumentation proved the descriptor
bytes are intact through Reset, scratch-drive selection, and cleanup; the next
investigation is the cached directory state while the guarded BIOS shims are
installed.
