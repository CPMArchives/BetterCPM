# Engineering Specification 142: Stage 3 File-Backed Overlays

## Status

Stage 3 increment 8 provides the storage and safe handoff needed for Function
202 integration on both supported platforms. It does not yet select the new
transaction path from Function 202.

## Constraint and decision

The TRS-80 boot area is exactly 20 KiB and the relocatable CCP carrier leaves
only 468 unused bytes. Enlarging the system area would change the qualified
disk formats and the native `SYSTEM.SYS` contract. The transaction components
therefore live as five private files in user zero:

- `R3PLAN.RSX`, the prospective planner at `LY_CFG`;
- `R3SLOTS.RSX`, the pointer-union preparer at `LY_CFG`;
- `R3SNAP.RSX`, the fresh and stateless snapshot constructor at `LY_CFG`;
- `R3MOVE.RSX`, the mover, scheduler, and handoff packed into `LY_CFG`; and
- `R3COMIT.RSX`, the disk-free commit engine at `LY_RSX`.

They are implementation overlays rather than BRSX providers. An attempted
ordinary `RSX LOAD` still fails BRSX validation.

## Safe replacement

The handoff runs from the tail of `R3MOVE.RSX` at `LY_CFG+0320h`. It opens a
named private overlay with the existing user-zero file stream, reads exactly
1 KiB into the requested destination, restores the supplied next-request
address in DE, and jumps to the replacement entry. Because it executes outside
`LY_RSX`, it can replace the active reconstruction coordinator without ever
returning through overwritten code. Read failure returns to the unchanged
manager call frame with an error.

The commit file is padded to the complete manager slot and restores the fixed
BDOS gateway in its final three bytes. The packed move image is checked for
component overlap at build time.

## Qualification

The focused Z80 test uses the real packed move image and a filesystem stub to
replace `LY_RSX`, verifies both 512-byte reads, confirms the exact transferred
image and next-request pointer, and returns through the original stack. Both
platform image builders install the same five private overlay payloads.

The next increment connects the Function 202 coordinator to these phases and
constructs its validated plans, unions, and prepared snapshots.
