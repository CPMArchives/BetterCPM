# Utilities ZSM4/LINK packaging and qualification

## Qualification result — 2026-10-24

**ZSM4 and LINK component acceptance: PASS on both supported emulator platforms.**
The packaged tools run from Utilities B: on BetterCP/M System A:. Each platform
passes seven cases: the macro/include and multi-module execution/diagnostic
probe, plus native assembly/link parity for SQ, USQ, CR, UNCR, LZH and UNLZH.
Post-run audits preserve every shipped System payload except the deliberately
replaced native STARTUP.SUB, and verify batch queue cleanup.

The final paired System generation is `release-8864aa58ca7a-11ade544a462`.
These results include BDOS implementation 1.10's extent corrections; earlier
failed and exploratory runs are retained separately and do not count as PASS.
Compression runtime reacceptance also passes on the corrected paired Systems:
86 commands / 27 round trips on cpmsim and 88 commands / 27 round trips on
Model 4. These include 127/128/129-byte, 17,001-byte and 70,001-byte fixtures,
all six /HELP and /VER queries, collision and malformed/checksum refusal,
user 7, temporary-file preservation, filesystem and shipped-System payload
checks. All six compression binaries remain unchanged.

The whole Utilities disk remains provisional, and whole-System conformance,
live protected-XIP and final frozen-release acceptance remain open.

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
All 154 regular archive members match the pinned Git objects. The source/binary
association comes from that upstream tree; rebuilding ZSM4 itself from its
source is not part of this executable qualification.

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
DDT remains PENDING_RELEASE_ACCEPTANCE in these new image reports. DDT, DUMP,
XSUB and the complete selected inventory must be reaccepted on final media;
the earlier ten-file inventory proof is not transferred to this fifteen-file
package or the changed kernel.

## BDOS compatibility corrections found by qualification

The first Model 4 CR attempt assembled without errors but LINK reported
`NO FILE:` and left `XXPROG.$$$` at 16 KiB. Its 33,280-byte COMMAND.REL is
byte-identical to the successful cpmsim assembly (SHA-256
`51a2ef3724ed2a39cc9479ec9ba64ea2fb4bbc4308758d0d6e66d43cfef7af53`).
Repeating without screen modules did not resolve it; cpmsim also linked the
same object with its screen pair loaded. These checks rule out the proposed
screen-memory explanation.

A separate public Function 22 probe exposed a compatibility gap: EX=2 is a new
physical extent on both EXM=0 and EXM=1 formats. Stock CP/M 2.2 accepts Make;
previous BetterCP/M rejects it with FFh. Make now distinguishes EXM groups and
S2, admitting a new physical extent while retaining duplicate-extent rejection.
The emitted-code regression checks 225 combinations of 8/16-bit maps, groups,
S2, users and reused FCBs. Existing entries are preserved, new maps are cleared
and caller IX/SP are checked. The earlier EX=1 pilot used different grouping
masks and is retained as exploratory evidence, not used alone for comparison.
This correction alone did not resolve LINK; that failed retest is retained.

Tracing the actual LINK binary with the production BDOS and a controlled
logical-disk provider isolated the remaining failure. After writing record 127,
LINK closes its temporary file and explicitly opens extent 1. Stock CP/M has
already prepared that extent; BetterCP/M left it until the next write call.
On cpmsim's EXM=1 format, extent 1 shares the existing physical directory entry,
which hid the difference. Model 4's EXM=0 format requires another entry.

Sequential Write now prepares the following extent immediately after a
successful full write. Random Write and zero-fill Random Write continue through
the shared transfer core directly and retain their requested extent/CR position.
Stock probes verify the normal sequential boundary, random record 127, and
completion status when the directory is full. The existing failed-growth FCB
rollback convention remains: a failed next-extent preparation cannot change the
successful record's return status, and the next write can retry. This does not
claim identical stock FCB scratch fields in that failure case.

The regression rejects the original core and passes 36 sequential timing/status
cases plus 12 random position/status cases. Directory-full, allocation,
grouped-extent and error-recovery regressions also pass. The controlled native
layout runs actual LINK to completion and produces the exact 29,355 CR bytes;
the final physical-emulator campaigns test the same workflow on the real BIOS.

The public interface remains BDOS API 1.2; implementation identity advances to
1.10. Open and Make share the iterator's existing EXM comparison, retaining
Open's S2 filter. This removes redundant comparisons and fits the correction
in 3,436 bytes, including the unchanged 40-byte private stack. Focused
extent-full checks reach 32/40 bytes. Native ZSM4/LINK builds of both changed
units match the cross build: BDOS 3,436 bytes and extensions 425 bytes.

A register-equivalent zeroing sequence keeps the longer version string inside
the existing extension allocation; Function 178, empty/live Function 182, and
version-stack checks pass. Ownership anchors and ROM measurements are refreshed
from emitted binaries: all 790 packed references and 105 CONFIG overlay words
remain checked, with no unresolved or unexplained operands. The packed ROM has
509 bytes spare. RAM allocations and the TPA boundary are unchanged.

Fresh System images are used for the final campaigns. Prior System and ROM
execution receipts retain their original binary scope. Build-time ROM checks
and cold-initializer execution are not whole-System conformance or protected-XIP
release acceptance. These are correctness fixes, not new compression features.

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

The supplementary live-disk USQ pilot is not a passing decode receipt. Its
snapshot was copied after the original run created BIG.BIN; USQ correctly
reported an existing output, and the pilot's completion assertion failed.
The completed full campaign supplies the passing decode and file comparisons;
no command-entry loss or new decoder defect was established by this pilot.

## Evidence and exact media

[Machine-readable qualification](Utilities-Toolchain-Qualification.json),
[complete evidence archive](Utilities-Toolchain-Evidence.tar.gz) and
[record checksums](Utilities-Toolchain-SHA256SUMS.txt) retain the passing native
campaigns, executed runner sources, private work disks, System payload audits,
compression reacceptance, pinned source snapshots and diagnostic history.
The evidence archive contains the complete distributable ZIP under `package/`.
Its internal SHA256SUMS.json verifies every other archive member.

| Target | Paired System SHA-256 | Utilities SHA-256 |
| --- | --- | --- |
| cpmsim | `c6c07791f419321bc661a56d86ba9afc0e68242e8f0ff070e07188a7a5d7563e` | `457cd8660e1a74f04b23d4440c2eeb1595ba5f1543ef2650575ecfea551fbb1d` |
| Model 4 | `37fceca09cc404488e7b274e8a93c690b024767b225451295a742b87bc87d585` | `95f8af912173f428f47d434269da65d7778933410b30986d14c943a2285392c1` |

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
reference is a fresh two-platform generation containing both extent corrections;
qualification does not transfer automatically to changed System or Utilities
images. Final editor/disassembler selection, general documentation placement,
complete Utilities acceptance and frozen-release evidence closure remain open.
