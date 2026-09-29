# z80pack ROM RSX-overlay qualification

## Decision

The z80pack ROM profile relocates every file-backed RSX transaction overlay
before placing it on the ROM-profile system disk. The accepted inventory
contains 18 artifacts and 704 discovered address words, with no unresolved
target. Conventional disk images and their overlays remain unchanged.

This completes the focused Implementation Item 2 regression. Under enforced
`DF00h..FFFFh` write protection, BetterCP/M now cold-boots, executes a
transient, reconstructs through WBOOT, loads and lists `ECHO.RSX`, unloads it,
restores 53 KiB TPA, and continues normal command and directory operation.

## Isolated cause

The first protected `RSX LOAD ECHO` attempt fell through unused RAM and trapped
on opcode `ED AE` at `D62Fh`. Three bounded probes established the cause:

1. the page-zero BDOS gateway at `D501h` was valid after cold initialization;
2. the RSX selector overwrote it during the load transaction; and
3. the selector copied its replacement gateway from conventional address
   `F07Dh`, although the ROM profile's live gateway source is `DAEAh`.

The failure was therefore an incomplete ROM relocation, not a stack-capacity
fault or a general RSX-architecture defect.

## Relocated artifacts

`tools/build_rom_rsx_overlays.py` applies the established dual shifted-layout
method to:

- the RSX selector, loader and resolver;
- the six CONFIG-workspace transaction overlays; and
- the nine RSX-manager transaction overlays.

References internal to an overlay follow its ROM runtime base. References to
immutable resident objects follow the packed ROM map. References to mutable
objects follow the accepted RAM map, while legitimate transient addresses
remain in low RAM. The generated `rom-rsx-overlays.json` records every source
and destination word plus hashes of all 18 outputs.

The ROM-profile disk builder installs those relocated artifacts only in the
ROM disk. The selector's `F07Dh` gateway source consequently becomes `DAEAh`,
and the loader and resolver system-track records receive the ROM BDOS gateway.

## Enforced qualification

`tools/test_z80pack_rom_xip.py` rejects a changed artifact count, changed
reference count, unresolved target, artifact hash mismatch, or loss of the
selector gateway relocation. Its guarded boot then performs:

1. cold boot and ordinary directory/transient checks;
2. WBOOT reconstruction and a second directory check;
3. `RSX LOAD ECHO` and `RSX LIST`, requiring BDOS service 199 and 51 KiB TPA;
4. `RSX UNLOAD ECHO` and `RSX LIST`, requiring no loaded RSXs and 53 KiB TPA;
5. locked CPU, DMA and guest-control protection probes; and
6. stack-capacity and workspace-lifetime checks.

The final `rom-xip-qualification.json` binds the ROM image, relocation-manifest
hash, 18-file/704-word inventory, RSX result, stack measurements and workspace
evidence into one acceptance record. Final release-candidate qualification
will rerun this gate; it is no longer open Implementation Item 2 design or
engineering work.
