# Utilities ZSM4/LINK packaging and qualification

## Selected tools and redistribution

The Utilities disk adds the unmodified native ZSM4 4.7 and Digital Research
LINK 1.3 binaries already used by compression native qualification. These
third-party tools retain their original command syntax and identities; they
are not assigned BetterCP/M utility build numbers or patched with /VER or /HELP.

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| ZSM4.COM | 22400 | `3dbeed62bc303a07c62e0fd41a5df44d023c2f82c05b76785a97d20a633f6ef8` |
| LINK.COM | 15616 | `82df88a9bcfb1068eb37df08df6d664711d20c73ddae66b81577dfed02642677` |

ZSM4 is taken directly from Hector Peraza's repository at revision
`96a9ac1081172e1c08291521b77d2a715ec59c8b`, `bin/zsm4.com`. The official
repository was freshly cloned and its binary compared with the existing
compatibility-suite tool. The source declares GPL version 2 or later; prior
copyright and contribution notices remain intact. The upstream README's older
4.6 heading is not used to identify the executable: the source ident is ZSM4.7
and the executed binary reports V4.7. The full pinned git archive, including
original Makefile, includes, libraries, documentation, tests and license, is
retained as [source.tar.gz](../../third_party/zsm4/source.tar.gz).

LINK is independently extracted as `0:LINK.COM` with raw `z80pack-hd` geometry
from `cpmsim/disks/library/hd-tools.dsk` in z80pack revision
`b7a6fa36a2ee185a73727dc5b56ac1af40679e81`. It matches the compatibility-suite
copy byte for byte. That suite was read at revision
`a9a878fcd2e36698c7e856654a85847a004fdd20`; neither user's checkout was modified.
The binary's native banner identifies LINK 1.3 and its retained copyright is
Digital Research 1980. Distribution follows the existing CP/M grant and its
July 7, 2022 clarification, published on the archive page updated July 9.
The grant names CP/M and derivatives: applying it to this DRI CP/M development
utility is the recorded redistribution basis, not a claim of a separate
LINK-specific grant or LINK source release. The original page and complete
permission text are retained. HTTP retrieval succeeded; HTTPS failed certificate
verification and that failure was not bypassed.

See the exact [ZSM4 provenance](../../third_party/zsm4/provenance.json) and
[LINK provenance](../../third_party/dri-link/provenance.json), including archive,
source, license and binary hashes. These works are not relicensed under the
license of BetterCP/M's original code.

## Package contents

Both target disks now contain 15 user-0 files: the previous ten qualified
components, ZSM4.COM, LINK.COM, TOOLINFO.TXT, ZSM4COPY.TXT and LINKCOPY.TXT.
The three text files record usage, ownership and complete license/permission
texts. They are CRLF ASCII with CP/M EOF markers. This settles these tools'
notices only; general on-disk manuals and build-material placement remain open.

The Utilities output directory also contains:

- ZSM4-SOURCE.tar.gz — complete corresponding source, original build scripts,
  documentation and license, supplied with the executables under GPL section 3a.
- Toolchain-Provenance.json — exact upstream and compatibility-suite records.
- LINK-Permission.html — the retained CP/M archive permission page.
- TOOLCHAIN-README.txt — redistribution companion instructions.

`BetterCPM-Utilities-package.zip` contains both images/reports, these four
companions and `Utilities-SHA256SUMS.txt`. All nine ZIP members and their
checksums are verified; repeated builds produce byte-identical ZIP archives.

Distribute this complete package. A disk image separated from its source
companion is not the complete toolchain distribution. The builder validates
binary, archive and permission hashes, embedded source binary/license identity,
required source files and on-disk license text before publishing. Reports bind
all companion hashes. `--toolchain-acceptance REPORT` additionally binds a
passing seven-case campaign per platform, the post-run System audits, both tool
hashes, both image hashes and the source companions. Component PASS rows name
the paired System hash; stale or incomplete evidence is refused. Rebuilding with identical inputs produces identical
images, reports and companion files; no toolchain download is needed at build time.

The independent FDF audit verifies all 15 names, user placement, exact payloads,
record padding, allocation bounds/crosslinks, and native DMK/raw conversion.
Free space is 69 allocation blocks (138 KiB) for cpmsim and 302 blocks (604 KiB)
for Model 4. Filesystem checks pass. The ten prior component binaries are
unchanged; their older receipts retain their original media identities.

## Execution procedure

Run the packaged tools from Utilities B: beside the recorded System A:, with
sources and outputs on a private writable A:. Model 4 uses its normal M4SCRN /
ADM3A pair; cpmsim uses the reconstructed pinned runtime. The qualification
runner creates isolated media for each case and never modifies source images.

The probe covers Z80 IX/displacement instructions, a macro in an included file,
two independently assembled REL modules, external symbol resolution, code/data
relocation and execution through BDOS. It verifies both MODULE OK and
TOOLCHAIN OK. Separate invalid-operand and unresolved-external cases require
explicit diagnostics; returning to SUBMIT is not interpreted as success. LINK
can write a COM even when externals are unresolved; that COM is never executed.

All six compression commands are also assembled and linked through the existing
prepared-source procedure. Their complete executable bytes and LINK code sizes
must match the qualified Build 004 commands, with only verified final-record
1Ah padding excluded. Native ZSM4 executes the macros/includes itself; host
preparation does not expand them. See the earlier
[compression native procedure](Compression%20Native%20Build%20Qualification.md).

Physical Enter gates hold native result screens until captured. The evidence
retains the earlier syntax pilot (missing explicit output=input), the original
ungated native attempt, and the corrected campaigns. Neither pilot is counted
as a completed qualification campaign. Native gates address screen-capture
races; no production instructions or tool binaries were changed.

Commands, fixture/prepared-source hashes, emulator and media identities,
console/text captures, native outputs, input preservation and filesystem checks
are retained. A separate audit checks all shipped System file payloads after
each case, except the explicitly replaced native STARTUP.SUB, and checks batch
queue cleanup. This is emulator-platform component qualification; physical
hardware and the remaining whole-release gates are not certified here.

## Reproduction

```sh
python3 tools/build_utilities_disk.py --build --output NEW_IMAGES
python3 tools/test_toolchain_distribution.py
python3 tools/test_utilities_inventory.py --artifacts ARTIFACT_TREE \
  --images NEW_IMAGES --output INVENTORY.json
python3 tools/qualify_utilities_toolchain.py --system SYSTEM_GENERATION \
  --utilities NEW_IMAGES --artifacts ARTIFACT_TREE --output NEW_CAMPAIGN \
  --simulator PINNED_CPMSIM
python3 tools/audit_utilities_toolchain.py --system SYSTEM_GENERATION \
  --campaign NEW_CAMPAIGN
```

The output/campaign directories must be new for qualification. The System
reference is the exact two-platform generation from utility reacceptance;
qualification does not transfer automatically to changed System or Utilities
images. Final editor/disassembler selection, general documentation placement,
complete Utilities acceptance and frozen-release evidence closure remain open.
