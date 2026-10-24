# Compression native ZSM4 build qualification

## Verdict — 2026-10-24

**PASS for SQ, USQ, CR, UNCR, LZH and UNLZH 1.0 Build 004.**
ZSM4 4.7 and DRI LINK 1.3 executed under stock 62K CP/M 2.2 on the recorded
local cpmsim 1.39. All six native executables match the qualified cross builds
byte for byte. No instruction, library ABI, utility behavior or build number
changed. Source changes to the codec macros are qualification comments only.

| Command | Exact executable bytes | Result |
| --- | ---: | --- |
| SQ | 8035 | Identical |
| USQ | 5310 | Identical |
| CR | 29355 | Identical |
| UNCR | 31118 | Identical |
| LZH | 17137 | Identical |
| UNLZH | 12127 | Identical |

The [native report](Compression-Native-Build-evidence.json) records source,
prepared-input, tool, transcript and executable hashes. The
[evidence bundle](Compression-Native-Build-evidence.tar.gz) retains the runner,
input qualification snapshot, sources, prepared CP/M sources, native build
scripts/transcripts, raw linked COM files and exact-length binaries. The
[qualification index](Compression-1.0-Qualification.json) binds these receipts.

## Native procedure and source preparation

Run from the repository root, with cpmtools, Expect and the recorded native
tools available:

```sh
python3 tools/test_codec_native.py
python3 tools/qualify_codec_native.py --output /private/tmp/codec-native-NEW
```

The output directory must be new. The runner accepts explicit `--cpmsim`,
`--tools` and host `--assembler` paths. Each utility gets private CP/M disks:
A: is stock CP/M, B: contains includes and output, C: the command source and
D: ZSM4.COM/LINK.COM. The guest executes:

```text
B:
D:ZSM4 B:COMMAND=C:COMMAND
D:LINK COMMAND[A]
```

The host prepares source text, not assembled code. ZSM4 processes the INCLUDE
files, macro definitions and invocations, expressions and instructions itself.
The prepared inputs make these explicit dialect/storage adjustments:

- Replace the command's `ORG 100H` with `CSEG` and `.PHASE 100H`, ending with
  `.DEPHASE`, so LINK places the code at 0100h without an extra 256-byte gap.
- Spell each `DS` allocation as `REPT` / `DB 0FFH` / `ENDM`, preserving the
  cross assembler's exact reserved-storage bytes, including trailing workspace.
- Spell an empty help line as `DB 13,10`; ZSM4 emits an unwanted zero byte
  for the cross source's empty string operand in `DB '',13,10`.
- Use `CFIO.MAC` for the shared file adapter's CP/M 8.3 filename.
- Remove comments, blank lines and redundant whitespace outside quoted strings
  to fit the native macro-storage budget. Quoted text, including semicolons
  and spaces, is preserved. The initial SQ trial exhausted ZSM4 symbol/macro
  storage; compact preparation resolves it without expanding macros on the host.
- Write CRLF text with a CP/M EOF marker.

Every fresh cross build must first match the previously qualified executable
size and SHA-256. Native assembly must report zero errors, and LINK's declared
code size must equal that exact size. The entire executable byte range must
match; the only excluded bytes are verified 1Ah padding to the next 128-byte
CP/M file record. No byte repair, relocation patching or masking is applied.
The guard tests reject changed code, changed LINK size, missing size evidence,
short files, extra records and unexpected padding. All six guard cases pass.

## Scope and remaining release gates

This closes **native build qualification through the documented prepared-source
procedure**. It does not claim the unprepared host-dialect files can be copied
unchanged to ZSM4. The prior historical, query and BetterCP/M two-platform
receipts remain applicable to the exact matching executable bytes; no changed
binary requires a new functional campaign.

The [pinned cpmsim reconstruction](CPMSIM%20Reconstruction%20Qualification.md)
now passes and repeats native parity for all six executables. Final Utilities inventory/image acceptance, other utilities affected by
the shared version-query change, distribution placement of native-build
materials and final release hash/evidence closure also remain open. Utilities
media remain provisional. This is native CP/M tool execution under emulation,
not physical-hardware or whole-disk release acceptance.
