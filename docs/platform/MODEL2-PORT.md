# TRS-80 Model II — BetterCP/M 1.1 engineering candidate

**The first guest qualification gates passed on trs80gp 2.5.8. Release qualification continues.**
The target is a 64 KiB Radio Shack/Tandy TRS-80 Model II in trs80gp with
eight-inch single-sided floppy drives. Model 12, 16, 16B, hard disks, physical
hardware and double-sided media are outside the current claim. No optional
RSX is loaded by the default startup record. Shipping 1.0.x systems are unchanged.

## Build and operate

From the repository root, with Python 3 and the project's z80asm in
`~/bin/z80asm`, run:

```sh
python3 -B tools/build_distribution.py --target trs80m2 --profile model2-fullram \
    --work build/model2-work --output build/model2-candidate
```

Use fresh work and output directories. The output contains two IMDs and a
manifest with SHA-256 hashes and a separate pair of RSX test fixtures; the staged workspace contains the assembly
listings, full checked SYSTEM.SYS and component binaries. The candidate is
deliberately outside the publish/all release target. Never reuse a checked
cpmsim or Model 4 binary that embeds resident addresses.

The pinned development emulator is **trs80gp 2.5.8** for macOS, binary SHA-256
`8f967e640927af1fb9de3a178bbf0bc4d687124780405885a6daa33a3fee1d9f`.
Use its built-in Model II boot ROM, without a replacement ROM or emulator patch.
The executable pin identifies the built-in ROM selection; a separate ROM-dump
hash has not been captured. To try the candidate interactively, mount working copies:

```sh
cp build/model2-candidate/Model-II-System-candidate.imd /tmp/bcpm-m2-a.imd
cp build/model2-candidate/Model-II-Utilities-candidate.imd /tmp/bcpm-m2-b.imd
"$HOME/Applications/trs80gp.app/Contents/MacOS/trs80gp" -m2 -mem 64 \
    -d0 /tmp/bcpm-m2-a.imd -d1 /tmp/bcpm-m2-b.imd
```

Keep the System Disk in drive 0; cold and warm reconstruction read it.
A0 contains the profile-matched PATH.COM. Use `PATH` to inspect the search
order and `A0:PATH /DEFAULT` to recover from any configured search list.
A0 is the expected prompt. DIR, B:STAT and TIME exercise ordinary commands;
TIME should report that no provider is loaded. The Utilities candidate contains
the system-management set, not the complete planned 1.1 release collection.
Do not use these images for irreplaceable data.

## Hardware and resident boundary

| Facility | Implementation and limit |
|---|---|
| Reset/boot | ROM reads FM surface to 0E00h. BOOT is at 1000h; the diagnostic hook at 1400h contains DIAG and a jump at 1404h to 1004h. The loader disables interrupts, unmaps the low ROM at F9h, selects upper RAM at FFh, uses a temporary stack below 2000h, reads 13 MFM sectors from cylinder 1 and enters BIOS BOOT. |
| WBOOT | Reuses the current checked command stages and CPX reconstruction. The BIOS reads package records by absolute record number, with CRC and component identity checks before entry. The Model II CRT displays a failure indicator on checked-loader halts. |
| Keyboard and CRT | Test FFh bit 7 without consuming a key; read FCh and mask the keyboard status bit. Emulated mixed-case input, backspace editing and prompt Ctrl-C passed. Physical modifier timing remains outside the emulated claim. Basic CRT is 80×24, with bounded scrolling, CR/LF/backspace, clear/home and the existing reverse cursor-character service. |
| Video/RAM | FFh=01h normally exposes RAM at F800h–FFFFh. FFh=81h maps the separate video RAM. Code executed during that mapping is below F800h (link assertion). VRAM operations restore RAM before touching the caller's stack and preserve maskable-interrupt state. RTC NMI remains disabled. |
| Floppy | FD1791 registers E4h–E7h, drive/side/density latch EFh, interrupt status E0h, Z80 DMA F8h. Bounded waits, DMA reset and FDC force-interrupt on abort. Physical DMA consumes 128 or 512 bytes as appropriate; BIOS presents 128-byte CP/M records. This is not hardware timing qualification. |
| Logical drives | A–D are initially assigned units 0–3; only 0/1 are needed in the pinned configuration. CONFIG can unbind/rebind B–D with the selected geometry, rejects other geometries and physical reconfiguration before committing a new binding. |
| Other devices | The common BIOS advertises CRT console and CRT list routing; unassigned RDR returns 1Ah, PUN discards output, LISTST reflects selected CRT routing. No serial, physical printer, or timer/clock provider is advertised. An optional clock is not needed to boot. |
| System utilities | CONFIG and SYSGEN translate protected-package records at the disk boundary; DUP walks the short FM surface for copy/check. Track formatting is not implemented; use preformatted BCM2SS images. The BIOS advertises neither a downloadable formatter nor a whole-sector cache to DUP. Guest install, copy and readback passed on the installer build. Configuration write-fault rollback remains open. |

With the overlay switched out, no permanently reserved high-RAM video hole
is required. The protected TPA gateway is **E101h**; the 448 complete
128-byte records occupy 0100h–E0FFh. E100h alone cannot hold another record.
The retained guest run executed the largest COM through three return paths
and rejected the next record, confirming the unloaded limit.

| Address | Selected purpose |
|---|---|
| E101h / E104h | Unloaded TPA boundary / history and persistent data |
| E1C4h / E2BCh | Shared gateway / BDOS |
| F03Ah / F1E3h | Shared extensions / disk control and Model II DMA |
| F5E9h / F8C6h | BIOS / protected file loader |
| F957h / FB57h / FB80h | Four DPH/bindings plus one shared 64-byte ALV and four 32-byte CSVs / resident state / directory buffer |
| FC00h–FFFFh | Temporary module/control workspace; ordinary file-record staging at FC00h and physical-sector deblocking at FE00h. Checked whole-sector overlay loads bypass deblocking. |

The current geometry needs 37 ALV bytes; a live SELDSK guard rejects DSM/CKS
that exceed the declared storage. No Model 4 upper-RAM recovery or change
to shared BDOS, PDS, CCP dispatch order or public BIOS entry numbers is required.

## Selected formats and package layout

BCM2SS is the only candidate format for the system, utilities and interchange.
77 cylinders, one side, FM cylinder 0 (26 × 128, IDs 1–26), MFM cylinders
1–76 (16 × 512, IDs 1–16, 3:1 physical interleave). IMD modes 0 and 3 encode
500 kb/s. Filesystem SPT=64, OFF=4, 2 KiB blocks, DSM=291, 128 directory
entries. There are 584 KiB of allocation space, including 4 KiB of directory;
580 KiB is initially available to files. Physical sector payload is 625,920 bytes.
Preformatting and host normalization do not add fictional sectors to the FM track.

| Checked package record | Physical location |
|---|---|
| 0, 1–2 | FM IDs 1, 2–3. Startup settings use 1–2. |
| 3 | FM ID 13 (ROM diagnostic vector); survives SYSGEN export/install. |
| 4–7 | FM IDs 5–8 (ROM bootstrap). |
| 8–159 | Consecutive 128-byte records starting on cylinder 1, MFM ID 1. |

The implementation uses the existing FDF v1 reserved-surface descriptor. The
16 × 512 layout cannot read original 8 × 1024 ATON/Lifeboat data by changing
only a DPB. No PT2SS, original P&T, ATON, Lifeboat, or MAX-80 media are
admitted as Model II release formats. No mixed-track FDF/FDB redesign is needed.

## Review of the earlier implementation

Primary case study: [a-griff's 14-commit port](https://github.com/a-griff/BetterCPM/compare/42a085998876dc61944e43e057eb238801623194...e24f4b5859e9d9c5abcb044e1eaafe12d3e72c64)
and [issue 523](https://github.com/CPMArchives/BetterCPM/issues/523). Credit
to a-griff for demonstrating boot, identifying the Model II boot locations,
DMA and device behavior, and the BCM2SS layout. The 49 changed paths group as follows:

| Fork paths | Current disposition |
|---|---|
| 18 files under src/platform/trs80m2 | Boot, disk/controller, keyboard, scrolling, DPB and ROM entry behavior informed the new backend. Permanent VRAM, private F600h extension, IM2/serial rings and clock are not carried into the 56 KiB map. Fork formatter, Perl IMD writer, serial harness and shell launchers are not build dependencies. |
| src/bios/bios.mac, src/bios/config.mac | Preserve the shared public vectors, monitor dispatch and CONFIG control API; select only hardware-specific operations. The current checked raw loader accepts record/count/destination, not the fork's old CHS bootstrap ABI. |
| src/utilities/config.mac, disk/common.inc, disk/sysgen.inc, dup.mac, sysgen.mac, time.mac | Keep shared utilities. Adapt the sparse package map for CONFIG/SYSGEN and DUP's physical walk. Do not import the fork's legacy service calls or TIME date changes. |
| 16 tools (BIOS/system/package/platform/media builders, FDF catalogue, clock builder, layout, TIME and Model II tests) | Current profile staging and checked carriers govern. The new producer builds fresh components in that context. Serial/clock tests apply only if those devices are implemented. |
| README, platform and user guides; three metadata files; STARTUP.SUB | The old help, release status, component identities and startup extensions are not authoritative for 1.1. Current sources and new receipts govern promotion. |

The [Radio Shack Model II Technical Reference Manual](https://www.bitsavers.org/pdf/radioShack/modelII/)
is the hardware reference. The [Pickles & Trout CP/M 2 user manual](https://www.bitsavers.org/pdf/picklesAndTrout/PT_CPM_2_TRS-80_II_12_and_16_Users_Manual_1983.pdf)
describes reset/warm boot, BIOS I/O routing and the serial/printer facilities
(especially §5.16 and parts 13–15). It supports exposing these devices through
standard CP/M entry points. It does not establish a requirement to reproduce
P&T's private functions, memory placement, or driver modules.

## What passes and what remains

[Initial host verification](../engineering/evidence/2026-11-07-model2-candidate/host-checks.json)
and [screen candidate verification and disk hashes](../engineering/evidence/2026-11-07-model2-candidate/screen-04.json).

* **Host verified:** full checked assembly and package CRC, fresh-build
  byte comparison, both physical IMD surfaces and all 160 protected records,
  the assembled record reader exercised for every package record and split spans
  with the physical transfer stubbed, independent cpmtools extraction and fsck,
  re-writing and reading the final
  allocation block, disk and directory overflow rejection. The common
  assembled CCP regressions exercise POKE, original tail spelling and dispatch.
* **Guest verified on the retained candidate:** cold boot to A0, all three
  full-size COM returns (RET, JP 0, BDOS Function 0), recovery after the
  next-record rejection, CPX reconstruction, the unloaded TIME response, and
  the HELLO RSX service lifecycle. The guest reported TOP=E101h unloaded
  and D801h with HELLO. ADM3A, VT52 and ANSI each positioned a distinct marker
  at row 7, column 10, and the final unload restored E101h. The 21 captured
  screens and [guest receipt](../engineering/evidence/2026-11-07-model2-guest/result.json)
  belong to the exact image hashes recorded there. Two manager snapshots fell
  before the prompt. Their subsequent service probes prove completion. The
  terminal tests left prior text on screen, so the audit checks newly written
  rows for the final unload and TPA result.
* **Guest installation verified:** SYSGEN installed the package on media with erased
  system tracks. The resulting System Disk matched the source byte for byte. Booting
  this disk alone reached A0, showed RCP.CPX and 56K, and CONFIG /SHOW returned to
  the prompt with the four expected saved bindings.
  [Installation and cold-boot receipt](../engineering/evidence/2026-11-07-model2-install/result.json).
* **Disk qualification passed on installer build `060b323f`:** DUP copied the
  installed disk. The duplicate matched every decoded source sector, cold-booted,
  and reported 00000 unreadable sectors. CONFIG displayed 149 for both the live
  and saved IOBYTE. [Resumed disk qualification](../engineering/evidence/2026-11-07-model2-install/resumed.json).
  The [numeric PATH guest run](../engineering/Numeric-PATH-1.1.md) used System Disk
  SHA-256 `d8e20a91e8277090ffbb095fad96b9d2c653af960791d9caa69f154e75a7110d`.
  The prepared compatibility batch uses this same disk.
* **Current guest conformance:** All 11 selected CP/M suite groups reached their expected
  totals on the PATH-integrated disk (269 passes, zero fails or errors). All eight
  supplemental cases passed. The final-block write changed precisely the last 128
  bytes, physical write protection preserved the disk, and both read-only file
  errors returned to B0 with TOP=E101h. On the full directory, sequential and
  random writes returned 01h and 05h. The edited command tail preserved case
  after Ctrl-C. CONFIG rejected DSM=292 without changing the live binding and
  ran the saved startup command on an independent cold boot.
  [Reviewed results](../engineering/evidence/2026-11-07-model2-conformance/review.json)
  and [59 CRT captures](../engineering/evidence/2026-11-07-model2-conformance/guest-screens.zip).
* **Release-media qualification passed on the PATH-integrated candidate.** Utilities,
  submitted input, lifecycle and installation passed on the same System Disk.
  After CONFIG displayed the four saved bindings, CPX LIST ran from the returned
  prompt and reported RCP.CPX and 56K. The installed disk and its duplicate each
  matched all 625,920 decoded bytes of the source. The duplicate booted alone and
  DUP reported zero unreadable sectors. CONFIG showed 149 for both live and saved
  IOBYTE. [Release-media acceptance record](../engineering/evidence/2026-11-07-model2-release/release-install.json).
* **Remaining release work:** Reconcile the outstanding console and other external
  suite cases, then update the maintained support matrix after platform acceptance.
  Serial, physical printer/clock, formatting and double-sided media are outside
  this profile. Physical hardware is optional. The candidate
  [operator guide](MODEL2-INSTALLATION.md) covers startup, monitors, copying and installation.

### CP/M 2.2 and Model II qualification

The 19-case batch runs one independent guest per case against a fresh copy of
the packaged System Disk. It retains the actual emulator arguments, CRT captures,
disposable media and results even when a later case fails. For preparation,
supply a checkout of the [CP/M 2.2 Compatibility Suite](https://github.com/CPMArchives/cpm-2.2-compatibility-suite)
containing commit `a9a878fcd2e36698c7e856654a85847a004fdd20`. The runner
reads that commit's program blobs and verifies their published checksums.

```sh
./Run-Model-II-Conformance.command --prepare --media build/model2-candidate \
    --suite /path/to/cpm-2.2-compatibility-suite --cpmtools /path/to/cpmtools-posix
./Run-Model-II-Conformance.command
```

Preparation checks the physical image hashes and every fixture filesystem.
The desktop run checks the hashes again. Its results are written under
`build/model2-conformance-guest/run-NAME`. To continue an interrupted batch,
supply `--resume build/model2-conformance-guest/run-NAME`. Completed cases are
checked against their retained captures and disks before they are reused.

| Cases | Evidence collected |
| --- | --- |
| CPUTEST, ECOTEST, DISKTEST, CCPTEST, ENTRYTST, BIOSTEST, ERRTEST, DIRTEST, BDOSTEST, FILETEST, RANDTEST | Selected returning groups used for TRS-80 native conformance. The 11 expected pass counts sum to 269. Observations, unrun cards and manual cases do not contribute to this number. |
| Final block and physical write protection | BDOS random I/O to block 291, followed by host comparison of every other byte. Separate standard BIOS write against the emulator's protected drive with a fresh read and a whole-disk comparison. |
| Full directory and two read-only file cases | Functions 21 and 34 on a full directory with free allocation blocks. Suite cases 0368 and 0369 must report file protection, warm boot and preserve the protected disk. |
| Console editing | Mixed-case command tail after backspace. Ctrl-C abandons the preceding line, and the next command must execute. The emulator injection checks the console path. Physical key rollover is outside this scope. |
| CONFIG rejection and persistence | Reject an incompatible DSM, read back the live binding, save a startup command, compare the changed disk records, and observe that command on a separate cold boot. |

Serial ports, a physical printer, a clock provider, double-sided operation and
formatting have no advertised implementation in this profile. Seven controlled CONSTEST output cases (0052–0058) ran with the actual Model II
resident in the Z80 CPU harness. The harness offered confirmation only after
the emitted byte stream matched the independent expected result. The
[transcripts](../engineering/evidence/2026-11-07-model2-release/constest.json)
document this scope. A separate [IOBYTE test](../engineering/evidence/2026-11-07-model2-release/character-routes.json)
exercised all 256 route values, non-consuming status, masked keyboard input,
CRT output/list selection, reader EOF and punch discard. The keyboard ports
and captured output endpoint were controlled. Additional interactive CONSTEST
input cases and physical modifier timing have separate evidentiary requirements. The
assembled Model II CONFIG.COM recovered the original startup record when
either write failed in the injected-I/O test and reported a failed rollback.
Guest controller fault injection and the remaining suite-card accounting are open. The [host preflight](../engineering/evidence/2026-11-07-model2-conformance/preflight.json)
records candidate and fixture verification.

The desktop invocation `run-rnlwah1u` recorded INCOMPLETE after its host audit
required all of FILETEST's C disk to stay identical. FILETEST actually creates
and erases C:BTTEMP.DAT. The review verified one deleted scratch entry, its
128-byte E7h record and every other original C-disk byte. It checked all 19
cases against the existing evidence without executing them again. The
[original receipt](../engineering/evidence/2026-11-07-model2-conformance/result.json)
and the reviewed result are retained separately. To recheck a finished run on
the host, use `./Run-Model-II-Conformance.command --audit build/model2-conformance-guest/run-NAME`.

### Full Utilities media

From the same source checkout, build the ordinary primary and NOAH companion
inventories for the matching System Disk. The packaging command rebuilds the
common transients and constructs the private BATCHIO carrier in the
`model2-fullram` profile. Both IMDs, their inventory reports, redistribution
notices and corresponding sources are included in `BetterCPM-Utilities-package.zip`.

```sh
python3 -B tools/build_utilities_disk.py --model2-system build/model2-candidate \
    --output build/model2-native-utilities
./Run-Model-II-Release-Checks.command --system build/model2-candidate \
    --utilities build/model2-native-utilities
```

Both volumes use native BCM2SS geometry. The packager verifies the logical
membership, allocation and every file's record data after decoding the physical
IMD. It also binds the release reports to the exact System Disk hash and checks
its profile against the private provider. The primary contains 27 files,
including SUBMIT for this System configuration. The companion contains 10.
The operator [mounting instructions](MODEL2-INSTALLATION.md#mount-the-full-utilities-set)
give the normal A/B/C assignments.

The desktop batch uses copies of all three disks and a separate D work disk.
It exercises compression/decompression, binary comparison, NOAH archive
listing, submitted Function 10 input, BATCHIO removal and STAT memory
reporting. Separate phases run the lifecycle and installer checks on the same
System Disk. Each phase leaves an independent receipt. The [host record](../engineering/evidence/2026-11-07-model2-release/host.json)
identifies two byte-identical builds and independent readback of all 37 files.
On `run-zyrow7xy`, the paired Utilities, submitted input, and all 21 lifecycle
captures passed. SYSGEN also installed and read back the System Disk correctly.
The original CONFIG capture contained the four expected saved bindings but
preceded the return prompt. The resumed run `run-6o2wq_ty` reused the verified
installation, demonstrated return by invoking CPX again, and passed the remaining
disk checks. Its [receipt](../engineering/evidence/2026-11-07-model2-release/release-install.json)
and [captures](../engineering/evidence/2026-11-07-model2-release/release-install-screens.zip)
retain the evidence from those phases. Use `--resume-install build/model2-release-guest/run-NAME` to reuse a
verified install from an incomplete paired run.
[Paired-media receipt](../engineering/evidence/2026-11-07-model2-release/media-guest.json).

### Disk installation qualification

Run `./Run-Model-II-Disk-Qualification.command` from a normal macOS session.
By default it reads the installer candidate under `build/model2-install-candidate`.
Build that candidate from the current branch using the distribution command
above with fresh `--work` and `--output build/model2-install-candidate` paths.
The update changes one byte in SYSGEN.COM to accept the eight-inch Model II
boot drive. Its protected system records match the first guest-tested image.

The batch uses disposable media. It erases the target's reserved surfaces
before SYSGEN and compares all installed sectors and existing filesystem
bytes to the source. It cold-boots the installed disk, runs CPX LIST and
CONFIG /SHOW, copies the full disk with DUP, then boots and checks the copy.
Each phase writes screen captures and a result under `build/model2-install-guest`.
The saved IOBYTE is read at CONFIG menu B, where the value stays visible. To
continue after an interrupted batch, use `--resume build/model2-install-guest/run-NAME`.
The runner verifies prior evidence and disk contents, then uses fresh private
copies to run outstanding phases.

### Model II screen backend

The candidate System Disk carries M2SCRN.RSX and the shared ADM3A, VT52 and
ANSI personalities. Load the backend first. For example:

```text
A0>RSX LOAD M2SCRN
A0>RSX LOAD VT52
A0>RSX LIST
A0>RSX UNLOAD VT52
A0>RSX UNLOAD M2SCRN
```

M2SCRN implements SCRN 1.1. Its capability word is exactly 0004h, selected
by the Model II profile. R3CARR checks the 16-byte private build identity and
R3META requires a private binding for the hardware-specific cursor addresses.
Portable MCON 1.1/1.2 personalities keep their existing capability encoding.
Model II has no assigned legacy MCON 1.0 provider.

The Model II and Model 4 share 80×24 cell, cursor, scrolling and rendition
code. On Model II each direct VRAM operation maps port FFh, completes the cell
or block transfer and restores upper RAM and interrupt state. The rendition
pointer supplied by a caller can therefore refer to normal RAM at F800h or
above. BEL has no audio output in this candidate.

The host Z80 test measured the limits below through BDOS Function 177 using the
assembled Model II resident code and a fixture filesystem. The first optional
module incurs 1,280 bytes of shared manager overhead. M2SCRN itself allocates
1,536 bytes. Unloading the last module restored E101h.

| Loaded profile | TPA top | Record-aligned TPA |
| --- | --- | ---: |
| Unloaded | E101h | 57,344 bytes |
| M2SCRN | D601h | 54,528 bytes |
| M2SCRN + ADM3A | D301h | 53,760 bytes |
| M2SCRN + VT52 | D201h | 53,504 bytes |
| M2SCRN + ANSI | CF01h | 52,736 bytes |

The host CPU test runs the assembled validation logic for both platform
identifiers and the three compiled personalities against the Model II
renderer. The guest batch also loads each personality, verifies an addressed
marker on the emulator screen and checks TPA after unload.

**Portability findings so far.** The BIOS vectors, checked command loader,
CPX/RSX reconstruction, FDF descriptor, filesystem writer, and host media
tooling proved reusable. The concrete costs were deblocking around a live
loader, scarce resident disk space, the physical/package distinction in three
utilities, the two-target screen predicate and the cpmsim-specific paths in the
checked utility builder. The shared CCP also exceeded its existing checked slot
by 14 bytes on an unchanged cpmsim baseline. POKE and original command-tail
storage have disjoint lifetimes: sharing the 127 bytes fixed the overflow for
both targets without changing the media contract. The bad-token guard prevents
the POKE parser retrying an unconsumed operand. A platform-independent HAL
redesign is not justified by these findings.


Host reproduction (run in the source checkout after building above):

```sh
out=build/model2-work/profiles/model2-fullram/trs80m2/build/trs80m2
python3 -B tools/test_model2_record_io.py "$out"
staged="$PWD/build/model2-work/profiles/model2-fullram/trs80m2"
python3 -B tools/test_model2_screen.py "$staged"
BETTERCPM_BUILD_CONTEXT="$staged/build/profile/context.json" python3 -B "$staged/tools/test_model2_screen_lifecycle.py"
python3 -B tools/test_model2_release_media.py "$out" --cpmtools /path/to/cpmtools-posix
python3 -B tools/test_build_profiles.py
```

The screen test also needs a normal Model 4 host build (`python3 -B tools/build_complete_system.py`)
and a z80pack checkout for its CPU core (`--z80pack`).

Use a cpmtools build with the POSIX raw-file backend. The macOS Homebrew
libdsk build read the small files here but returned “Bad parameter” on the
last-block fixture. The POSIX backend read and rewrote that same final block.
This is a host-tool distinction; neither result measures a guest DMA transfer.
