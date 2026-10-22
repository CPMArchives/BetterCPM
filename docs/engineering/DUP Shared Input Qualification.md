# DUP shared input qualification

2026-10-22 — DUP 1.0 Build 005

## Change and memory cost

FORMAT and COPY approval now call `DP_ASK`, an entry into the same
`ui/confirm.inc` one-key adapter used by SYSGEN. Original questions remain at
their existing sites. Only Y/y authorizes; every other response declines.
No default, invalid-key retry, extra display or typeahead flush is introduced.
Menu/drive selection, operation gates, verification and cleanup are unchanged.

The complete shared binding is 220 bytes: 185 shared controller bytes, 28 adapter
code bytes, two choice-list bytes and five controller-state bytes. No text
editor, word module, field controller or formatting buffer is linked. DUP is
8,483 bytes (220 more than Build 004), SHA-256
`2fe64362672daea9e72b9ac34b5032cddd5a126f889b4c4fc1fd46d138016331`.
The binary remains below its private stack; existing copy buffers and 51K TPA
requirement are unchanged. No resident allocation or BIOS/BDOS change.

Both build paths select the common adapter. Native ZSM4/LINK and cross assembly
match. Extracting the adapter preserves SYSGEN Build 006 byte-for-byte at
`6b639c4ab99bbbc138f15a770099d5de1d1845003918bae1162b51c4cabb06ba`;
its native build and confirmation campaign pass again.

## Compiled checks

DUP and SYSGEN share the same safety campaign. Each passes all 255 nonzero key
bytes, with exactly one key consumed and trailing input preserved despite
hostile BDOS register clobbering. Three malformed-controller configurations fail
closed without reading a key. Six scoped /VER cases establish pure standalone
identity and invalid-combination rejection. Editor/field symbols are absent.
DUP's existing parser, direct-engine dispatch, one-shot exit and /VER checks pass.

## Actual cpmsim

The live command-line campaign passes FORMAT/COPY refusal without media changes,
physical boot-drive protection, confirmed copy with exact raw-payload equality,
verification and read-only CHECK. A separate direct FORMAT campaign passes
complete erased-image and verified-track checks. These use current DUP injected
into private copies; the initial partial fixture omitted DISK.FDB, and supplied
the normal generated catalog before the complete passing runs. No source
reference or daily emulator disk was edited.

The new native builder initially omitted expansion of the existing console
binding. That build-helper issue was corrected; the final parity check passes.
It did not require a utility or OS behavior change.

## Native Model 4

Native refusal, FORMAT, COPY and CRC-error campaigns use a private full System
Disk with current DUP substituted. Each retains its own invocation, VRAM captures,
raw fixtures, file audit and filesystem check. Reference-file payloads are
independently checked and the source fixture's hash must remain unchanged.
The harness unloads monitor/backend providers in dependency order and records a
53K TPA witness before launching DUP; the existing 51K requirement is retained.

These are focused changed-utility regressions on disposable media, not another
complete release-distribution or core-OS acceptance run. Patterned B/C raw media
are deliberately not treated as valid CP/M filesystems.


## Final native results

All four groups pass:

- Decline: protected boot drive, refused FORMAT/COPY, unchanged B/C images,
  restored binding and normal return.
- FORMAT: interactive confirmation, all 160 surfaces and 1,600 sector IDs,
  sizes, header/data CRCs and erased payloads independently verified; subsequent
  direct CHECK reports zero unreadable sectors.
- COPY: direct confirmation, reformat of a mismatched destination, exact
  patterned payload over two cylinders/both sides including the reserved track,
  preserved later tracks/source, restored binding and clean CHECK.
- CRC failure: sector-3 read error prevents destination writes, preserves target
  and source, restores binding and reports exactly one unreadable sector.

All 29 original System Disk file payloads pass independent before/after audits;
filesystem checks pass and the reference DMK remains unchanged. The first decline
run's operational assertions passed, but its generated manifest used padded
record hashes for README.TXT instead of cpmtools' exact-byte length. Correcting
the fixture hashes and repeating the retained media/file audit resolved that
accounting mismatch; no emulator replay or product change was needed. Remaining
groups used the corrected exact-byte manifest and completed normally.
