# Engineering Specification 181: CPX Pre-Transient Shutdown

## Result

The CCP now calls every present CPX shutdown entry in reverse profile order
immediately before handing a located transient program to the protected COM
reader. Resident `GO` and `JUMP` perform the same shutdown before transferring
control to TPA code. The caller's drive/user context is restored first, and
each callback receives its module base in `HL` as required by the BCPX
lifecycle ABI.

Commands handled by the CCP or a CPX do not reclaim the command environment
and do not call shutdown. A transient name that cannot be opened also leaves
the active chain untouched. Once shutdown begins, the CCP clears the published
head and cannot resume that instance.

The protected COM reader already treats EOF as successful completion and sends
logical read errors, BIOS errors, and oversize images through WBOOT. Those
paths therefore reconstruct a fresh command environment rather than returning
to a partly shut-down chain.

## Memory disposition

The coordinator is part of the reclaimable CCP. It grows from 4,968 to 5,029
bytes and remains inside the existing 5,120-byte allocation, leaving 91 bytes.
At most eight two-byte module bases plus a zero sentinel are retained on the
existing 128-byte CCP stack. The TPA, protected-memory boundary, command
reloader, and all fixed resident allocations are unchanged.

## Focused evidence

- Synthetic callbacks prove reverse shutdown order and clearing of the active
  head.
- A zero shutdown pointer is skipped without disturbing the surrounding order.
- Missing transient files return to the live command environment without
  invoking shutdown.
- Resident `GO` and `JUMP` shut down the chain before entering TPA code.
- Successful EOF and post-shutdown logical read, final BIOS-error, and oversize
  outcomes each invoke shutdown exactly once; every failure enters WBOOT and
  never executes the partial program.
- The complete z80pack build accounts for 68 CCP relocation references.
- Protected cpmsim execution passes cold boot, command dispatch, transient and
  warm reconstruction, directory access, and dynamic RSX load/list/unload with
  the `DF00h` CPU and DMA write boundary enforced.

## Disposition

BCPX initialization, failure rollback, publication, and pre-transient shutdown
are now implemented. Implementation Item 3 still requires its fixed closure
matrix across retained CPX/RSX dispatch, ordering, unload, reconstruction, and
failure behavior before it can be declared complete.
