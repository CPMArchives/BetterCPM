# SYSGEN destination input qualification

2026-10-22 — SYSGEN 1.0 Build 007

## Implementation and preserved policy

`SG_DRIVE` reuses the already-linked shared choice controller. The interactive
caller still prints the original header/question, accepts B..D with KEY's ASCII
case folding, exits on Ctrl-C, and repeats the heading for all other keys.
Command-line parsing and selection do not call this adapter. Disk operations,
installation/export recovery and approval wording are unchanged.

Unknown keys use an internal `?` member while their original returned byte is
retained for caller dispatch. Every selection return restores the Y/N list,
count and zero default before later approvals. A malformed selection aborts
without reading input or reusing a stale drive. `SG_ASK` only selects approval
mode; it deliberately does not repair malformed approval configuration.

The binary is 5,818 bytes, SHA-256
`94bf2aa3f122eaed1f49f2cfe0cb9703985a98a2bcc5644e859f193bc9cd6088`.
This adds 84 transient bytes over Build 006, including six adapter data bytes.
No second controller/editor/buffer or resident storage is added. Existing stack,
payload workspace and 36K TPA guard remain intact. Native ZSM4/LINK output is
byte-identical to the cross build.

## Evidence

- `tools/test_sysgen_shared_destination.py`: all 256 first key bytes compared
  against unchanged KEY, including zero polling, case folding, control bytes,
  exactly consumed/preserved input, balanced stack and hostile BDOS registers.
  Six alternating destination/approval cases confirm context isolation; one
  corrupt selection verifies fail-closed behavior followed by safe approval.
  Report: `build/utilities/sysgen-shared-destination.json`.
- `tools/test_sysgen_shared_choice.py`: 255 nonzero approval bytes, three
  malformed approval configurations and six version/usage cases pass.
  Report: `build/utilities/sysgen-shared-choice.json`.
- `tools/test_sysgen_command_line.py`: 32 valid/invalid command tails preserve
  source-loader dispatch and reject malformed tails before source I/O.
- `tools/build_native_sysgen.py`: 5,818 byte-identical bytes.
- `tools/test_sysgen_destination_media.py`: cpmsim and native Model 4 each
  redisplay the original question after A, E, CR and ESC, and return to the CCP
  on Ctrl-C. Every mounted disk image remains byte-for-byte unchanged.
  Reports: `/private/tmp/bcpm-sysgen-destination-cpmsim/result.json` and
  `/private/tmp/bcpm-sysgen-destination-model4-final/result.json`.
  The Model 4 report includes six VRAM captures. Its ESC is a physical CLEAR
  matrix stroke; the initial harness setup stopped before launching because
  the generic key helper cannot encode ASCII ESC. Only the corrected completed
  run is counted as passed.

The media campaign covers invalid selection and exit; successful selected-key
compatibility is covered by the compiled exhaustive comparison. It does not
claim a new destructive installation/export qualification campaign, since those
engines are unchanged.
