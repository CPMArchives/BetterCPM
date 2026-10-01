# Engineering Specification 182: Implementation Item 3 Closure

## Result

Implementation Item 3 is complete. The retained command environment now has a
single qualified production path for CCP dispatch, BCPX-v1 CPX profiles,
BRSX-v2 RSX profiles, required SUBMIT/XSUB input, transient reclamation, warm
reconstruction, ordered unload, rollback and callable resident services.

The final ROM-profile failure was a relocation defect in the disk-loaded CONFIG
overlay used by Function 176. The ROM profile loads that overlay into writable
RAM at `DA6Dh`, rather than its conventional linked address `F000h`. Relocating
only its final `EX_RETURN` jump left its internal control transfers pointing at
`Fxxx` ROM addresses. `CPX LIST` consequently entered unrelated immutable disk
code and profile changes did not complete.

The existing dual shifted-layout analysis now inventories all 105 address words
in the z80pack CONFIG overlay. It resolves 102 to the accepted live-RAM map and
three to packed immutable code. The ROM-media builder applies that complete
inventory and records every source and destination in `rom-config.json`. The
boot verifier independently reconstructs the relocated overlay and rejects
missing, overlapping or changed operands.

`CPX.COM` also establishes a private 64-byte stack before making nested control
and output calls. This follows the full-TPA transient contract: the protected
system supplies only its small return stack, while a utility with deeper call
requirements owns its working stack. The utility remains an ordinary transient
and does not reduce the 53 KiB TPA.

## Focused diagnosis

The closure work used bounded probes rather than an open debugging session:

1. the direct Function 176 handler passed;
2. the complete conventional extension gateway passed and preserved `DE`, `IX`
   and `SP`;
3. the BIOS overlay loader was shown not to replace the saved caller stack;
4. a direct relocated-ROM gateway probe reached `F0EDh`, proving that CONFIG's
   internal `F000h` links, rather than gateway state, caused the failure; and
5. complete CONFIG relocation made the original protected cpmsim lifecycle pass.

The Stage-3 coordinator fixture still encoded the former `0E00h` transaction
reserve. Its four boundaries now use the production `0F00h` reserve. This was a
stale test fact; production coordinator behavior did not change.

## Qualification evidence

- BCPX format, name-based Function 176 control, CCP dispatch and transient-load
  result tests pass.
- The BRSX carrier, slots, snapshot, preparation, plan, schedule, mover, commit,
  coordinator, resolver, stateful service, service gateway, loader-safety and
  runtime-overlay tests pass.
- cpmsim stateful relocation, warm boot and rollback pass.
- Protected cpmsim cold-boots with the `DF00h..FFFFh` write boundary enforced.
- `CPX LIST`, ordered load, command dispatch, WBOOT reconstruction, middle
  unload, final unload and transient fallback pass.
- Dynamic RSX load, list and unload pass in the same protected run.
- CPU writes, DMA writes, guest unlock, boundary changes and reset persistence
  are rejected or restored as specified.
- The default TPA returns to 53 KiB after CPX and RSX profiles are removed.

The local `trs80gp` 2.5.8 executable currently aborts inside macOS AppKit
application registration before guest execution. Its unavailable run is a host
GUI startup failure and does not alter the BetterCP/M result. Final release
qualification will rerun the Model 4 matrix in a working host environment.

## Disposition

The fixed Implementation Item 3 matrix is closed. Later implementation items
may rely on the frozen CPX/RSX formats and lifecycle contracts. Release-candidate
qualification must rerun these gates; it must not reopen their architecture
without new failing evidence.
