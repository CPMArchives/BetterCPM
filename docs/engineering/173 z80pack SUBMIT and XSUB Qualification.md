# Engineering Specification 173: z80pack SUBMIT and XSUB Qualification

## Result

The required CP/M-compatible SUBMIT/XSUB path is now focused-qualified on
z80pack. During qualification, XSUB exposed a transient-return defect that was
hidden by the earlier TRS-80 workflow.

XSUB formerly replaced the CCP's transient stack with the page-zero TPA
ceiling before querying Function 177. The production manager temporarily moves
its own control frame while an overlay is active; restoring through XSUB's
replacement stack did not preserve the CCP return path on z80pack. After a
successful load, XSUB also issued another Function 177 query before warm-boot
reconstruction. That call entered the newly committed BATCHIO provider before
its prepared live-chain link had been reconstructed.

XSUB now preserves the CCP stack, performs the idempotent query/load sequence,
and returns directly to the CCP after a successful load. The ordinary transient
return performs WBOOT reconstruction before BATCHIO can intercept a public
BDOS call. This is the same lifecycle already used by the general RSX utility.

## Focused diagnosis

A disposable z80pack overlay trace recorded the public request address, entry
stack, and all 18 Function 177 request bytes. It established that:

- `RSX LOAD BATCHIO` entered once with operation 1 and succeeded;
- the original XSUB entered with operation 3 but could not safely resume;
- preserving the caller stack allowed both operations 3 and 1 to complete;
- the following pre-reconstruction query then entered the fresh BATCHIO chain
  before reaching the manager; and
- removing that query and returning through the CCP produced a reconstructed,
  active provider.

No Function 177 transaction or BATCHIO carrier change was required.

## Automated evidence

`tools/test_z80pack_submit_xsub.py` uses separate private disk copies and
verifies:

- ordered SUBMIT execution;
- `$1` substitution and `$$` quoting;
- a final source line without CR;
- deletion of exhausted `$$$.SUB` files;
- XSUB installation through Function 177;
- submitted Function 10 input through BATCHIO; and
- continuation with a later submitted command.

The test removes two unrelated diagnostic utilities from each private image to
make directory entries for its fixtures. The R3 transaction overlays remain on
disk because they are required implementation components of Function 177.
Maximum-TPA overwrite and failure cleanup remain covered by the existing
TRS-80 `tools/test_submit_xsub.py` campaign.

## Acceptance

- Clean z80pack image construction passes.
- The focused z80pack SUBMIT/XSUB campaign passes.
- The ordinary z80pack boot/file/RSX campaign passes.
- The established TRS-80 SUBMIT/XSUB campaign remains the required companion
  regression. A fresh run of the corrected image was blocked on the current
  host because trs80gp 2.5.8 aborted in macOS application registration before
  emulator startup; it produced no BetterCP/M result.
- The default 53 KiB TPA contract is unchanged.
