# Pinned cpmsim reconstruction and compression requalification

## Verdict — 2026-10-24

**PASS.** The emulator reconstruction gate is closed for the recorded runtime
and ROM-qualification profiles. Compression Build 004 is requalified on the
reconstructed runtime. This does not close final release-media acceptance or
other utilities' pending component acceptance.

The [source lock and build procedure](../../third_party/z80pack/README.md) pin
upstream z80pack `91fd28eb04e675c2127df88ed3f40675e15282e2`, two runtime disk
patches and a separate qualification patch. The upstream commit was confirmed
in udo-munk/z80pack. Runtime geometry source exactly reproduces the code at the
maintainer's `b7a6fa36` checkout; its additional backend-notes commit and local
untracked files are not build inputs. ROM instrumentation is optional and
separate from the runtime requirements.

| Profile | cpmsim SHA-256 |
| --- | --- |
| runtime | `3a41c74a8e70562fefc9d4e6c0e532259bb82b83518f7bfc259230699fe82c05` |
| qualification | `61ad39b8be562505b66090ab4557a9335b0d90eb29c1498d6f8bd161e6e4046c` |

The [evidence index](CPMSIM-Reconstruction-evidence.json) and
[bundle](CPMSIM-Reconstruction-evidence.tar.gz) retain both environment
manifests, compiler logs, helper hashes, primitive outputs, integration
transcripts, media identities and compression receipts. Reconstruction tooling
was committed at `fce9a51` before the final environment builds and compression
runs. Harness corrections and the isolation test were committed at `6c274f2`
before the final interchange/XIP runs. The integration fixture source is merged
main `919aca2`; exact source and test identities remain distinguished.

## Bounded results

| Check | Result |
| --- | --- |
| Clean archive extraction, ordered patch application, C builds and helper builds | PASS, both profiles |
| Independent rebuild on this host | Identical executable hashes |
| Poisoned source/object files in a separate checkout | Ignored; pinned inputs and all rebuilt executable hashes identical |
| Runtime geometry port interface | Version 2 observed from executed Z80 code |
| ROM guard primitives | 7 pass: execution, CPU/DMA writes, guest unlock/boundary change, reset and unprotected mode |
| Ordinary BetterCP/M boot and Utilities B: compression execution | 86 commands, 27 round trips, all six tools pass |
| cpmtools → BetterCP/M → cpmtools interchange | 4 formats, byte-identical |
| Protected ROM integration | Cold boot, DIR, transient execution, CPX and RSX lifecycle, stack and workspace checks pass |
| Historical compression exchange on stock CP/M 2.2 | 178/178 cases meet expected outcomes: 148 decoded, 26 safe refusals, 3 historical skips, 1 known historical producer defect |
| Stock CP/M query tests | 90 commands pass |
| Native ZSM4 4.7 / LINK 1.3 on reconstructed cpmsim | All six outputs byte-identical to qualified Build 004 |

Compression uses the same qualified System image
`995368798bed5c3acc3d15b097c22e4b19213b134a60ca9e67ae0641ddc10dc9`
and Utilities image
`7e527f29a75cbd69c7af0dbe138f5674ebc4ea0cdda7d0bb86c314d2866497a1`.
The additional command relative to the prior 85-command cpmsim receipt is the
pre-execution DEFAULT.TXT readback. File preservation, checksum/malformed
refusal, temporary-file handling, drive defaults and user 7 all pass. No codec
binary changes or build-number changes occurred. Existing Model 4 evidence is
retained; this host-emulator reconstruction does not affect that platform.

## Integration fixture and harness corrections

The broad legacy development image overflowed the 332K filesystem even from
isolated source. This is separate from the selected Utilities disk, which fits
and passes above. For disk-interchange and ROM integration, the isolated source
build therefore used the existing Dictaphone 80T DS 692K FDF definition. It is
**test media**, not a change to release disk geometry or inventory. The legacy
builder still names those files with its fixed `332K` suffix; the retained
boot-format description, 737280-byte image lengths and SHA-256 identities
specify the actual geometry. Compression acceptance still uses the qualified
332K media.

The four interchange cases are MM Standard SYSTEM, MM 80T DS DATA, Ampro Little
Board 40T SS and 40T DS. The old test used obsolete CONFIG menu letters. It now
uses documented `/PHYSICAL` and `/LOGICAL ... /FORMAT` commands and independently
compares host and guest file bytes. No guest behavior changed.

The ROM harness expected 44 reloader relocations; current source has 45 because
`CALL LY_BIOS+66` resets unfinished monitor output before reconstruction. The
retained relocation record identifies that reference. The count was corrected,
and an Expect timeout handler was moved after process creation so it monitors
the emulator rather than the caller's stdin. Protected execution then passed.

The old ROM patch was a concatenation containing zero-context incremental
hunks. The first `git apply` trial misplaced those additions and failed C
compilation. The authoritative patch was regenerated as one contextual diff
from the established `patch -p1` result. No ROM-guard behavior was redesigned.
Failure logs are retained alongside successful results.

## Reproduction and release boundary

First run the two reconstruction commands and isolation/primitive test in the
[pinned build instructions](../../third_party/z80pack/README.md). Use new private
output directories. For the recorded compression images and fixtures:

```sh
python3 tools/test_codec_utilities_platforms.py --only z80pack \
  --simulator RUNTIME/z80pack/cpmsim/cpmsim \
  --system SYSTEM_GENERATION --artifacts ARTIFACT_ROOT --output NEW_PLATFORM
python3 tools/test_codec_historical_cpm.py --z80pack RUNTIME/z80pack \
  --commands-dir ARTIFACT_ROOT/build/utilities --corpus HISTORICAL_CORPUS \
  --output NEW_HISTORICAL
python3 tools/test_codec_versions_cpm.py --z80pack RUNTIME/z80pack
python3 tools/qualify_codec_native.py --cpmsim RUNTIME/z80pack/cpmsim/cpmsim \
  --output NEW_NATIVE
python3 tools/test_z80pack_interchange.py --image-dir INTEGRATION_IMAGES \
  --simulator RUNTIME/z80pack/cpmsim/cpmsim
python3 tools/test_z80pack_rom_xip.py --image-dir INTEGRATION_IMAGES \
  --simulator QUALIFICATION/z80pack/cpmsim/cpmsim
```

The clean integration source was exported with `git archive 919aca2`; bootstrap
BOOT/STAGE1, `build_rsxselect.py` and `build_complete_system.py` establish the
existing clean-build prerequisites before `build_z80pack_image.py --format
'Dictaphone 6000 CP/M Rev. A (80T, DS, DD, 692K)'`. Logs and media hashes are retained.

The compression platform harness's generic note says reconstruction is a
separate gate; this record closes that separate gate by binding its exact
emulator hash to the reconstruction manifests. No earlier receipt is relabelled.
Final Utilities membership, all-component acceptance, other utilities affected
by shared query changes, final target media and complete release hash/evidence
closure remain open. Future changes to emulator source/options, guest binaries
or final media require the relevant reacceptance.
