# Compression Utilities Disk Platform Qualification

## Verdict

**Blocked by a recorded Model 4 data-integrity failure.** The final Build 004
commands execute from private Utilities B: beside normal BetterCP/M System A:.
The z80pack/cpmsim campaign passes all three pairs and 27 round trips. Model 4
CR/UNCR and LZH/UNLZH pass their respective nine-round-trip matrices. The Model 4
SQ/USQ campaign completes its 39 commands and seven regular round trips, but
fails preservation of pre-existing C: data. It does not qualify that pair or
close the six-command Model 4 release gate.

Two existing temporary sentinels, SQU00000.$$$ and USQ00000.$$$, are each read
back as 128 E5 bytes. The C: DEFAULT.TXT fixture and its A: restoration also
fail the expected payload comparison. The commands report completion; directory
and filesystem consistency checks alone do not detect these payload failures.
The seven original A: source fixtures, their restored regular outputs, saved
large-file source copy, shipped System payloads and reserved System area pass
independent readback. The cause and exact point of corruption are **not yet
established**. These observations do not establish whether a codec, file adapter,
OS disk layer, emulator, or test preparation is responsible.

The large Model 4 SQ case uses an identical C: source copy to avoid repeated
floppy-drive switches. After encoding, the test renames that copy SAVED.BIN and
restores BIG.BIN on C:, retaining both copies and the original A: input. Other
regular cases use A: input and C: output. Fixtures cover empty/binary data,
127/128/129-byte boundaries, a 17,001-byte extent crossing and a 70,001-byte
64-KiB crossing, padded to physical CP/M records. Default logged-drive and user-7
cases, collision refusals and controlled malformed/checksum cases are included.
A returned prompt or successful message is not sufficient for acceptance.

Both platforms capture complete extra-argument /HELP and /VER output for all
six commands and help precedence. The broader forgiving query implementation
is independently qualified in [Common Utility Query Qualification](Utility%20Query%20Qualification.md).
Historical interoperability also passes for these same final binaries.

## Evidence and remaining work

The [machine-readable record](Compression-Utilities-Platform-evidence.json) and
[console, VRAM and audit bundle](Compression-Utilities-Platform-evidence.tar.gz)
retain passing cases, the failed readbacks, exact executable/image identities,
actual runner snapshots and the independent failure-audit script. Earlier
incomplete pilots are not accepted results. Completed cases reused during the
campaign were checked against reconstructed seed disks and retained output and
capture hashes. Original distribution images were never mounted directly.

Investigate and reproduce the Model 4 corruption, correct its cause, then rerun
the affected matrix with unchanged-source and sentinel assertions enabled.
Clean pinned cpmsim reconstruction, native ZSM4 build qualification, remaining
Utilities selections and final whole-image acceptance remain separate open gates.
The packaged Utilities disk remains PROVISIONAL. Other utilities changed by the
shared /VER revision need relevant final-artifact component reacceptance; older
receipts retain their original binary/image scope.

## Reproduction

Build isolated System generations with tools/build_distribution.py --target all,
build all six compression commands into the z80pack artifacts tree, then run:

```sh
python3 tools/test_codec_utilities_platforms.py \
  --system /private/tmp/codec-system/release-GENERATION \
  --artifacts /private/tmp/codec-build/z80pack \
  --output /private/tmp/codec-platform-campaign
```

Use fresh disposable directories and disks. The harness requires cpmtools,
the existing local cpmsim and trs80gp prerequisites; it records exact emulator
hashes without claiming a clean pinned reconstruction. The failed Model 4
SQ case must remain a failure until payload preservation is demonstrated.
