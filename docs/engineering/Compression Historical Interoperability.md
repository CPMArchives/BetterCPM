# Compression Utilities — Historical Interoperability Qualification

## Verdict and scope

**PASS for the supported-format exchange matrix**, qualified 2026-10-23 on
stock z80pack 62K CP/M 2.2 with a Z80 CPU, user area zero and disposable
IBM-3740 disks. The final version 1.0 Build 004 binaries are feature-frozen; no production
codec or file-policy corrections were needed for this rerun. The requested
forgiving-query amendment changes startup handling and identification only.

The campaign ran **178 cases and 340 CP/M command invocations**. Counts are:
148 successful decoded-file comparisons, 26 intentional unsafe-name refusals,
three historical empty-input skips, and one independently confirmed historical
encoder defect. A passing guard/limitation case is not counted as a successful
file exchange. The historical control pairs add 52 byte-for-byte comparisons.

Evidence: [machine-readable results](Compression-Historical-Interop-evidence.json)
and [178 console transcripts, run log, query logs and test-source snapshots](Compression-Historical-Interop-evidence.tar.gz).
The transcript bundle SHA-256 is `9c5428622097536378a81461dc24c19647444e59694786884f5049606029c796`. The JSON binds historical
and current command hashes, input/output hashes, simulator and boot-template
hashes, test source and per-case console hashes. This report qualifies those
artifacts, not every historical executable sharing a version number.

The six final COM files were read from `build/utilities/` and required to match
fresh builds byte for byte before any campaign command ran (`--commands-dir`).
Their feature baseline is `00e6785`, merged as `569825d`; each identifies as
version 1.0 Build 004 after the forgiving query amendment. This evidence supersedes the pre-`/VER` command-baseline
run retained in Git history (`aa7b9b9`). The report now also pins the shared
includes, all codec sources, builders, identity/help generation, utility
metadata and assembler, alongside the runner's own hash. A source revision
alone does not identify local test-tool changes; these hashes do.

The historical programs execute directly, without patching, rebuilding or
substituting our implementations. Only filenames on disposable disks are
aliased to `HENC`, `CTRL` or `HDEC` to avoid collision with our programs.

## Frozen 1.0 artifact identities

| Command | Version/build | COM bytes | SHA-256 |
| --- | --- | ---: | --- |
| SQ | 1.0 / 004 | 8035 | `2517bf6d77631f6f6408a4b2bb7dcca769ae59a7ab0931b4dfe3ffdb2163335d` |
| USQ | 1.0 / 004 | 5310 | `25fdd2e566cc241a6f7b5623fc4a075a4c1843e45091309315de5bfa7fc247a0` |
| CR | 1.0 / 004 | 29355 | `8a089b84239004602dfd9ad0c4586c5c94ad73b9f257553521e6004569e381a3` |
| UNCR | 1.0 / 004 | 31118 | `e77200e4a8c36d3e7d455eeaed96c289a06e82a4756f29023a7850374e760be3` |
| LZH | 1.0 / 004 | 17137 | `36eff2d7dfa413ce18699d31291107c588fa84deabf957c7b9c27ec033c45eef` |
| UNLZH | 1.0 / 004 | 12127 | `2f21b8e6c81766c407cccdfb08029d39753f40fad4c43ee47050de9b6cd2e89a` |

The [1.0 qualification index](Compression-1.0-Qualification.json) binds these
artifacts, report and transcript bundle hashes and the outstanding release
gates. The refreshed query campaign passes 356 full-Z80 cases and 90 stock
CP/M 2.2 command invocations, including complete identities/help screens,
bounded and mixed arguments, no file access, state preservation and prompt
return. Its logs and test sources are included in the bundle. Final COM files are required to match fresh builds before campaign execution.

Separate BetterCP/M two-platform and [native ZSM4/LINK qualification](Compression%20Native%20Build%20Qualification.md)
now pass for these same executable bytes. The [pinned emulator campaign](CPMSIM%20Reconstruction%20Qualification.md)
repeats all 178 historical cases successfully. Remaining final Utilities disk checks
are open in the [1.0 release checklist](../releases/1.0-ROADMAP.md#compression-utilities--10-feature-freeze-and-release-checklist).
Stock CP/M 2.2 qualification does not close those gates. Any changed executable
requires refreshed relevant evidence before release; identical rebuilds retain
these exact hash identities.

## Exchange matrix

Each generated-input row uses 14 fixtures. Historical producer rows also run a
historical decoder as a control before our decoder.

| Producer | Consumer | Successful exchanges | Other checked results |
| --- | --- | ---: | --- |
| SQ 1.7 | BetterCP/M USQ | 14 | None |
| BetterCP/M SQ | USQ 2.0 | 14 | None |
| BetterCP/M SQ | USQ120 | 14 | None |
| CRUNCH 2.4 | BetterCP/M UNCR | 12 | Empty skipped; leading-DLE producer defect rejected |
| BetterCP/M CR | UNCR 2.4 | 14 | None |
| CrLZH 1.1 | BetterCP/M UNLZH | 13 | Empty skipped |
| CrLZH 2.0 | BetterCP/M UNLZH | 13 | Empty skipped |
| BetterCP/M LZH | UCRLZH 2.0 | 14 | None |

The 14 inputs are empty, one-byte/short-extension, binary control bytes,
extensionless, 127/128/129-byte boundaries, all 256 byte values, long DLE and
ordinary runs, a leading-DLE run, text, a 17,001-byte extent-crossing file,
a 70,001-byte file and a ring-wrap/repeated-block file. Input is explicitly
padded to CP/M records with 1Ah before import. Comparisons preserve every record
byte; they do not infer a host byte length from a text EOF marker.

For every successful generated exchange, an independent host decoder verifies
the actual encoded bytes and original checksum, and the CP/M-produced decoded
file is compared byte for byte with the physical-record input. Every imported
program and input file is read back after execution to verify it was unchanged.
Our generated compressed files also have their final 1Ah record padding checked.
The code-level reconstruction/width/reset campaigns remain separate evidence;
this command matrix is not a claim that every internal transition occurs in each
historical implementation.

## Preserved historical files

| Original corpus | Native CP/M results |
| --- | --- |
| `sq111.lbr`: `SQ111.DQC` | Our USQ, historical USQ 2.0 and USQ120 independently restore identical `SQ111.DOC` records (3456 bytes). |
| `usqfst20.lbr`: `UF20.MQC` | All three restore identical `UF20.MAC` records (38400 bytes). |
| Compatibility-suite CRUNCH 2.4 corpus | Our UNCR restores all 13 members; manifest compressed and original-source hashes are checked. |
| `crlzh11.lbr` | Our UNLZH restores 7 members; safely refuses 14 unsafe embedded names. |
| `crlzh20.lbr` | Our UNLZH restores 14 members; safely refuses 12 unsafe embedded names. |

The squeezed members are extracted as their exact allocated archive records.
Their padding is not assumed to match our encoder's padding, and neither the
file nor its header is rewritten for acceptance. Host tree/RLE interpretation
checks the stored checksum; agreement between two historical decoder executables
and ours supplies an additional independent check.

All 47 CrLZH members are also decoded successfully by the current assembled
UNLZH **library** campaign (`tools/test_unlzh.py`: 217 cases, 15,670 calls,
12 synthetic reconstructions). The standalone command's 26 refusals are its
existing filename policy, principally high-bit characters in filename slots;
metadata outside those slots is ignored. The command does not strip high bits
or publish a sanitized alternative name. These refusals remain a documented
compatibility limit rather than being described as successful extraction.

## Historical findings and controls

### CRUNCH 2.4 leading-DLE encoder defect

The pinned GEL-labelled CRUNCH 2.4 executable produces a malformed stream for
the fixture beginning with 2048 `90h` bytes, followed by 18,000 `A` bytes and
normal record padding. Its decoded RLE token prefix is `90 90 00 90 00 ...`.
The first DLE is unescaped, so the next `90h` is interpreted as a repeat count
without any preceding ordinary history byte. Source inspection of its initial
lookahead/STATE0 path supports this diagnosis.

The unmodified historical UNCR 2.4 control prints `Checksum error detected.`
and produces bytes different from the original. Our UNCR reports `invalid or
truncated crunched file` and leaves no final output. The host model rejects
`invalid repeat` as well. This is recorded as `HISTORICAL_ENCODER_DEFECT`, not as
a successful decode or an outstanding defect in our UNCR. The campaign retains
this vector explicitly; it has not been silently replaced by a passing input.
A second run fixture beginning with an ordinary `R` before the DLE run succeeds
through the historical control and our decoder. Our CR output for the leading-DLE
input succeeds through historical UNCR, confirming the reverse direction too.

### Empty files and expanded output

CRUNCH 2.4, CrLZH 1.1 and CrLZH 2.0 skip the zero-record source without creating
a compressed file. Each is an explicitly verified `HISTORICAL_SKIP`; there is
nothing to feed to our decoder in that direction. Our encoded empty files do
restore correctly with the historical decoders, including both historical USQs.

For CRUNCH/CrLZH generated files, the historical encoder runs on the source DU
so expanded output can be retained through its own save-anyway prompt. The
harness answers Y only to that prompt on disposable media. It does not patch
an installation flag or mistake the program's uncompressed copy fallback for
a successful compressed result. Each result must have the correct format and
checksum. SQ 1.7 uses its documented output-drive-first syntax. The known SQ 1.7
BDS C drive/user-prefix bug is avoided by plain source operands; support for
those old operand bugs is not part of this format qualification.

## Reproduction

Prerequisites: host Python 3, C compiler only for the separate library test,
`z80asm`, z80pack `cpmsim` plus its stock `cpm22-62khd.dsk`, cpmtools and expect.
The default assembler and z80pack paths match the other codec tests; override
`--assembler` and `--z80pack` as necessary.

```sh
python3 tools/test_codec_historical_cpm.py --fetch \
  --commands-dir build/utilities \
  --corpus /path/to/cpm-2.2-compatibility-suite/suite/crunched-source \
  --archives /path/to/crlzh11.lbr /path/to/crlzh20.lbr
python3 tools/test_unlzh.py \
  --archives /path/to/crlzh11.lbr /path/to/crlzh20.lbr
```

`--fetch` downloads eight original executables and two SQ archives into ignored
`build/test-fixtures/historical-interop/`. Every artifact is size/SHA-256 checked
before execution. CRUNCH/UNCR downloads reproduce the compatibility-suite pins.
The CrLZH archives are supplied separately, with their existing SHA-256 pins in
`test_unlzh.py`. All upstream artifacts are from the preserved
[SQ/USQ archive](https://dflund.se/~pi/cpm/files/ftp.mayn.de/pub/cpm/archive/squsq/);
exact URLs and hashes appear in the test and JSON evidence. Fixtures are used
locally without adding historical binaries, source or license-restricted
packages to BetterCP/M's distribution.

`--commands-dir DIR` reads the six final COM files and rejects any difference
from freshly built source outputs before execution. Without it, the campaign
tests freshly built temporary commands. Final release qualification must select
the intended distributed files with this option.

`--only SQ`, `--only CR`, or `--only LZH` limits the family. `--match TEXT`
selects case names; an empty selection fails. `--skip-archived` runs the generated
matrix only. The default output is `build/historical-interop/report.json`, plus
console transcripts. Failure disks are retained there for diagnosis. Every case
uses newly copied/formatted temporary media; the user's emulator disks and
read-only corpora are never opened for writing. The report distinguishes
`DECODED`, `EXPECTED_REFUSAL`, `HISTORICAL_SKIP` and `HISTORICAL_ENCODER_DEFECT`.

## Limits and related specifications

This closes the initial real-executable interoperability gap, especially for
SQ/USQ. It does not certify all historical releases, malformed-input recovery,
non-additive check modes, CRUNCH 1.x, LHA archives, other OSes, nonzero user areas,
all physical platforms or relative speed/compression ratios. Disk images remain
subject to their own release acceptance. Keep the narrower library, fault-
injection and native round-trip regressions alongside this historical campaign.

- [Common ABI and file-handling specification](Compression%20Utilities%20Common%20Specification.md)
- [SQ/USQ specification](SQ-USQ%20Specification.md)
- [CR/UNCR specification](CR-UNCR%20Specification.md)
- [LZH/UNLZH specification](LZH-UNLZH%20Specification.md)
