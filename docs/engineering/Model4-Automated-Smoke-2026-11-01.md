# Model 4 automated release smoke checks — 2026-11-01

The maintainer launched automated trs80gp runs from normal Terminal. The agent
inspected their captures and independently exported and compared file bytes.
Historical blocked attempts and manual results are unchanged. This is bounded
smoke coverage, not a pass for every assertion in the full qualification ledger.

| Check | Result | Evidence |
| --- | --- | --- |
| PATCH valid patch | PASS | 128 output bytes compared in full; input unchanged |
| PATCH expected-byte mismatch | PASS | Rejected; existing destination and input fixtures unchanged |
| DSYM valid complete LINK report | PASS | Two canonical symbols independently exported and compared |

PATCH run: `/Users/nathanael/Downloads/model4-release-smoke-20261101-212156`.
DSYM run: `/Users/nathanael/Downloads/model4-dsym-20261101-213042`.

The original combined runner failed on a host padding assumption. Its later
DSYM fixture was corrected to include CP/M text termination. The final DSYM run
printed successful conversion but the host exporter looked on D:; DSYM defaults
to the current drive and wrote A0:SAMPLE.DSY. Inspection of the private A: image
confirmed the expected output. No emulator rerun was needed to establish that
result. The runner now supplies an explicit D: destination and compares
preservation against actual pre-run exports. These were harness corrections;
no guest binaries were changed. Earlier failed runs are not relabeled wholesale.

The B: and C: images were unchanged in both verified runs. Source release images
were preserved in the DSYM run. Full receipts are retained under
`build/model4-patch-verified-20261101` and
`build/model4-dsym-verified-20261101`.

## Tested image identities

The following SHA-256 values identify the actual copied inputs, which can
include guest changes since initial package extraction. They do not imply
byte identity with pristine candidate archives.

### PATCH run

- `BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`: `0dfc373897a3952ee7c934011afe5ead6314c0de066a64b846521dcec229cb35`
- `BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk`: `a67dfb84a8709b3f6c21d38036ba47486630b4481c5550ee14905f8d5649d854`
- `BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk`: `be7827c7cae78d1c33e80eed952ea7466889403eeb9de28a3287affe56bceb2f`
- `BetterCPM-Work-800K.dmk`: `a2bd8239531919ae078c6d2dcef650738ec77e8307993df8d3fcd74a46c29107`
### DSYM run

- `BetterCPM-Distribution-trs80gp-80T-DS-System.dmk`: `0dfc373897a3952ee7c934011afe5ead6314c0de066a64b846521dcec229cb35`
- `BetterCPM-Utilities-trs80gp-80T-DS-800K.dmk`: `a67dfb84a8709b3f6c21d38036ba47486630b4481c5550ee14905f8d5649d854`
- `BetterCPM-NOAH-trs80gp-80T-DS-800K.dmk`: `be7827c7cae78d1c33e80eed952ea7466889403eeb9de28a3287affe56bceb2f`
- `BetterCPM-Work-800K.dmk`: `a2bd8239531919ae078c6d2dcef650738ec77e8307993df8d3fcd74a46c29107`

DSYM exported output SHA-256: `3234b80b22ecd62c89a114620bba66982b88b0381e4391f29b80b6b05113b948`.

## Presentation smoke run

Run: `/Users/nathanael/Downloads/model4-presentation-20261101-213818`.
The runner reported `PASS_TEXT_CHECKS` for all five cases. The agent inspected
the text and GIF captures. These checks used the same A:, B:, and C: hashes
listed above; D: was a freshly generated blank work image. Captures and the
full receipt are retained in `build/model4-presentation-reviewed-20261101`.

| Component | Check | Result |
| --- | --- | --- |
| DIR 011-dev | Empty D: listing | PASS: `D0: NO FILE` followed immediately by `---- 796K FREE ----` |
| CRCKSUM 008-dev | `/40` grouped table | PASS: complete header/rule/value groups; checksum columns start at zero-based positions 19 and 29 |
| COPY 009-dev | `/HELP` | PASS: usage and documented options displayed in text and raster capture |
| COMPARE 003-dev | `/VER /HELP /BOGUS` | PASS text/help precedence; raster review unresolved |
| NOAH 020 | `/HELP` | PASS text, including `/L`, `/A`, `/QUIET`, `/H`; raster review unresolved |

The COMPARE GIF omits the `/HELP` and `/VER` labels and the returned prompt;
the NOAH GIF omits `/VER` and the prompt. All are present in the corresponding
raw screen-memory captures. This discrepancy is not yet attributed to either
the screenshot mechanism or guest rendering. Do not treat these two raster
checks as passed, or infer a guest defect solely from the discrepancy.

### Repeated capture review — resolved

Follow-up run: `/Users/nathanael/Downloads/model4-capture-review-20261101-215408`.
Both cases passed text checks. For each case, all three raw screen-memory
captures are byte-identical. COMPARE's final GIF shows both `/HELP` and `/VER`
and the returned prompt. NOAH's middle GIF shows `/H /HELP`, `/VER`, and the
returned prompt; its other GIFs omit some of those pixels despite unchanged
screen memory. This resolves the earlier uncertainty as a raster capture
artifact rather than missing help output. Both bounded help-screen visual
checks now PASS. No guest binary changed. Receipts and captures are retained
in `build/model4-capture-reviewed-20261101`. Image identities are recorded
in the run receipt and match the presentation smoke inputs above.

### NOAH operation setup correction

Run `/Users/nathanael/Downloads/model4-noah-output-20261101-220239`
failed before archive processing: `NOAH.OVL unavailable or invalid; operation stopped.`
The runner incorrectly invoked C:NOAH from A0:. The documented overlay lookup
uses the invocation DU, then A0:, requiring the operator to log onto C0: first.
The runner now switches to C:, waits for C0>, then invokes NOAH. This is a
harness error, not an established NOAH defect; normal-operation output remains
pending a corrected run. Original receipt retained in
`build/model4-noah-output-blocked-20261101/result.json`.

### NOAH 020 normal-operation output — PASS

Corrected run: `/Users/nathanael/Downloads/model4-noah-output-20261101-220755`.
Command after logging onto C0:: `NOAH /ADD D:SMOKE.LBR A:STARTUP.SUB`.
Text and raster captures show:

```text
A0:STARTUP.SUB
NOAH: LBR update verified and published.
1 file added.

C0>
```

The agent inspected both captures. PASS for bounded normal-operation output
smoke coverage: concise output, single operation count, and return to C0>.
This is not an independent archive-byte verification or coverage of every
NOAH operation. Tested A:/B:/C: hashes match the prior smoke inputs; originals
and private B:/C: were preserved by the runner. Receipt and captures are in
`build/model4-noah-output-reviewed-20261101`. This completes execution of the
maintainer's reduced runtime smoke scope; final artifact identity, installation,
conformance and release acceptance remain separate work.

## Repository evidence bundle

Receipts, captured text/screens and small verified exports are preserved in
[evidence/2026-11-01-model4-smoke/receipts-and-captures.tar.gz](evidence/2026-11-01-model4-smoke/receipts-and-captures.tar.gz),
with an adjacent SHA256SUMS.txt. Full disk images and raw intermediates remain
local; their hashes and original run locations are recorded in the receipts.
