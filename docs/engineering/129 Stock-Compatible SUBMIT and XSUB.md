# Stock-Compatible SUBMIT and XSUB

Date: 2026-09-08

## Result

BetterCP/M now builds native `SUBMIT.COM` and `XSUB.COM`, consumes the CP/M
2.2 reverse-record `$$$.SUB` command stack in the CCP, and supplies submitted
BDOS Function 10 input through the protected BRSX mechanism.  The ordinary
53K target remains unchanged.  No fixed BIOS, BDOS, gateway, history, or
persistent-data address was allocated for this work.

## Reference behavior

The implementation was checked against Digital Research's *CP/M 2.0 Interface
Guide* material in the July 1982 *CP/M Operating System Manual*, the published
CP/M 2.2 `submit.plm` and `ccp.ASM`, the preserved DRI `XSUB1.ASM`, and the
project's frozen 0620/0621 propositions and RUN42/IN42 fixtures.

The compatibility contract implemented here is:

- `SUBMIT name [p1 ... p9]`, with the source type forced to `SUB`;
- upper-case source translation, `$0` through `$9`, `$$` for a literal dollar,
  and `^A` through `^Z` for control bytes;
- blank-delimited parameters, 125-byte expanded command limit, and the DRI
  2K aggregate command buffer limit;
- one counted 128-byte record per non-empty command, stored in reverse order;
- CP/M `1AH`, physical sequential EOF, CR, and CR/LF source handling, including
  a final source line without CR;
- A-drive `$$$.SUB` consumption by both CCP and XSUB, one record per use;
- deletion at exhaustion, after a bad submitted command, on console abort, and
  after malformed/read/close failures;
- XSUB interception of Function 10 only, caller maximum-length truncation,
  caller DMA preservation, input echo, and pass-through after the stream ends.

## Design

The CCP does not gain a `SUBMIT` resident command.  It checks A:$$$.SUB during
command acquisition, copies one counted record into its ordinary command
buffer, publishes the decremented record count, echoes the line, and uses the
normal CPX/transient dispatcher.  The file is the durable continuation: a warm
boot can reconstruct every byte of the CCP and CPXs without losing the next
command.

`XSUB.COM` installs `BATCHIO.RSX` through BetterCP/M Function 202.  BATCHIO owns
its FCB, record buffer, remembered DMA address, and Function-10 adapter inside
protected dynamically allocated memory.  When it later observes that the
stream is absent it requests operation 4, a deferred profile retirement.  The
manager removes the reconstruction record immediately but waits for WBOOT to
rebuild the chain, avoiding the unsafe act of overwriting a module while that
module is executing.  The manager still occupies its original packed slot and
the persistent RSX table keeps its original size and ownership.

## Memory cost

| Component | File/code bytes | Protected cost |
|---|---:|---:|
| `SUBMIT.COM` | 3,274 | none after return |
| `XSUB.COM` | 151 | none after return |
| `BATCHIO.RSX` | 436 | 512 while active |
| BRSX manager | 893 | existing 1,024 charge while any BRSX is active |
| CCP submitted reader | included in 3,066-byte CCP | no new fixed allocation |

With no RSX, the maximum record-aligned COM remains 54,272 bytes
(`0100H..D4FFH`).  With BATCHIO as the only active BRSX, the tested maximum COM
is 52,736 bytes; this is the existing 1K manager charge plus BATCHIO's 512-byte
allocation, not a reduction of the default target.

## Evidence

`tools/test_submit_xsub.py` creates private TRS-80 disk images and verifies:

- ordered execution, `$1`, `$$`, EOF without final CR, and `$$$.SUB` cleanup;
- continuation after a 54,272-byte COM overwrites the complete default TPA;
- Function-10 delivery after a 52,736-byte COM overwrites the entire active
  TPA, followed by WBOOT reconstruction and another submitted command;
- pending-console cancellation across WBOOT, unknown-command cancellation,
  parameter errors, and cleanup in every case.  The cancellation probe seeds
  the documented test build's protected pending byte so timing cannot make the
  keyboard-status assertion intermittent.

The preserved RUN42/IN42 pair produced `IN42 count=07 data=BATCH42`, satisfying
the operative 0620 ordering and 0621 buffered-input propositions.  The larger
RUN42 survey proceeds to PIP, which is outside this task and was not present on
that disposable BetterCP/M image.

The complete-system build, BRSX manager regression, CCP/system regressions,
TRS-80 boot workflow, and z80pack image build are the release checks for this
change.

Final reproducible artifact hashes from the passing build are:

| Artifact | SHA-256 |
|---|---|
| `SUBMIT.COM` | `e14e07726d2b5028f8555917dd482295d7814079b00025415d2d5b480ea150c5` |
| `XSUB.COM` | `07cb79e6648419193685225cd6c652bd72882f860b367da14601c613b18deca8` |
| `BATCHIO.RSX` | `10318199b11d224603e4ef7701e1892948291830dbc870dba05e2ca191b534d6` |
| TRS-80 system DMK | `ea693c74552d9ade733cb6a339907cc284b22b5237c6d36902c3cb585f330ee6` |
| disposable z80pack system disk | `abcbbd781e8151a63dbe7b23a9bb8485032c4ad9533ce51890cc3850d975d26c` |

Observed results on the final tree:

- PASS: `test_submit_xsub.py`;
- PASS: `test_ccp.py`, `test_ccp_acquisition.py`, and
  `test_console_direct.py`;
- PASS: `test_rsx_manager.py` (after operation 4 was added), complete-system
  construction, BATCHIO/ECHO coexistence and Function-203 chaining, z80pack
  construction, and `test_z80pack_boot.py`;
- STOPPED outside this change: `test_system.py` still expects page-zero WBOOT
  `EF03H`, while the concurrently edited canonical layout places
  `LY_BIOS+3` at `EA0BH`.  No SUBMIT/XSUB code or allocation owns that vector,
  so this task did not alter the overlapping BIOS/BDOS/layout work.

## Limits and follow-up

Flow control, named-directory syntax, and other enhanced scripting remain
loadable-CPX work.  BetterCP/M reconstructs its CCP after transient return, so
the stock `(xsub active)` notice is emitted on BATCHIO's first public BDOS pass
after reconstruction rather than by code installed in page-zero WBOOT.  Its
lifecycle and meaning are preserved, but exact screen placement is a remaining
presentation difference from a non-overwritten DRI CCP.
