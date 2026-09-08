# RET termination and z80pack READER qualification

2026-09-08.  This focused work closes CP/M 2.2 compatibility items 0509 and
0471 without running or replacing the complete 627-item conformance campaign.

## 0509: entry RET

The protected command handoff now puts the target currently stored at 0001h
on the transient program's initial stack.  This is the normal destination of
the public jump at 0000h, rather than the public gateway itself.  A program
which temporarily replaces the page-zero WBOOT target can therefore distinguish
plain entry RET from Function 0 or JP 0000h, while an ordinary RET still reaches
BetterCP/M's protected command-environment reconstruction.

The change is size-neutral.  BIOS remains 638 bytes, the protected gateway
remains 248 bytes, and the advertised TPA remains 54,273 bytes (53 KiB).

`python3 tools/test_ret_termination.py` builds a transient which saves and
replaces the page-zero target, then returns.  The test fails if the replacement
hook prints its marker.  It also requires a restored prompt and a successful
following VER command.  The focused run passed.

## 0471: normal input and absent READER

The portable BIOS keeps its default unassigned READER response of Ctrl-Z.
During the z80pack build only, that leaf is bound to cpmsim port 5, the
documented CP/M 2 RDR input port.  This adds no resident bytes.

`python3 tools/test_z80pack_reader.py` builds private z80pack disks, installs
the independently built BIOSTEST.COM, and runs its retained two-stage 0471
procedure.  Stage one starts z80pack's documented `cpmsend` provider before
cpmsim and proves that READER returns uppercase `R`.  Stage two starts a new
emulator without a sender and proves immediate Ctrl-Z.  Every expected prompt
and verdict must match explicitly; timeouts and early emulator exits fail the
harness.

The accepted evidence is in:

- `build/z80pack-reader-0471-v6/reader-stage1.txt`
- `build/z80pack-reader-0471-v6/reader-stage2.txt`

BIOSTEST's final retained verdict is:

    0471  P  R  READER returned R; absent READER returned Ctrl-Z

These focused results must still be included in the next clean consolidated
campaign ledger.  They are not a substitute for that user-run campaign.
