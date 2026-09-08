# Full-TPA COM loading

2026-09-08. Replaces the 47.75 KiB loading restriction recorded in the earlier
compatibility campaign. The default COM file limit is now 424 CP/M records:
54,272 bytes (53 KiB). The TPA remains 54,273 bytes; a COM file is stored in
128-byte records, leaving one byte unused at this boundary.

The CCP parses the filename and opens it as before, then prepares the default
FCBs and command tail while its command line still exists. It copies the open
FCB into the protected module reader's idle 36-byte FCB, selects the physical
buffer as staging DMA, and transfers control to a protected system-stack entry.
The module reader's code remains intact: no overlay restoration is needed.

The permanent reader loads one 128-byte record into protected buffer memory,
checks the inclusive last destination byte against the active ECB_TPATOP,
and copies only fitting records into the TPA. EOF permits execution; other
read results and oversized records enter warm boot without executing a partial
image. User number and DMA=0080h are restored on either exit. Successful launch
saves the current target of the public page-zero WBOOT jump as its protected
return address. Entry RET therefore bypasses a transient program's temporary
page-zero hook while still reaching the protected reconstruction path after the
CCP has been completely overwritten. As with all full-TPA loads, a program must
provide its own stack for deep use; the initial protected return stack is small.

The active ceiling includes installed RSXs: it is read at run time, not taken
from the default 53 KiB constant. CPXs and the CCP are reconstructible; RSXs,
persistent history, and the protected core are above the applicable ceiling.

The gateway uses its existing initialization padding for entry/exit code.
Private adapter vectors are packed at EXT+3 (login), +6 (open), +9 (read), with
+12 entering the COM reader; all source consumers move together. Extensions
grow from 399 to 425 bytes, consuming 26 previously spare bytes after BDOS.
No TPA, history, sector buffer or drive capacity is removed. Builder checks
protect the FCB and gateway entry offsets. These are private internal entries,
not changes to the standard BIOS vectors or CP/M BDOS calls.

Failed loads after handoff now warm boot because the CCP may already be gone.
They may already have prepared page-zero arguments; they never launch the
partial program. Missing-file failures before handoff still follow the CCP's
ordinary path. Error text for the protected failure path is not yet added.

## Evidence

`build/compatibility/load-boundary-20260908-082021/` contains private emulator
images, patterned COM fixtures, recorded screens and fixture parameters.
FIT: 424 records loaded and independently checked byte-for-byte beyond its
initial code record, printed LOADOK FIT, then warm-booted and ran VER.
OVER: 425 records did not execute and returned to a working prompt that ran VER.

`tools/test_ccp_load_results.py` runs assembled CCP and protected handoff code
with deterministic EOF/read-error providers, testing status 1, 2, FF and a
nonterminating record stream. Checks include default arguments on successful
launch, no execution on failure, warm-boot handoff and caller-user restoration.
The BIOS retry, BIOS-vector and unified-BDOS tests also pass on the new layout.

The old `test_system.py` harness still fails at its pre-existing EF03h warm-boot
address expectation. `test_ccpreload.py` still uses obsolete fixtures and fails
at DFFEh after correcting its entry addresses. These results are not counted as
passes; real-emulator warm reconstruction is tested by the boundary workflow.

The real trs80gp RSX-manager regression also passed: ordered loading, chaining,
warm restoration, middle unloading, and TPA restoration.

A second maximum-size run used RET instead of JP 0 and successfully rebuilt
the command environment and ran VER. The fresh `build/z80pack-full-tpa` target
passed cpmsim boot, DIR, transient/warm return, B–D create/write/close/open/read,
DUP copy/check, RSX load/unload, and 53 KiB TPA checks; cpmtools independently
verified the written files. Full-size patterned-file boundary testing was on
trs80gp; the z80pack run was the normal distribution regression.

The later `tools/test_ret_termination.py` probe replaces page zero's WBOOT
target before returning from its entry point.  It proves that entry RET does
not invoke that public hook, that the command environment is reconstructed,
and that a following VER command runs.  This closes compatibility item 0509
without changing the 54,273-byte TPA or any resident allocation.
