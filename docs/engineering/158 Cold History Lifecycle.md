# Engineering Specification 158: Cold History Lifecycle

## Purpose and bounded increment

This increment completes the outstanding 1.0 PDS cold-entry correction. True
cold boot must create an empty history-v1 object. WBOOT and command-environment
reconstruction must preserve a valid object. It does not alter the fixed
192-byte PDS, introduce a general allocator, or begin the ROM/RAM redesign.

## Source finding

The CCP already owns and validates the history representation. `CCP_HINIT`
accepts a valid `BH`, version-1 header and resets an invalid header to the
canonical empty object. The common cold gateway did not distinguish a stale
but valid-looking object from new state. The z80pack platform initializer
invalidated the signature independently, while the TRS-80 initializer did not.

The correct boundary is the portable `SYS_COLD` entry. It now invalidates the
history signature before command-environment reconstruction. The reconstructed
CCP then creates the canonical empty object through its existing owner path.
`SYS_WARM` bypasses the invalidation and retains valid persistent history. The
redundant z80pack-only invalidation has been removed.

The three-byte store initially moved the protected `SYS_COMSTART` entry. The
common drive-restoration path recovered exactly two bytes by replacing a
conditional branch and unconditional BDOS call with `CALL NZ,BDOS`. This keeps
the gateway at 248 bytes, preserves every fixed entry address and retains the
32-byte system stack.

## Focused verification

`tools/test_history_lifecycle.py` seeds a valid nonempty object and proves:

- `SYS_COLD` invalidates it and the owner produces an empty v1 object;
- `SYS_WARM` preserves the seeded object byte for byte; and
- the test reaches both stable gateway entries rather than simulating their
  intended effects.

The existing history-reconstruction, PDS-descriptor and CCP tests pass. Both
TRS-80 and z80pack artifacts rebuild. The resident span remains
`D5C4h` through `EF7Fh`, the gateway remains 248 bytes and the descriptor still
publishes the 192-byte PDS with the accepted 53 KiB record-aligned COM ceiling.

The shared CCP-listing symbol parser was corrected to accept the inline label
comments required by the current source-comment convention. That test-only
change restores existing history and CCP tests; it does not affect generated
system code.

## Bounded test disposition

The broader `tools/test_system.py` currently fails the same print-string
assertion on unchanged `main`, before reaching the changed lifecycle path.
`tools/test_packed_tpa.py` also did not produce new qualification evidence:
the changed tree reached a trs80gp abort, while unchanged `main` failed earlier
in its boot-image fixture. Neither failure is attributed to this increment, and
neither was expanded into an unrelated debugging session. Final core and TPA
qualification remains part of implementation item 2.

## Disposition

The bounded PDS implementation now meets its cold/WBOOT lifecycle contract in
focused qualification. Full release-candidate qualification remains required.
Implementation item 2 continues with ROM/RAM ownership, protected execution in
place, workspace and stack evidence, and final core/PDS qualification.
