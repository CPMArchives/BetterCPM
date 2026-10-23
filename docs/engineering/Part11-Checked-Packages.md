# Engineering assessment Part 11: integrated checked builds and packages

Date: 23 October 2026. Status: bounded assessment complete; awaiting review.
Part 10 was approved and Part 11 authorized. Accepted core 1.0 remains
`3b2d2d7f4fe0472438465165f11fb550d79c8662`.

## 1. Decision

**The streaming loader now builds as part of a coherent checked cpmsim
profile, with matching command carriers, runtime helpers and an installer
that rejects incompatible input before destination writes.** The qualified
full-RAM image retains **56 KiB unloaded / 53 KiB with ANSISCRN + ADM3A**.
The checked legacy control retains **53 KiB unloaded / 50 KiB with that pair**.

Both profiles pass package installation, disk-source installation and exact
package export. Installed targets cold-boot, and installation leaves their
existing filesystem bytes unchanged. Damaged, old or foreign packages and
missing/foreign critical destination files are refused without changing the
destination in the tested campaigns.

This closes the gap between Parts 9–10's patched proof images and freshly
built, internally consistent cpmsim assessment media. It does not complete
release adoption or native/ROM qualification. The selected build mode remains
an isolated assessment path; the accepted core 1.0 and ordinary release
builders are not silently replaced.

## 2. Fresh build integration

`assessment_checked_profiles.py --carrier-bindings --streaming-commands`
stages a new source tree, applies the checked profile and runs the builders
from source. There is no post-build transplant of Part 8 resident bytes.
Normal CCP and CPX builders emit their bound carriers; the image builder
assembles the streaming stage, embeds its expected CRC in the bootstrap,
and embeds the bootstrap CRC in the newly assembled resident gate.

The same build supplies the checked R3PACK runtime, migrated RSXs, generated
CONFIG compatibility records, profile-specific SYSGEN and manifest-selected
filesystem. Package metadata is generated from the complete system payload,
then the final SYSGEN is rebuilt against that metadata. An early common build
uses a deliberately refusing placeholder until the complete target contract
exists; it is not the distributed installer.

The source is isolated on `assessment/part11-checked-packages`, based on Part
10 commit `950357a1adfb90c8960f4f541f767e3d9034df03`. Main was observed at
`c61ba341d9a638e134b7ebacd007146b0fc1dd56`, which includes separate compression
documentation work. That newer main-only work was not imported into this
qualification and is not overwritten by this branch.

## 3. Compatibility contract

The old input list covered source plus selected build scripts. Part 11 uses
a conservative complete input closure over `src`, `tools`, `metadata` and
`third_party`, excluding Python caches. It includes **1,033 files**, the selected
layout, profile, policy epochs and assembler hash. This captures metadata and
transitive Python dependencies that a `build_*.py` list could miss. It also
includes test tools conservatively: changing those can invalidate a private
contract even when executable semantics do not change. Documentation is
excluded from this private build-input hash.

The 128-bit compatibility ID is deterministically derived from that contract.
A changed input changes the ID; a repeat build from identical inputs preserves
it. The two layouts have distinct IDs. Source metadata records the Git base;
the actual working-tree input hashes are authoritative for these builds.
The preserved branch supplies those exact source bytes.

| Qualified profile | Compatibility ID | Maximum application | With screen pair |
| --- | --- | ---: | ---: |
| cpmsim-fullram | `2523e49e548cd78a185fe10b13fca51c` | 57,344 bytes | 54,272 bytes |
| cpmsim-legacy-checked | `a002efa41f91fb16b1b589323e55a86f` | 54,272 bytes | 51,200 bytes |

The contract's private, carrier and package epochs are now 2. These policy
epochs are distinct from individual file-format versions: BRSX3 remains the
Part 8 RSX format; BCPX2/BCM2 and their schema-2 CRC trailers remain Part 10's
command formats. The new system package is **BCSY version 2, platform 2
(cpmsim)**. This does not change the accepted core's release designation.

Fresh private IDs appear consistently in the resident, bootstrap, second stage,
CCP, RCP and runtime package. A repeat full-RAM build produces identical bytes
for **35 artifacts**, including the raw System Disk, SYSTEM.SYS, loader
carriers, CCP and all 30 selected filesystem artifacts.

## 4. Package and installer behavior

The existing package admission only recognized the old header, length and
system base. It could not establish that the new stages and resident belonged
together. Part 11 introduces a 128-byte version-2 header over the same 160-record
system payload: **20,608 bytes total**.

The header records the selected profile ID, payload CRC and header CRC.
The installer checks the format/base/identity, exact length and EOF, both
CRCs, and agreement between header binding metadata and the resident's saved
A: binding. It also compares the buffered system image against a build-owned
normalized CRC. Thus recomputing the file CRC after swapping or corrupting a
stage does not make the package acceptable to this installer.

Only established editable regions are normalized for that build-owned check:
the two startup records, four physical-drive definitions, four logical-drive
bindings and the cold IOBYTE operand. The buffered bytes are saved, zeroed for
the check and restored exactly, including after rejection. Code, fixed layout,
private IDs, loader stages and command carrier remain covered. For file input,
the separate payload CRC also covers the actual editable bytes as packaged.

These checks detect accidental corruption and mixed build products. They are
not authentication or a guarantee that arbitrary user-edited geometry is valid.
The existing geometry and destination checks still apply.

Disk-source installation and export use the same normalized contract check.
Export constructs the new header and preserves the raw payload exactly. The
live exported file matches the host-generated package byte for byte.

The changed installer identifies itself as `Assessment P11` plus its profile
ID prefix, rather than reusing the released SYSGEN build identity. Its final
executable is **6,638 bytes**, below its fixed transfer-buffer boundary. The
existing approximately 36 KiB transient workspace requirement remains; this
utility growth consumes no resident OS allocation.

## 5. System tracks and filesystem must agree

SYSGEN preserves files; it does not install a new command/runtime file set.
Therefore a successful track copy alone is insufficient evidence of a coherent
upgrade. Before writing, the checked installer reads **RCP.CPX and R3PACK.RSX
from user 0 on the destination**, requires their complete expected content,
and rejects missing, truncated, extra-record or mismatched files. The caller's
user area is restored on both success and failure.

The qualified workflow prepares the matching destination filesystem before
installing system tracks. Live tests use populated destinations with the two
matching files and a sentinel file, then verify filesystem byte preservation
and cold boot. Separate campaigns supply a missing RCP, foreign RCP or foreign
R3PACK and verify the entire destination remains unchanged.

This is not a transaction that simultaneously upgrades every file and the
system area. Optional private RSXs are still subject to their load-time
binding checks; the installer does not replace or certify all optional files
or a user-written startup script. An installation/recovery procedure must
coordinate those files before release adoption.

Neither HELLO.CPX nor HELLO.RSX is a distribution component. The clean System
Disks contain **30 manifest-selected files**, with HELLO and STATEFUL excluded.
Qualification injects fixtures only into disposable test copies. Part 10's
896-byte HELLO.CPX result is retained as a small-carrier test observation,
not as overhead attributed to the shipped configuration.

## 6. Memory, processing and qualification

No additional resident allocation is introduced. The streaming stage remains
**1,301 bytes**, with its **5,504-byte temporary envelope**. The full-RAM stage
executable is byte-identical to approved Part 10; only its surrounding private
contracts and generated carriers are newly bound. The earlier processing
overhead remains. No speed improvement or physical Z80 timing result is claimed.

The final outputs, after implementation fixes, receive these checks:

- Both fresh profiles execute patterned maximum-size applications, reject a
  one-record oversize application, and return through RET, JP 0, BDOS Function
  0 and BIOS WBOOT. Their screen-pair and unloaded TPA measurements match the
  table above.
- Both profiles run the full command-reconstruction campaign: five optional
  CPX failure/recovery cases, STATEFUL preservation, screen load/unload, and
  fatal stage/ID/mandatory-CCP corruption. The original generated system tracks
  are used directly, without prototype patching.
- The full-RAM assembled streaming loader repeats Part 10's admission tests:
  126 failing record positions, 32 failed reads that modify their buffer,
  invalid bindings/checksums/relocations, exact placement boundaries and 81
  synthetic header/payload/trailer combinations. Bootstrap admission repeats
  its 25-case summary campaign.
- Host and assembled package readers agree on **15 package cases**: matching,
  foreign profile/ID, old format, base, length/EOF, header and payload corruption,
  binding mismatch and resealed altered bootstrap/stage/CCP/private ID.
- Four raw-buffer fixtures check matching, foreign, corrupt and permitted
  editable-field input, including exact restoration of the buffered payload.
  Three destination-file fixtures check matching, missing and foreign content,
  enforce user 0 and restore a caller initially in user 7.
- Both profiles pass **15 live installation/export/refusal cases each**:
  package install, disk install, export, seven invalid file packages, three
  critical destination-file failures, foreign disk-source input and decline.
  Successful installations preserve filesystem bytes and cold-boot. Refusals
  preserve the complete destination byte for byte.
- The source/identity audit checks profile separation, consistent private
  binding, distribution fixture exclusion and 35 deterministic repeat artifacts.

The earlier intermediate build directories are not the qualified outputs.
The report preserves `tested-fullram`, `tested-legacy`, their final campaign
results and the repeat-build audit. [Part11-Reproduction.md](Part11-Reproduction.md)
identifies the commands and evidence.

## 7. Adoption limits and next part

The result supports adopting this build/package design for the checked cpmsim
path after the remaining qualification. It does not justify calling the
whole migration release-ready.

Still outstanding are actual Model 4 and ROM integration, native build parity,
private-utility compatibility beyond the installer/CONFIG paths exercised here,
complete stack ownership/high-water analysis, hardware timing, broader
geometry/user-startup cases and interruption during physical installation.
The classic write/readback sequence remains, with boot record zero written
last. It is not an atomic upgrade: a failed write can leave an unbootable target.
No power-loss or write-abort recovery claim is made by these tests.

Legacy SYSBUILD/package-generation paths are not migrated by this selected
cpmsim mode. The v2 package is deliberately rejected by the old file-package
reader. These gates do not control what an old raw-sector copier might write.
The latest main-only utility work also needs reconciliation before release.

**Proposed Part 12:** audit remaining private utility dependencies and stack
ownership in the checked cpmsim path; identify and resolve concrete blockers
before native/ROM adoption. Keep physical installation-interruption testing
and the separate Model 4 window-banking investigation explicitly scheduled.
Pause after that bounded qualification assessment.

Part 11 is complete and awaits review. No Part 12 work has begun.
